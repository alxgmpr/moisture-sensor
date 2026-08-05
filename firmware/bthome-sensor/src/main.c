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

#include "bthome.h"

static void advertise(const uint8_t *svc_data)
{
	const struct bt_data ad[] = {
		BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
		BT_DATA(BT_DATA_SVC_DATA16, svc_data, BTHOME_ADV_DATA_LEN),
		BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_SENSOR_DEVICE_NAME,
			sizeof(CONFIG_SENSOR_DEVICE_NAME) - 1),
	};
	int err;

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
