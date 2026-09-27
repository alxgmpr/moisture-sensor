#ifndef BOARD_BTHOME_H
#define BOARD_BTHOME_H

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

struct board_bthome_values {
    int16_t temperature_cc;
    uint16_t humidity_cpct;
    uint8_t battery_pct;
    uint16_t battery_mv;
    uint16_t moisture1_cpct;
    uint16_t moisture2_cpct;
    bool omit_moisture;
};

/* UUID FCD2 + info + battery, temperature, humidity, voltage, and two probes. */
#define BOARD_BTHOME_PAYLOAD_LEN 20

int board_bthome_encode(const struct board_bthome_values *values,
                        uint8_t *payload, size_t payload_len);
#endif
