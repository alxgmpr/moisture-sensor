#include "bthome.h"

#include <errno.h>

static size_t put_u16(uint8_t *p, size_t i, uint8_t object, uint16_t value)
{
    p[i++] = object;
    p[i++] = (uint8_t)value;
    p[i++] = (uint8_t)(value >> 8);
    return i;
}

static size_t put_u8(uint8_t *p, size_t i, uint8_t object, uint8_t value)
{
    p[i++] = object;
    p[i++] = value;
    return i;
}

int board_bthome_encode(const struct board_bthome_values *v,
                        uint8_t *p, size_t n)
{
    size_t i = 0;

    if (!v || !p || n < BOARD_BTHOME_PAYLOAD_LEN)
        return -EINVAL;

    /* BTHome v2, unencrypted. Multi-byte values are little endian. */
    p[i++] = 0xd2;
    p[i++] = 0xfc;
    p[i++] = 0x40;
    /* Objects are emitted in numerical order.  0x01 is battery percentage;
     * 0x0c is voltage in millivolts scaled by 0.001 V. */
    i = put_u8(p, i, 0x01, v->battery_pct);
    i = put_u16(p, i, 0x02, (uint16_t)v->temperature_cc);
    i = put_u16(p, i, 0x03, v->humidity_cpct);
    i = put_u16(p, i, 0x0c, v->battery_mv);
    if (!v->omit_moisture) {
        i = put_u16(p, i, 0x14, v->moisture1_cpct);
        i = put_u16(p, i, 0x14, v->moisture2_cpct);
    }
    return (int)i;
}
