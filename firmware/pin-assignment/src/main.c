/*
 * Pin-assignment fire-test — nRF54L15 DK (PCA10156).
 *
 * Proves or refutes the datasheet readings that set the I2C pinout in
 * HARDWARE.md §6. One build is one test case; the case is named and its
 * expected outcome declared in Kconfig, so an unexpected result is reported
 * as such rather than left for the operator to notice.
 *
 * The bus is driven raw rather than through the bme280 sensor driver. A
 * driver that retries would hide a marginal bus, and what is under test is the
 * pin assignment, not the sensor.
 *
 * Integrity checking: the BME280 has no CRC on its I2C transfers, so a
 * corrupt byte is indistinguishable from a real one at the protocol level.
 * Instead each pass re-reads the 26-byte factory calibration block and
 * compares it against the copy read at startup. That block is constant for
 * the life of the part, so any difference is the bus, not the sensor — and 26
 * bytes of known-good data catches far more than a single register would.
 */

#include <stdlib.h>
#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/printk.h>

/* Breakouts differ: SDO low is 0x76, SDO high is 0x77. Probe both. */
static const uint8_t candidate_addr[] = { 0x76, 0x77 };

#define REG_CALIB	0x88	/* calib00..25, 26 bytes, constant */
#define REG_ID		0xD0
#define REG_RESET	0xE0
#define REG_CTRL_HUM	0xF2
#define REG_STATUS	0xF3
#define REG_CTRL_MEAS	0xF4
#define REG_TEMP	0xFA	/* 20-bit, 3 bytes */

#define CALIB_LEN	26

#define ID_BME280	0x60
#define ID_BMP280	0x58	/* many "BME280" boards are really this */

/* osrs_t x1, osrs_p x1, forced mode */
#define CTRL_MEAS_FORCED 0x25

/* Enough passes to catch a bus that works once and then does not. A pin that
 * violates the clock-pin rule may well enumerate and fail intermittently. */
#define PASSES		20

static const struct device *const bus = DEVICE_DT_GET(DT_ALIAS(testbus));

static uint8_t addr;
static uint8_t calib_ref[CALIB_LEN];
static uint16_t dig_T1;
static int16_t dig_T2, dig_T3;

static int reg_read(uint8_t reg, uint8_t *buf, size_t len)
{
	return i2c_write_read(bus, addr, &reg, 1, buf, len);
}

static int reg_write(uint8_t reg, uint8_t val)
{
	uint8_t buf[2] = { reg, val };

	return i2c_write(bus, buf, sizeof(buf), addr);
}

/* Bosch's integer compensation, temperature only (BME280 datasheet §4.2.3).
 * Returns hundredths of a degree C. */
static int32_t compensate_temp(int32_t adc_T)
{
	int32_t var1, var2;

	var1 = (((adc_T >> 3) - ((int32_t)dig_T1 << 1)) * (int32_t)dig_T2) >> 11;
	var2 = ((((adc_T >> 4) - (int32_t)dig_T1) *
		 ((adc_T >> 4) - (int32_t)dig_T1)) >> 12) * (int32_t)dig_T3 >> 14;

	return ((var1 + var2) * 5 + 128) >> 8;
}

/* Returns the chip ID, or a negative error. */
static int probe(void)
{
	uint8_t id;
	int err;

	for (size_t i = 0; i < ARRAY_SIZE(candidate_addr); i++) {
		addr = candidate_addr[i];

		err = reg_read(REG_ID, &id, 1);
		if (err == 0 && (id == ID_BME280 || id == ID_BMP280)) {
			return id;
		}
	}

	addr = 0;
	return -ENODEV;
}

/* One measurement cycle plus an integrity check. Exercises writes as well as
 * reads, so a pin that only fails in one direction still shows up. */
static int one_pass(int32_t *temp_centi, bool *integrity_ok)
{
	uint8_t calib[CALIB_LEN];
	uint8_t raw[3];
	int32_t adc_T;
	int err;

	/* ctrl_hum must be written before ctrl_meas or it does not latch. */
	err = reg_write(REG_CTRL_HUM, 0x01);
	if (err) {
		return err;
	}

	err = reg_write(REG_CTRL_MEAS, CTRL_MEAS_FORCED);
	if (err) {
		return err;
	}

	k_msleep(10);

	err = reg_read(REG_CALIB, calib, sizeof(calib));
	if (err) {
		return err;
	}

	*integrity_ok = (memcmp(calib, calib_ref, CALIB_LEN) == 0);

	err = reg_read(REG_TEMP, raw, sizeof(raw));
	if (err) {
		return err;
	}

	adc_T = ((int32_t)raw[0] << 12) | ((int32_t)raw[1] << 4) | (raw[2] >> 4);
	if (adc_T == 0x80000) {
		/* Reset value — the conversion never ran. */
		return -ENODATA;
	}

	*temp_centi = compensate_temp(adc_T);

	return 0;
}

int main(void)
{
	int ok = 0, bus_err = 0, corrupt = 0;
	int32_t temp_centi = 0;
	bool integrity_ok;
	int id, err;

	printk("\n=== %s ===\n", CONFIG_TEST_LABEL);
	printk("expecting: %s\n", IS_ENABLED(CONFIG_TEST_EXPECT_PASS) ? "PASS" : "FAIL");
	printk("bus:       %s\n", bus->name);

	if (!device_is_ready(bus)) {
		printk("bus not ready — the instance failed to initialise.\n");
		printk("VERDICT: FAIL (no bus)%s\n",
		       IS_ENABLED(CONFIG_TEST_EXPECT_PASS) ? "  *** UNEXPECTED ***" : "");
		return 0;
	}

	id = probe();
	if (id < 0) {
		printk("no BME280/BMP280 at 0x76 or 0x77 (%d)\n", id);
		printk("VERDICT: FAIL (no device)%s\n",
		       IS_ENABLED(CONFIG_TEST_EXPECT_PASS)
			       ? "  *** UNEXPECTED — check wiring before trusting this ***" : "");
		return 0;
	}

	printk("found 0x%02x at 0x%02x (%s)\n", id, addr,
	       (id == ID_BME280) ? "BME280" : "BMP280, no humidity");

	err = reg_read(REG_CALIB, calib_ref, sizeof(calib_ref));
	if (err) {
		printk("calibration read failed (%d) — cannot establish a reference\n", err);
		return 0;
	}

	dig_T1 = (uint16_t)(calib_ref[0] | (calib_ref[1] << 8));
	dig_T2 = (int16_t)(calib_ref[2] | (calib_ref[3] << 8));
	dig_T3 = (int16_t)(calib_ref[4] | (calib_ref[5] << 8));

	printk("calibration reference: T1=%u T2=%d T3=%d\n", dig_T1, dig_T2, dig_T3);

	for (int i = 0; i < PASSES; i++) {
		integrity_ok = false;

		err = one_pass(&temp_centi, &integrity_ok);
		if (err) {
			bus_err++;
		} else if (!integrity_ok) {
			corrupt++;
		} else {
			ok++;
		}

		k_msleep(20);
	}

	if (ok > 0) {
		/* Report the last conversion so the operator can sanity check
		 * it against the room, not just trust a counter. */
		printk("last reading: %d.%02d C\n",
		       temp_centi / 100, abs(temp_centi % 100));
	}

	printk("result: %d/%d ok  (%d bus errors, %d calibration mismatches)\n",
	       ok, PASSES, bus_err, corrupt);

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
