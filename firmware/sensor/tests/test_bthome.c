#include "bthome.h"

#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <string.h>

int main(void)
{
    const struct board_bthome_values v = {
        .temperature_cc = -1234,
        .humidity_cpct = 5678,
        .battery_pct = 87,
        .battery_mv = 3012,
        .moisture1_cpct = 2500,
        .moisture2_cpct = 10000,
    };
    const uint8_t expected[] = {
        0xd2, 0xfc, 0x40,
        0x01, 0x57,
        0x02, 0x2e, 0xfb,
        0x03, 0x2e, 0x16,
        0x0c, 0xc4, 0x0b,
        0x14, 0xc4, 0x09,
        0x14, 0x10, 0x27,
    };
    uint8_t actual[BOARD_BTHOME_PAYLOAD_LEN];

    assert(board_bthome_encode(&v, actual, sizeof actual) == (int)sizeof actual);
    assert(memcmp(actual, expected, sizeof expected) == 0);
    assert(board_bthome_encode(NULL, actual, sizeof actual) == -EINVAL);
    assert(board_bthome_encode(&v, actual, sizeof actual - 1) == -EINVAL);
    struct board_bthome_values uncalibrated = v;
    uncalibrated.omit_moisture = true;
    assert(board_bthome_encode(&uncalibrated, actual, sizeof actual) == 14);
    assert(!memcmp(actual, expected, 14));
    return 0;
}
