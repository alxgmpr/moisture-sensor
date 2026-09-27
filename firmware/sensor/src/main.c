/* Real battery-powered sensor image. One cold boot per cycle. */
#include "sensor.h"
#include "bthome.h"
#include "config_service.h"
#include <string.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/mgmt/mcumgr/transport/smp_bt.h>
#include <zephyr/dfu/mcuboot.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/timer/nrf_grtc_timer.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/kernel.h>
#include <zephyr/pm/device.h>
#include <zephyr/pm/device_runtime.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/sys/reboot.h>

struct sensor_boot_trace {
    uint32_t magic;
    uint32_t boots;
    uint32_t stage;
    int32_t error;
    uint32_t last_failure_stage;
    int32_t last_failure_error;
    struct sensor_fault fault;
    struct sensor_sample sample;
    uint32_t wake_seconds;
};

static struct sensor_boot_trace sensor_trace __attribute__((section(".noinit")));
static struct sensor_fault cycle_fault;
static const struct sensor_bus *trace_bus;
static uint32_t reset_cause;
static uint8_t pmic_reset = 0xff, previous_stage = 0xff;

static void pmic_trace(uint8_t stage)
{
    if (trace_bus)
        (void)sensor_retained_stage(trace_bus, stage);
}

static void trace_boot(void)
{
    /* A new layout/magic must never interpret old or power-on SRAM as errors. */
    if (sensor_trace.magic != 0x53454e54u)
        sensor_trace = (struct sensor_boot_trace){.magic = 0x53454e54u};
    sensor_trace.boots++;
}

static void trace_stage(uint32_t stage, int error)
{
    pmic_trace(stage);
    sensor_trace.stage = stage;
    sensor_trace.error = error;
}

static void trace_failure(uint32_t stage, int error)
{
    trace_stage(stage, error);
    sensor_trace.last_failure_stage = stage;
    sensor_trace.last_failure_error = error;
    sensor_trace.fault = cycle_fault;
    printk("sensor failure stage=%u error=%d addr=0x%02x reg=0x%02x "
           "observed=0x%04x mask=0x%04x expected=0x%04x\n",
           (unsigned)stage, error, cycle_fault.address, cycle_fault.reg,
           cycle_fault.observed, cycle_fault.mask, cycle_fault.expected);
}

static uint16_t diagnostic_error(void)
{
    int64_t error = sensor_trace.last_failure_error;

    if (error < 0)
        error = -error;
    return error > UINT16_MAX ? UINT16_MAX : (uint16_t)error;
}

#if !CONFIG_SENSOR_OTA
static const struct device *sensor_wdt;
#endif

struct sensor_devices {
    const struct device *main;
    const struct device *fdc;
};

/* Runtime PM applies the no-pull, disconnected sleep pinctrl state. */
static int fdc_bus_is_asleep(const struct device *dev) {
    enum pm_device_state state;
    int rc = pm_device_state_get(dev, &state);
    if (rc)
        return rc;
    return pm_device_runtime_is_enabled(dev) && state == PM_DEVICE_STATE_SUSPENDED ? 0 : -EBUSY;
}

static int transfer(void *ctx, uint8_t address, const uint8_t *w, size_t nw, uint8_t *r,
                    size_t nr) {
    const struct sensor_devices *devices = ctx;
    const struct device *dev = address == 0x50 ? devices->fdc : devices->main;
    if (nw && nr)
        return i2c_write_read(dev, address, w, nw, r, nr);
    if (nw)
        return i2c_write(dev, w, nw, address);
    return i2c_read(dev, r, nr, address);
}
static void delay(void *ctx, unsigned ms) {
    (void)ctx;
    k_msleep(ms);
}
static char hex_digit(uint8_t v) {
    return v < 10 ? (char)('0' + v) : (char)('A' + v - 10);
}
static uint8_t battery_percent(uint16_t millivolts) {
    /* Provisional voltage-only estimate for the CR2032 prototype. */
    if (millivolts <= 2200)
        return 0;
    if (millivolts >= 3000)
        return 100;
    return (uint8_t)(((uint32_t)(millivolts - 2200) * 100U) / 800U);
}
#if !CONFIG_SENSOR_OTA
static int arm_watchdog(void) {
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(wdt31));
    struct wdt_timeout_cfg cfg = {.window = {0, 15000}, .flags = WDT_FLAG_RESET_SOC};
    if (!device_is_ready(dev))
        return -ENODEV;
    int rc = wdt_install_timeout(dev, &cfg);
    if (rc < 0)
        return rc;
    rc = wdt_setup(dev, WDT_OPT_PAUSE_HALTED_BY_DBG);
    if (!rc)
        sensor_wdt = dev;
    return rc;
}

static void feed_watchdog(void)
{
    if (sensor_wdt)
        (void)wdt_feed(sensor_wdt, 0);
}
#else
static void feed_watchdog(void) { }
#endif
static int radio_window(const struct sensor_bus *bus, const struct sensor_sample *sample) {
    struct sensor_config config;
    sensor_settings_get(&config);
    trace_stage(70, 0);
    int rc = sensor_radio_start(bus);
    if (rc) {
        trace_failure(70, rc);
        return rc;
    }
    uint8_t id[16];
    bt_addr_le_t addr = {.type = BT_ADDR_LE_RANDOM};
    ssize_t n = hwinfo_get_device_id(id, sizeof(id));
    if (n < 6) {
        trace_failure(71, -EIO);
        return -EIO;
    }
    for (ssize_t i = 0; i < n; i++)
        addr.a.val[i % 6] ^= id[i];
    addr.a.val[5] |= 0xc0;
    rc = bt_id_create(&addr, NULL);
    if (rc < 0) {
        trace_failure(72, rc);
        return rc;
    }
    rc = bt_enable(NULL);
    if (rc) {
        trace_failure(73, rc);
        return rc;
    }
    char name[] = {
        'S', 'o', 'i', 'l', '-',
        hex_digit(addr.a.val[1] >> 4), hex_digit(addr.a.val[1] & 0x0f),
        hex_digit(addr.a.val[0] >> 4), hex_digit(addr.a.val[0] & 0x0f), 0,
    };
    const char *device_name = config.name[0] ? config.name : name;
    rc = bt_set_name(device_name);
    if (rc) return rc;
    /* BTHome v2 service data uses UUID FCD2, standard object IDs, and the
     * calibrated moisture values configured below. */
    uint8_t bthome[BOARD_BTHOME_PAYLOAD_LEN];
    struct board_bthome_values values = {
        .temperature_cc = sample->temperature_cc,
        .humidity_cpct = sample->humidity_cpct,
        .battery_pct = battery_percent(sample->battery_mv),
        .battery_mv = sample->battery_mv,
        .moisture1_cpct = sensor_moisture(sample->capacitance_ff[0], config.dry[0], config.wet[0]),
        .moisture2_cpct = sensor_moisture(sample->capacitance_ff[1], config.dry[1], config.wet[1]),
        .omit_moisture = !config.calibrated,
    };
    int payload_len = board_bthome_encode(&values, bthome, sizeof bthome);
    if (payload_len < 0) {
        trace_failure(74, -EINVAL);
        return -EINVAL;
    }
    const struct bt_data ad[] = {
        BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
        BT_DATA(0x16, bthome, payload_len),
    };
    const struct bt_data sd[] = {
        BT_DATA(BT_DATA_NAME_COMPLETE, device_name, strlen(device_name)),
        /* SMP is in scan response; BTHome remains in the primary packet. */
        BT_DATA_BYTES(BT_DATA_UUID128_ALL, SMP_BT_SVC_UUID_VAL),
    };
    rc = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_USE_IDENTITY |
                                         BT_LE_ADV_OPT_SCANNABLE |
                                         BT_LE_ADV_OPT_CONN,
                                         config.adv_ms * 8 / 5, config.adv_ms * 8 / 5,
                                         NULL),
                         ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (rc) {
        trace_failure(75, rc);
        return rc;
    }
    trace_stage(76, sample->battery_mv);
    int64_t deadline = k_uptime_get() + config.window_ms;
    bool had_connection = false;
    while (k_uptime_get() < deadline || sensor_session_connected()) {
        uint16_t radio_battery_mv;
        rc = sensor_battery_read(bus, &radio_battery_mv);
        if (!rc && radio_battery_mv < SENSOR_MIN_BATTERY_MV)
            rc = -ERANGE;
        if (!rc)
            rc = sensor_watchdog_feed(bus);
        if (rc) {
            trace_failure(78, rc);
            sensor_session_disconnect();
            (void)bt_le_adv_stop();
            return rc;
        }
        feed_watchdog();
        sensor_settings_process();
        if (sensor_session_expired()) {
            sensor_session_disconnect();
            break;
        }
        if (sensor_session_connected()) had_connection = true;
        else if (had_connection) break;
        if (sensor_sample_requested()) {
            /* Foreground only; callbacks never touch I2C. Sampling remains
             * bounded by both watchdogs, with the FDC rail off afterwards. */
            struct sensor_sample fresh = {0};
            int measured = sensor_start(bus, &fresh);
            if (!measured) measured = sensor_measure(bus, &fresh);
            const struct sensor_devices *devices = bus->ctx;
            int off = fdc_bus_is_asleep(devices->fdc);
            if (!off && !measured) off = sensor_radio_start(bus);
            sensor_status_sample(&fresh, measured ? measured : off);
            if (off) {
                trace_failure(80, off);
                return off;
            }
            if (measured) {
                trace_failure(61, measured);
                sensor_session_disconnect();
                (void)bt_le_adv_stop();
                return measured;
            }
        }
        int64_t remaining = deadline - k_uptime_get();
        sensor_session_wait(sensor_session_connected() ? 1000 :
                            remaining > 1000 ? 1000 : remaining > 0 ? remaining : 0);
    }
    /* Finish an accepted save even if the client has just disconnected. */
    sensor_settings_process();
    feed_watchdog();
    rc = bt_le_adv_stop();
    if (rc != -EALREADY && rc)
        trace_failure(77, rc);
    else
        trace_stage(77, 0);
    return rc == -EALREADY ? 0 : rc;
}

#if CONFIG_SENSOR_OTA
static const struct bt_data ota_ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, SMP_BT_SVC_UUID_VAL),
};
static const struct bt_data ota_sd[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
            sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};
static void ota_advertise(void) {
    int rc = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1, ota_ad, ARRAY_SIZE(ota_ad),
                             ota_sd, ARRAY_SIZE(ota_sd));
    if (rc)
        printk("OTA advertising failed (%d)\n", rc);
    else
        printk("OTA ready: connect over BLE using MCUmgr/SMP\n");
}
static void ota_disconnected(struct bt_conn *conn, uint8_t reason) {
    ARG_UNUSED(conn);
    printk("OTA disconnected (reason 0x%02x)\n", reason);
    ota_advertise();
}
BT_CONN_CB_DEFINE(sensor_ota_conn_callbacks) = {
    .disconnected = ota_disconnected,
};
static int ota_identity(void) {
    uint8_t id[16];
    bt_addr_le_t addr = {.type = BT_ADDR_LE_RANDOM};
    ssize_t n = hwinfo_get_device_id(id, sizeof(id));
    if (n < 6)
        return -EIO;
    for (ssize_t i = 0; i < n; i++)
        addr.a.val[i % 6] ^= id[i];
    addr.a.val[5] |= 0xc0;
    return bt_id_create(&addr, NULL) < 0 ? -EIO : 0;
}
static int ota_run(const struct sensor_bus *bus) {
    int rc = sensor_ota_start(bus);
    if (rc)
        return rc;
    rc = ota_identity();
    if (rc)
        return rc;
    rc = bt_enable(NULL);
    if (rc)
        return rc;
    rc = boot_write_img_confirmed();
    if (rc)
        return rc;
    ota_advertise();
    printk("OTA maintenance active\n");
    for (;;) {
        sensor_settings_process();
        if (sensor_session_expired()) sensor_session_disconnect();
        sensor_session_wait(1000);
    }
    return 0;
}
#endif
static void power_backoff(const struct sensor_bus *bus, int error)
{
    /* Keep the failing operation in SCRATCHB across Hibernate. Replacing it
     * with the generic backoff stage would hide sensing and radio failures
     * when the PMIC removes power from the MCU's retained RAM. */
    if (sensor_trace.last_failure_stage != sensor_trace.stage ||
        sensor_trace.last_failure_error != error)
        trace_failure(84, error);
    sensor_trace.wake_seconds = CONFIG_SENSOR_UV_RETRY_SECONDS;
    /* Preserve the watchdog origin across the hibernate power cut so the
     * first recovery advertisement/status can distinguish these paths. */
    if (trace_bus && (reset_cause & RESET_WATCHDOG))
        (void)sensor_retained_stage(bus, 0xe1);
    else if (trace_bus && ((pmic_reset >> 1) & 15) == 5)
        (void)sensor_retained_stage(bus, 0xe2);
    int rc = trace_bus ? sensor_hibernate(bus, CONFIG_SENSOR_UV_RETRY_SECONDS) : -ENODEV;
    /* Normally VOUT disappears during the task write. If I2C failed or the
     * rail did not turn off, use the MCU's timed System OFF as a fallback.
     * Retained BLOCKED prevents sensor/radio attempts on a watchdog reset.
     * A PMIC that cannot be reached cannot be guaranteed to stop its timer. */
    k_msleep(20);
    if (trace_bus)
        (void)sensor_stop(bus);
    trace_stage(85, rc);
    int wake = z_nrf_grtc_wakeup_prepare((uint64_t)CONFIG_SENSOR_UV_RETRY_SECONDS *
                                       USEC_PER_SEC);
    if (wake) {
        sensor_trace.stage = 86;
        sensor_trace.error = wake;
    }
    /* Even if timed wake preparation fails, stay off instead of feeding a
     * reset loop. Recovery then requires an external wake or power cycle.
     * No timeout-dependent work is safe after GRTC preparation. */
    sys_poweroff();
}

int main(void) {
    trace_boot();
    trace_stage(1, 0);
    struct sensor_devices devices = {
        .main = DEVICE_DT_GET(DT_NODELABEL(i2c22)),
        .fdc = DEVICE_DT_GET(DT_NODELABEL(i2c20)),
    };
    struct sensor_bus bus = {&devices, transfer, delay, &cycle_fault};
    struct sensor_sample sample = {0};
    int rc = 0;
    if (!device_is_ready(devices.main) || !device_is_ready(devices.fdc))
        rc = -ENODEV;
    if (!rc)
        rc = fdc_bus_is_asleep(devices.fdc);
    if (device_is_ready(devices.main))
        trace_bus = &bus;
    if (rc)
        power_backoff(&bus, rc);

    uint8_t retained = 0;
    rc = sensor_retained_read(&bus, &retained, &previous_stage, &pmic_reset);
    if (!rc)
        rc = sensor_power_probe(&bus, &sample.battery_mv);
    (void)hwinfo_get_reset_cause(&reset_cause);
    (void)hwinfo_clear_reset_cause();
    sensor_status_diagnostics(reset_cause, pmic_reset, previous_stage,
                              sensor_trace.last_failure_stage, diagnostic_error());
    /* An interrupted attempt gets a full quiet interval even after voltage
     * rebounds. Once BLOCKED, use a higher voltage for recovery. SMP's explicit
     * software reboot at a healthy supply must still allow an OTA test boot;
     * normal error paths below never request immediate software reboots. */
    bool planned_reboot = (reset_cause & RESET_SOFTWARE) &&
                          sample.battery_mv >= SENSOR_RECOVER_BATTERY_MV;
    if (rc || (retained == SENSOR_POWER_ATTEMPT && !planned_reboot) ||
        !sensor_power_allowed(sample.battery_mv, retained))
        power_backoff(&bus, rc ? rc : -EAGAIN);
    rc = sensor_retained_state(&bus, SENSOR_POWER_ATTEMPT);
    if (rc)
        power_backoff(&bus, rc);
    uint8_t clear[] = {0xd1, 1};
    (void)transfer(&devices, 0x74, clear, 2, NULL, 0);
#if !CONFIG_SENSOR_OTA
    rc = arm_watchdog();
    if (rc)
        power_backoff(&bus, rc);
#endif
    int settings_rc = sensor_settings_init();
    if (settings_rc)
        printk("configuration load failed (%d); using build defaults\n", settings_rc);
#if CONFIG_SENSOR_OTA
    rc = ota_run(&bus);
    power_backoff(&bus, rc);
    return 0;
#else
    trace_stage(2, 0);
#endif
    trace_stage(40, 0);
    rc = sensor_start(&bus, &sample);
    bool power_ready = rc == 0;
    trace_stage(50, rc);
    if (rc)
        trace_failure(50, rc);
    if (!rc) {
        trace_stage(60, 0);
        rc = sensor_measure(&bus, &sample);
        if (rc)
            trace_failure(61, rc);
    }
    sensor_trace.sample = sample;
    sensor_status_sample(&sample, rc);
    int stop = fdc_bus_is_asleep(devices.fdc);
    if (!stop)
        stop = sensor_sensors_off(&bus);
    if (stop)
        power_backoff(&bus, stop);
    bool low_battery = sample.battery_mv < SENSOR_MIN_BATTERY_MV;
    if (rc || low_battery)
        power_backoff(&bus, rc ? rc : -ERANGE);
    if (power_ready) {
        rc = radio_window(&bus, &sample);
        if (rc)
            power_backoff(&bus, rc);
    }
    stop = sensor_stop(&bus);
    if (stop)
        power_backoff(&bus, stop);
    struct sensor_config config;
    sensor_settings_get(&config);
    uint32_t cycle_seconds = sensor_sleep_seconds(&config,
        sample.battery_mv < config.low_mv, k_uptime_get());
    sensor_trace.wake_seconds = cycle_seconds;
#if !CONFIG_SENSOR_OTA && defined(CONFIG_BOOTLOADER_MCUBOOT)
    if (!settings_rc && boot_write_img_confirmed())
        power_backoff(&bus, -EIO);
#endif
    rc = sensor_retained_state(&bus, SENSOR_POWER_CLEAN);
    if (rc)
        power_backoff(&bus, rc);
    trace_stage(83, 0);
    k_msleep(20);
    /* GRTC preparation disables kernel compare channels. Nothing that uses
     * I2C, delays, logging, or any kernel timeout may follow it. */
    int wake = z_nrf_grtc_wakeup_prepare((uint64_t)cycle_seconds * USEC_PER_SEC);
    if (wake) {
        sensor_trace.stage = 81;
        sensor_trace.error = wake;
        /* Fail closed: an external wake may be needed if no timer was armed. */
    }
    sys_poweroff();
    return 0;
}
