#ifndef CARRIER_H
#define CARRIER_H
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
/* Board policy, in PMIC ADC millivolts; cell sag still requires qualification. */
#define CARRIER_MIN_BATTERY_MV 1800
#define CARRIER_RECOVER_BATTERY_MV 2000
#define CARRIER_POWER_CLEAN 0xa0
#define CARRIER_POWER_ATTEMPT 0xa1
#define CARRIER_POWER_BLOCKED 0xa2
#define CARRIER_POWER_BOOTING 0xa3
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
/* Bench trial: automatic BOOST during BLE, with sensors off and watchdog armed. */
int carrier_radio_start(const struct carrier_bus *);
/* Feed only while the foreground radio/OTA loop is making progress. */
int carrier_watchdog_feed(const struct carrier_bus *);
int carrier_watchdog_start(const struct carrier_bus *, uint32_t seconds);
/* Only stops PMIC watchdog after the switched rail is confirmed disabled. */
int carrier_stop(const struct carrier_bus *);
uint8_t carrier_crc(const uint8_t *, size_t);
int carrier_retained_read(const struct carrier_bus *, uint8_t *, uint8_t *, uint8_t *);
int carrier_retained_state(const struct carrier_bus *, uint8_t);
int carrier_retained_stage(const struct carrier_bus *, uint8_t);
int carrier_battery_read(const struct carrier_bus *, uint16_t *);
int carrier_power_probe(const struct carrier_bus *, uint16_t *);
int carrier_hibernate(const struct carrier_bus *, uint32_t seconds);
bool carrier_power_allowed(uint16_t mv, uint8_t retained);
#endif
