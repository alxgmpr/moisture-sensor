#ifndef CARRIER_H
#define CARRIER_H
#include <stddef.h>
#include <stdint.h>
#define CARRIER_MIN_BATTERY_MV 2200
/* A status timeout is distinct from a failed bus transfer. Kept by the caller
 * so subsequent shutdown transactions cannot erase the original evidence. */
struct carrier_fault {
    int error;
    uint8_t address, reg;
    uint16_t observed, mask, expected;
};
/* Callbacks must bound each bus transaction. No concurrent users of this bus. */
struct carrier_bus {
    void *ctx;
    int (*transfer)(void *, uint8_t, const uint8_t *, size_t, uint8_t *, size_t);
    void (*delay_ms)(void *, unsigned);
    struct carrier_fault *fault;
};
struct carrier_sample {
    uint16_t battery_mv, output_mv;
    int16_t temperature_cc;
    uint16_t humidity_cpct;
    int32_t capacitance_ff[2];
    uint8_t capdac[2];
};
int carrier_start(const struct carrier_bus *, struct carrier_sample *);
int carrier_ota_start(const struct carrier_bus *);
int carrier_measure(const struct carrier_bus *, struct carrier_sample *);
/* Leave BOOST and the watchdog on while disconnecting the sensor supply. */
int carrier_sensors_off(const struct carrier_bus *);
/* Feed only while the foreground radio/OTA loop is making progress. */
int carrier_watchdog_feed(const struct carrier_bus *);
/* Only stops PMIC watchdog after the switched rail is confirmed disabled. */
int carrier_stop(const struct carrier_bus *);
uint8_t carrier_crc(const uint8_t *, size_t);
#endif
