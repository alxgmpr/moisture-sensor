/*
 * BTHome soil sensor — nRF54L15 DK, simulated data.
 *
 * One cold boot is one cycle: wake, generate, advertise, System OFF. Waking
 * from System OFF resets the device, so there is no loop and no state to
 * carry between cycles.
 */

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/sys/printk.h>

#include <string.h>

#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/timer/nrf_grtc_timer.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/sys/reboot.h>

#ifdef CONFIG_SENSOR_OTA
#include <zephyr/bluetooth/conn.h>
#include <zephyr/dfu/mcuboot.h>
#include <zephyr/mgmt/mcumgr/transport/smp_bt.h>
#endif

#include "bthome.h"

/*
 * The BLE identity must be identical on every cold boot. Zephyr generates one
 * when none is configured — the LBS sample logs "No ID address" and does
 * exactly that — and a fresh address each hour would make Home Assistant
 * register a new device every hour.
 *
 * Deriving it from the chip's own ID keeps it stable with no settings
 * subsystem, no NVS, and no flash wear.
 */
static int set_stable_identity(void)
{
	bt_addr_le_t addr = { .type = BT_ADDR_LE_RANDOM };
	uint8_t hwid[16];
	ssize_t n;
	int err;

	n = hwinfo_get_device_id(hwid, sizeof(hwid));
	if (n < 6) {
		printk("hwinfo_get_device_id returned %d\n", (int)n);
		return -1;
	}

	/* Fold every byte of the device id into six so none of it is ignored. */
	memset(addr.a.val, 0, sizeof(addr.a.val));
	for (ssize_t i = 0; i < n; i++) {
		addr.a.val[i % 6] ^= hwid[i];
	}

	/* A static random address must have its two most significant bits set. */
	addr.a.val[5] |= 0xC0;

	err = bt_id_create(&addr, NULL);
	if (err < 0) {
		printk("bt_id_create failed (%d)\n", err);
		return err;
	}

	printk("identity: %02X:%02X:%02X:%02X:%02X:%02X\n",
	       addr.a.val[5], addr.a.val[4], addr.a.val[3],
	       addr.a.val[2], addr.a.val[1], addr.a.val[0]);

	return 0;
}

/* One wet-to-dry sweep, then it repeats, so the curve is visible in a session. */
#define SIM_DRY_PERIOD_MS   (6ULL * 60 * 60 * 1000)
#define SIM_MOIST_WET_CPCT  8000U   /* 80.00 % */
#define SIM_MOIST_DRY_CPCT  2500U   /* 25.00 % */

/* SENSE2 reads four points below SENSE1 so that a positional mix-up between
 * the two entities is obvious in Home Assistant rather than invisible. */
#define SIM_SENSE2_OFFSET   400U

/*
 * GRTC SYSCOUNTER survives System OFF — the datasheet is explicit that
 * SYSCOUNTERL/H are restored on wakeup even though the rest of GRTC resets.
 * That makes it the one clock that measures total elapsed time across cold
 * boots, which is why the simulation can be a pure function of it and needs no
 * stored state.
 *
 * The counter runs at sys_clock_hw_cycles_per_sec(), not a fixed 1 MHz, so
 * convert rather than assume.
 */
static uint64_t elapsed_ms(void)
{
	uint64_t ticks = z_nrf_grtc_timer_read();

	return (ticks * 1000ULL) / (uint64_t)sys_clock_hw_cycles_per_sec();
}

/* Triangle wave in [-amplitude, +amplitude], integer only. */
static int32_t triangle(uint64_t t_ms, uint32_t period_ms, int32_t amplitude)
{
	uint32_t phase = (uint32_t)(t_ms % period_ms);
	uint32_t half = period_ms / 2U;
	uint32_t up = (phase < half) ? phase : (period_ms - phase);

	return ((int32_t)up * 2 * amplitude) / (int32_t)half - amplitude;
}

static struct bthome_values sim_values(uint64_t t_ms)
{
	uint64_t phase = t_ms % SIM_DRY_PERIOD_MS;
	uint32_t span = SIM_MOIST_WET_CPCT - SIM_MOIST_DRY_CPCT;
	uint16_t m1 = (uint16_t)(SIM_MOIST_WET_CPCT -
				 (uint64_t)span * phase / SIM_DRY_PERIOD_MS);
	uint64_t drained = t_ms / (30ULL * 60 * 1000);   /* 1 % per 30 min */

	struct bthome_values v = {
		.battery_pct = (drained >= 99) ? 1U : (uint8_t)(100U - drained),
		.temperature_cc =
			(int16_t)(2100 + triangle(t_ms, 20U * 60 * 1000, 150)),
		.humidity_cpct =
			(uint16_t)(4500 + triangle(t_ms, 37U * 60 * 1000, 800)),
		.moisture1_cpct = m1,
		.moisture2_cpct = (m1 > SIM_SENSE2_OFFSET)
					  ? (uint16_t)(m1 - SIM_SENSE2_OFFSET)
					  : 0U,
	};

	return v;
}

/* The advertisement is exactly 31 of 31 bytes with a 7-character name; a
 * longer CONFIG_SENSOR_DEVICE_NAME makes bt_le_adv_start() fail at runtime,
 * and the device silently stops advertising every cycle while the console
 * still looks healthy. */
BUILD_ASSERT(sizeof(CONFIG_SENSOR_DEVICE_NAME) - 1 <= 7,
	     "BLE name must fit the 9 spare AD bytes");

static void advertise(const uint8_t *svc_data)
{
	const struct bt_data ad[] = {
		BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
		BT_DATA(BT_DATA_SVC_DATA16, svc_data, BTHOME_ADV_DATA_LEN),
		BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_SENSOR_DEVICE_NAME,
			sizeof(CONFIG_SENSOR_DEVICE_NAME) - 1),
	};
	int err;

	if (set_stable_identity() < 0) {
		printk("continuing with the stack's own identity\n");
	}

	err = bt_enable(NULL);
	if (err) {
		printk("bt_enable failed (%d)\n", err);
		return;
	}

	/*
	 * Ask the stack what identity it actually holds, rather than trusting
	 * the address we handed bt_id_create().
	 *
	 * The earlier version printed our own computed buffer, which is a
	 * deterministic function of the chip id — so it printed the same six
	 * bytes whether bt_id_create() had succeeded, failed, or been ignored.
	 * That made "stable across resets" a tautology and hid a real bug for
	 * the whole build. This line is the only one that can contradict us.
	 */
	{
		bt_addr_le_t ids[CONFIG_BT_ID_MAX];
		size_t count = ARRAY_SIZE(ids);

		bt_id_get(ids, &count);
		if (count > 0) {
			printk("stack identity: %02X:%02X:%02X:%02X:%02X:%02X (type %u, %u id%s)\n",
			       ids[0].a.val[5], ids[0].a.val[4], ids[0].a.val[3],
			       ids[0].a.val[2], ids[0].a.val[1], ids[0].a.val[0],
			       ids[0].type, (unsigned)count, count == 1 ? "" : "s");
		} else {
			printk("stack identity: NONE — bt_id_create() did not take\n");
		}
	}

	/*
	 * Non-connectable, non-scannable: there is no GATT service worth
	 * connecting to, and staying connectable would hold the radio up
	 * waiting for connections we do not want.
	 *
	 * BT_LE_ADV_OPT_USE_IDENTITY is load bearing and not a privacy
	 * preference. Without it Zephyr advertises from a Non-Resolvable
	 * Private Address, freshly generated by bt_rand() every time the
	 * advertising parameters are set (subsys/bluetooth/host/id.c,
	 * bt_id_set_adv_private_addr). Since every cycle is a cold boot, that
	 * is a new MAC every wake, and Home Assistant registers a new device
	 * each time — 24 dead sensors a day on the hourly build.
	 *
	 * Setting the identity with bt_id_create() is not enough on its own:
	 * it fixes what bt_id_get() reports and what the console prints, but
	 * the address actually transmitted still comes from the NRPA path
	 * until this flag selects the identity address instead. Verify this
	 * with a scanner or with Home Assistant, never from the console.
	 */
	err = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_USE_IDENTITY,
					      BT_GAP_ADV_FAST_INT_MIN_2,
					      BT_GAP_ADV_FAST_INT_MAX_2, NULL),
			      ad, ARRAY_SIZE(ad), NULL, 0);
	if (err) {
		printk("adv_start failed (%d)\n", err);
		return;
	}

	printk("advertising %d ms\n", CONFIG_SENSOR_ADV_WINDOW_MS);
	k_msleep(CONFIG_SENSOR_ADV_WINDOW_MS);

	bt_le_adv_stop();
}

static const struct gpio_dt_spec escape_btn = GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);

#ifdef CONFIG_SENSOR_OTA
static const struct bt_data ota_ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
	BT_DATA_BYTES(BT_DATA_UUID128_ALL, SMP_BT_SVC_UUID_VAL),
};

static const struct bt_data ota_sd[] = {
	BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
		sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static void ota_advertise(void)
{
	int err = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1,
				  ota_ad, ARRAY_SIZE(ota_ad),
				  ota_sd, ARRAY_SIZE(ota_sd));

	if (err) {
		printk("OTA advertising failed (%d)\n", err);
		return;
	}

	printk("OTA ready: connect over BLE using MCUmgr/SMP\n");
}

static void ota_disconnected(struct bt_conn *conn, uint8_t reason)
{
	ARG_UNUSED(conn);
	printk("OTA disconnected (reason 0x%02x)\n", reason);
	ota_advertise();
}

BT_CONN_CB_DEFINE(ota_conn_callbacks) = {
	.disconnected = ota_disconnected,
};

static void ota_run(void)
{
	int err;

	if (set_stable_identity() < 0) {
		printk("continuing with the stack's own identity\n");
	}

	err = bt_enable(NULL);
	if (err) {
		printk("bt_enable failed (%d)\n", err);
		return;
	}

	/* CONFIG_MCUMGR_TRANSPORT_BT registers the SMP service at init. */
#ifdef CONFIG_SENSOR_OTA_SKIP_CONFIRM
	printk("OTA rollback test: leaving image unconfirmed\n");
#else
	err = boot_write_img_confirmed();
	if (err) {
		printk("MCUboot image confirmation failed (%d)\n", err);
		return;
	}
#endif

	ota_advertise();
	printk("staying awake for OTA maintenance\n");
	k_sleep(K_FOREVER);
}
#endif

/*
 * Held at boot, this keeps the device awake and therefore programmable. A
 * device in System OFF does not answer the debugger, so without an escape a
 * one-hour cycle leaves a very small window to flash in.
 *
 * DK only. Our board needs no equivalent: with a debugger attached the device
 * is in Debug Interface mode and System OFF is emulated, so it stays reachable.
 */
static bool escape_held(void)
{
	if (!gpio_is_ready_dt(&escape_btn)) {
		return false;
	}

	if (gpio_pin_configure_dt(&escape_btn, GPIO_INPUT) < 0) {
		return false;
	}

	/* The devicetree spec carries GPIO_ACTIVE_LOW, so 1 means pressed. */
	return gpio_pin_get_dt(&escape_btn) == 1;
}

static void sleep_until_next_cycle(void)
{
	int err;

	printk("sleeping %d s\n", CONFIG_SENSOR_CYCLE_SECONDS);
	/*
	 * The console drain above must happen before we arm the wake source:
	 * z_nrf_grtc_wakeup_prepare() clears every other GRTC channel and
	 * expects to be followed immediately by sys_poweroff(). Kernel timer
	 * activity between the two (even a k_msleep()) runs through the
	 * channels it just cleared and undoes the arm.
	 */
	k_msleep(50);   /* sys_poweroff() does not wait for the console */

	err = z_nrf_grtc_wakeup_prepare((uint64_t)CONFIG_SENSOR_CYCLE_SECONDS *
					USEC_PER_SEC);

	if (err < 0) {
		/*
		 * This is the one failure that must not fall through to sleep.
		 * System OFF with no wake source never returns, so a device
		 * that sleeps here is gone until someone presses reset.
		 */
		printk("GRTC wake prepare failed (%d) — resetting instead\n", err);
		sys_reboot(SYS_REBOOT_COLD);
	}

	sys_poweroff();
}

/*
 * Covers a hang while the radio is up. It does not fire during the sleep —
 * not because of WDT_OPT_PAUSE_HALTED_BY_DBG below (that only pauses the
 * counter under a debugger), but because the watchdog peripheral loses power
 * in System OFF along with the rest of the chip, and waking from System OFF
 * is a full reset. There is nothing left counting down to fire.
 *
 * The window is the advertising window plus a fixed margin, not a multiple of
 * the window: the cycle's ~2.1 s cost (bt_enable, encode, console) is mostly
 * fixed overhead, not proportional to CONFIG_SENSOR_ADV_WINDOW_MS. A multiple
 * shrinks along with the window, so a short window (e.g. 400 ms) would demand
 * the fixed overhead complete inside a budget it cannot meet, and the device
 * would watchdog-reset forever without ever reaching sys_poweroff().
 *
 * There is no wdt_feed() anywhere in this file, deliberately: the watchdog is
 * armed once per cold boot and never fed again, so the whole cycle — escape
 * check, encode, advertise — has to finish inside window.max on its own.
 * Measured overhead is about 2.1 s against the 8 s window this config
 * produces, which is the margin that invariant relies on.
 */
static void watchdog_start(void)
{
	const struct device *wdt = DEVICE_DT_GET(DT_NODELABEL(wdt31));
	struct wdt_timeout_cfg cfg = {
		.window.min = 0,
		.window.max = CONFIG_SENSOR_ADV_WINDOW_MS + 6000,
		.callback = NULL,
		.flags = WDT_FLAG_RESET_SOC,
	};
	int err;

	if (!device_is_ready(wdt)) {
		printk("watchdog not ready — continuing without it\n");
		return;
	}

	if (wdt_install_timeout(wdt, &cfg) < 0) {
		printk("wdt_install_timeout failed — continuing without it\n");
		return;
	}

	err = wdt_setup(wdt, WDT_OPT_PAUSE_HALTED_BY_DBG);
	if (err < 0) {
		printk("wdt_setup failed (%d) — continuing without it\n", err);
	}
}

int main(void)
{
	uint64_t now_ms;
	struct bthome_values v;
	uint8_t svc[BTHOME_ADV_DATA_LEN];

	printk("\n=== bthome-sensor ===\n");

#ifdef CONFIG_SENSOR_OTA
	ota_run();
	return 0;
#endif

	if (escape_held()) {
		printk("Button 0 held — staying awake so the board can be flashed.\n");
		while (1) {
			k_sleep(K_FOREVER);
		}
	}

	watchdog_start();

	now_ms = elapsed_ms();
	v = sim_values(now_ms);

	printk("elapsed %llu ms\n", now_ms);

	if (bthome_encode(&v, svc, sizeof(svc)) != BTHOME_ADV_DATA_LEN) {
		/* Never advertise a partial packet: a missing field rebinds
		 * SENSE2 to the wrong Home Assistant entity silently. Skipping
		 * the advertisement lets HA mark the entity stale, which is
		 * honest about what happened. */
		printk("encode failed — skipping this advertisement\n");
	} else {
		printk("payload:");
		for (size_t i = 0; i < sizeof(svc); i++) {
			printk(" %02X", svc[i]);
		}
		printk("\n");

		printk("battery %u%%  temp %d.%02d C  hum %u.%02u%%  m1 %u.%02u%%  m2 %u.%02u%%\n",
		       v.battery_pct, v.temperature_cc / 100,
		       (v.temperature_cc % 100 + 100) % 100,
		       v.humidity_cpct / 100, v.humidity_cpct % 100,
		       v.moisture1_cpct / 100, v.moisture1_cpct % 100,
		       v.moisture2_cpct / 100, v.moisture2_cpct % 100);

		advertise(svc);
	}

	sleep_until_next_cycle();

	return 0;   /* unreachable */
}
