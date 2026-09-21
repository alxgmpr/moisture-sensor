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

int board_bthome_encode_diagnostic(uint16_t stage, uint16_t error, uint8_t *p, size_t n)
{
    if (!p || n < BOARD_BTHOME_DIAGNOSTIC_LEN)
        return -EINVAL;
    p[0] = 0xd2;
    p[1] = 0xfc;
    p[2] = 0x40;
    size_t i = put_u16(p, 3, 0x3d, stage);
    return (int)put_u16(p, i, 0x3d, error);
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
    i = put_u16(p, i, 0x14, v->moisture1_cpct);
    i = put_u16(p, i, 0x14, v->moisture2_cpct);
    /* 0x3d is the standard BTHome uint16 count object. Repeating it keeps
     * the packet standard while exposing stage and errno separately. */
    i = put_u16(p, i, 0x3d, v->diagnostic_stage);
    i = put_u16(p, i, 0x3d, v->diagnostic_error);
    return (int)i;
}
