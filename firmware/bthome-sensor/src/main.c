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

	/* Non-connectable, non-scannable: there is no GATT service worth
	 * connecting to, and staying connectable would hold the radio up
	 * waiting for connections we do not want. */
	err = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_NONE,
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

int main(void)
{
	/* Fixed values for now; Task 4 replaces this with the simulation. */
	const struct bthome_values v = {
		.battery_pct = 87,
		.temperature_cc = 2345,
		.humidity_cpct = 4120,
		.moisture1_cpct = 6250,
		.moisture2_cpct = 5875,
	};
	uint8_t svc[BTHOME_ADV_DATA_LEN];

	printk("\n=== bthome-sensor ===\n");

	if (bthome_encode(&v, svc, sizeof(svc)) != BTHOME_ADV_DATA_LEN) {
		printk("encode failed\n");
		return 0;
	}

	printk("payload:");
	for (size_t i = 0; i < sizeof(svc); i++) {
		printk(" %02X", svc[i]);
	}
	printk("\n");

	advertise(svc);

	printk("cycle complete\n");
	return 0;
}
