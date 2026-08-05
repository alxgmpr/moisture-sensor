#include "bthome.h"

/* Service UUID 0xFCD2, transmitted little endian. */
#define BTHOME_UUID_LO 0xD2
#define BTHOME_UUID_HI 0xFC

/* Bits 5-7 hold the BTHome version (2); bit 0 clear means unencrypted. This
 * single byte is the whole encryption seam — it becomes 0x41 when encryption
 * is turned on. */
#define BTHOME_DEVICE_INFO 0x40

#define OBJ_BATTERY     0x01   /* uint8,  factor 1    */
#define OBJ_TEMPERATURE 0x02   /* sint16, factor 0.01 */
#define OBJ_HUMIDITY    0x03   /* uint16, factor 0.01 */
#define OBJ_MOISTURE    0x14   /* uint16, factor 0.01 */

static size_t put_u8(uint8_t *buf, size_t i, uint8_t obj, uint8_t val)
{
	buf[i++] = obj;
	buf[i++] = val;
	return i;
}

static size_t put_u16(uint8_t *buf, size_t i, uint8_t obj, uint16_t val)
{
	buf[i++] = obj;
	buf[i++] = (uint8_t)(val & 0xFFU);
	buf[i++] = (uint8_t)(val >> 8);
	return i;
}

int bthome_encode(const struct bthome_values *v, uint8_t *buf, size_t buf_len)
{
	size_t i = 0;

	if (v == NULL || buf == NULL || buf_len < BTHOME_ADV_DATA_LEN) {
		return -1;
	}

	buf[i++] = BTHOME_UUID_LO;
	buf[i++] = BTHOME_UUID_HI;
	buf[i++] = BTHOME_DEVICE_INFO;

	/* Ascending object id, and SENSE1 before SENSE2. The moisture ordering
	 * is load-bearing: Home Assistant assigns the `_2` postfix by position,
	 * and the BTHome spec requires the same order in every advertisement. */
	i = put_u8(buf, i, OBJ_BATTERY, v->battery_pct);
	i = put_u16(buf, i, OBJ_TEMPERATURE, (uint16_t)v->temperature_cc);
	i = put_u16(buf, i, OBJ_HUMIDITY, v->humidity_cpct);
	i = put_u16(buf, i, OBJ_MOISTURE, v->moisture1_cpct);
	i = put_u16(buf, i, OBJ_MOISTURE, v->moisture2_cpct);

	return (int)i;
}
