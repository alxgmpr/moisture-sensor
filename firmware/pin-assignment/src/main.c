/*
 * Pin-assignment fire-test — nRF54L15 DK (PCA10156).
 *
 * Proves or refutes the datasheet readings that set the I2C pinout in
 * HARDWARE.md §6. One build is one test case; the case is named and its
 * expected outcome declared in Kconfig, so an unexpected result is reported
 * as such rather than left for the operator to notice.
 *
 * The bus is driven raw rather than through the sht4x sensor driver. A driver
 * that retries would hide a marginal bus, and what is under test is the pin
 * assignment, not the sensor.
 */

#include <stdlib.h>

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/printk.h>

#define SHT4X_ADDR		0x44
#define SHT4X_CMD_SERIAL	0x89
#define SHT4X_CMD_MEASURE_HI	0xFD

/* Enough passes to catch a bus that works once and then does not. A pin that
 * violates the clock-pin rule may well enumerate and fail intermittently. */
#define PASSES			20

static const struct device *const bus = DEVICE_DT_GET(DT_ALIAS(testbus));

/* CRC-8, polynomial 0x31, init 0xFF — SHT4x datasheet §4.4. */
static uint8_t sht4x_crc(const uint8_t *data, size_t len)
{
	uint8_t crc = 0xFF;

	for (size_t i = 0; i < len; i++) {
		crc ^= data[i];
		for (int bit = 0; bit < 8; bit++) {
			crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x31)
					   : (uint8_t)(crc << 1);
		}
	}

	return crc;
}

/* One command/response round trip with both CRCs checked. The SHT4x wants a
 * stop between the command and the read, so this is not i2c_write_read(). */
static int sht4x_transact(uint8_t cmd, uint32_t delay_ms, uint8_t rx[6])
{
	int err;

	err = i2c_write(bus, &cmd, 1, SHT4X_ADDR);
	if (err) {
		return err;
	}

	k_msleep(delay_ms);

	err = i2c_read(bus, rx, 6, SHT4X_ADDR);
	if (err) {
		return err;
	}

	if (sht4x_crc(&rx[0], 2) != rx[2] || sht4x_crc(&rx[3], 2) != rx[5]) {
		/* Bytes arrived but are corrupt — the interesting failure. A
		 * mis-timed clock shows up here, not as a NAK. */
		return -EIO;
	}

	return 0;
}

int main(void)
{
	uint8_t rx[6];
	int ok = 0, nak = 0, crc = 0;
	int err;

	printk("\n=== %s ===\n", CONFIG_TEST_LABEL);
	printk("expecting: %s\n", IS_ENABLED(CONFIG_TEST_EXPECT_PASS) ? "PASS" : "FAIL");
	printk("bus:       %s\n", bus->name);

	if (!device_is_ready(bus)) {
		printk("bus not ready — the instance failed to initialise.\n");
		printk("VERDICT: FAIL (no bus)%s\n",
		       IS_ENABLED(CONFIG_TEST_EXPECT_PASS) ? "  *** UNEXPECTED ***" : "");
		return 0;
	}

	err = sht4x_transact(SHT4X_CMD_SERIAL, 10, rx);
	if (err == 0) {
		printk("sensor serial: %02x%02x%02x%02x\n",
		       rx[0], rx[1], rx[3], rx[4]);
	} else {
		printk("serial read failed (%d) — check wiring and address 0x%02x\n",
		       err, SHT4X_ADDR);
	}

	for (int i = 0; i < PASSES; i++) {
		err = sht4x_transact(SHT4X_CMD_MEASURE_HI, 10, rx);
		if (err == 0) {
			ok++;
		} else if (err == -EIO) {
			crc++;
		} else {
			nak++;
		}
		k_msleep(20);
	}

	if (ok > 0) {
		/* Report the last good conversion so the operator can sanity
		 * check it against the room, not just trust a counter. */
		uint16_t t_ticks = ((uint16_t)rx[0] << 8) | rx[1];
		uint16_t rh_ticks = ((uint16_t)rx[3] << 8) | rx[4];
		int t_milli = -45000 + (175000LL * t_ticks) / 65535;
		int rh_milli = -6000 + (125000LL * rh_ticks) / 65535;

		printk("last reading: %d.%03d C, %d.%03d %%RH\n",
		       t_milli / 1000, abs(t_milli % 1000),
		       rh_milli / 1000, abs(rh_milli % 1000));
	}

	printk("result: %d/%d ok  (%d bus errors, %d CRC failures)\n",
	       ok, PASSES, nak, crc);

	/* A partial pass is a fail. An intermittent bus is exactly what a
	 * violated timing rule looks like, and it is not a result we can
	 * design against. */
	bool passed = (ok == PASSES);

	printk("VERDICT: %s%s\n",
	       passed ? "PASS" : "FAIL",
	       (passed == IS_ENABLED(CONFIG_TEST_EXPECT_PASS))
		       ? "" : "  *** UNEXPECTED — the datasheet reading in HARDWARE.md §6 is wrong ***");

	return 0;
}
