#ifndef BOARD_BTHOME_H
#define BOARD_BTHOME_H

#include <stddef.h>
#include <stdint.h>

struct board_bthome_values {
    int16_t temperature_cc;
    uint16_t humidity_cpct;
    uint8_t battery_pct;
    uint16_t battery_mv;
    uint16_t moisture1_cpct;
    uint16_t moisture2_cpct;
    uint16_t diagnostic_stage;
    uint16_t diagnostic_error;
};

/* UUID FCD2 + info + measurements + two diagnostic count objects. */
#define BOARD_BTHOME_PAYLOAD_LEN 26
#define BOARD_BTHOME_DIAGNOSTIC_LEN 9

int board_bthome_encode(const struct board_bthome_values *values,
                        uint8_t *payload, size_t payload_len);
/* Failed samples carry diagnostics only; zero is a valid sensor reading. */
int board_bthome_encode_diagnostic(uint16_t stage, uint16_t error,
                                  uint8_t *payload, size_t payload_len);

#endif
