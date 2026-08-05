/*
 * BTHome v2 service-data encoder.
 *
 * Pure C — no Zephyr, no hardware. Everything that can be got wrong about the
 * wire format lives in this module so it can be tested on the host.
 */
#ifndef BTHOME_H_
#define BTHOME_H_

#include <stddef.h>
#include <stdint.h>

/*
 * Every field is mandatory, and there is deliberately no way to express an
 * absent measurement. BTHome binds the second moisture value positionally, so
 * omitting one field would silently rebind SENSE2's reading to Home
 * Assistant's `moisture` entity with no error raised anywhere.
 */
struct bthome_values {
	uint8_t  battery_pct;     /* 0..100 */
	int16_t  temperature_cc;  /* hundredths of a degree C */
	uint16_t humidity_cpct;   /* hundredths of a percent */
	uint16_t moisture1_cpct;  /* hundredths of a percent, SENSE1 */
	uint16_t moisture2_cpct;  /* hundredths of a percent, SENSE2 */
};

/* UUID (2) + device info (1) + five measurements (14). */
#define BTHOME_ADV_DATA_LEN 17

/*
 * Writes the complete BTHome service-data payload — 0xFCD2 little endian, the
 * device-info byte, then the measurements — into buf. The caller wraps this in
 * an AD element of type BT_DATA_SVC_DATA16; the length and type bytes are the
 * Bluetooth stack's job, not ours.
 *
 * Returns BTHOME_ADV_DATA_LEN, or -1 if any argument is NULL or buf_len is too
 * small.
 */
int bthome_encode(const struct bthome_values *v, uint8_t *buf, size_t buf_len);

#endif /* BTHOME_H_ */
