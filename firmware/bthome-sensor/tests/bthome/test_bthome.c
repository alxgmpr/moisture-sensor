/*
 * Host tests for the BTHome encoder. Plain C and plain asserts: the module
 * under test has no Zephyr dependency by design, so the test should not
 * invent one. Compiles and runs in well under a second with the system cc.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../../src/bthome.h"

static int failures;

static void expect_bytes(const char *name, const uint8_t *got,
			 const uint8_t *want, size_t len)
{
	if (memcmp(got, want, len) == 0) {
		printf("PASS %s\n", name);
		return;
	}

	failures++;
	printf("FAIL %s\n  want:", name);
	for (size_t i = 0; i < len; i++) {
		printf(" %02X", want[i]);
	}
	printf("\n  got: ");
	for (size_t i = 0; i < len; i++) {
		printf(" %02X", got[i]);
	}
	printf("\n");
}

static void expect_int(const char *name, int got, int want)
{
	if (got == want) {
		printf("PASS %s\n", name);
		return;
	}
	failures++;
	printf("FAIL %s: want %d, got %d\n", name, want, got);
}

/* battery 87 %, 23.45 C, 41.20 %RH, SENSE1 62.50 %, SENSE2 58.75 % */
static const struct bthome_values nominal = {
	.battery_pct = 87,
	.temperature_cc = 2345,
	.humidity_cpct = 4120,
	.moisture1_cpct = 6250,
	.moisture2_cpct = 5875,
};

static void test_golden_vector(void)
{
	static const uint8_t want[BTHOME_ADV_DATA_LEN] = {
		0xD2, 0xFC,             /* service UUID 0xFCD2, little endian */
		0x40,                   /* BTHome v2, unencrypted */
		0x01, 0x57,             /* battery 87 */
		0x02, 0x29, 0x09,       /* temperature 2345 */
		0x03, 0x18, 0x10,       /* humidity 4120 */
		0x14, 0x6A, 0x18,       /* moisture 6250   (SENSE1) */
		0x14, 0xF3, 0x16,       /* moisture 5875   (SENSE2) */
	};
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	expect_int("golden returns full length",
		   bthome_encode(&nominal, buf, sizeof(buf)), BTHOME_ADV_DATA_LEN);
	expect_bytes("golden vector", buf, want, sizeof(want));
}

static void test_negative_temperature(void)
{
	struct bthome_values v = nominal;
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	v.temperature_cc = -500;   /* -5.00 C -> 0xFE0C -> 0C FE little endian */
	bthome_encode(&v, buf, sizeof(buf));

	expect_int("negative temp low byte", buf[6], 0x0C);
	expect_int("negative temp high byte", buf[7], 0xFE);
}

static void test_moisture_order(void)
{
	struct bthome_values v = nominal;
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	/* SENSE1 must land at offset 12-13 and SENSE2 at 15-16. Home Assistant
	 * assigns moisture_2 by position, so a swap here silently binds the
	 * wrong electrode to the wrong entity with no error anywhere. */
	v.moisture1_cpct = 0x1111;
	v.moisture2_cpct = 0x2222;
	bthome_encode(&v, buf, sizeof(buf));

	expect_int("sense1 low byte", buf[12], 0x11);
	expect_int("sense1 high byte", buf[13], 0x11);
	expect_int("sense2 low byte", buf[15], 0x22);
	expect_int("sense2 high byte", buf[16], 0x22);
}

static void test_buffer_too_small(void)
{
	uint8_t buf[BTHOME_ADV_DATA_LEN - 1];

	expect_int("short buffer rejected",
		   bthome_encode(&nominal, buf, sizeof(buf)), -1);
}

static void test_null_arguments(void)
{
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	expect_int("null values rejected", bthome_encode(NULL, buf, sizeof(buf)), -1);
	expect_int("null buffer rejected", bthome_encode(&nominal, NULL, 99), -1);
}

int main(void)
{
	test_golden_vector();
	test_negative_temperature();
	test_moisture_order();
	test_buffer_too_small();
	test_null_arguments();

	printf("\n%s\n", failures ? "TESTS FAILED" : "all tests passed");
	return failures ? 1 : 0;
}
