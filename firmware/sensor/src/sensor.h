#ifndef SENSOR_H
#define SENSOR_H
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
/* Board policy, in PMIC ADC millivolts; cell sag still requires qualification. */
#define SENSOR_MIN_BATTERY_MV 1800
#define SENSOR_RECOVER_BATTERY_MV 2000
#define SENSOR_POWER_CLEAN 0xa0
#define SENSOR_POWER_ATTEMPT 0xa1
#define SENSOR_POWER_BLOCKED 0xa2
#define SENSOR_POWER_BOOTING 0xa3
/* A status timeout is distinct from a failed bus transfer. Kept by the caller
 * so subsequent shutdown transactions cannot erase the original evidence. */
struct sensor_fault {
    int error;
    uint8_t address, reg;
    uint16_t observed, mask, expected;
};
/* Callbacks must bound each bus transaction. No concurrent users of this bus. */
struct sensor_bus {
    void *ctx;
    int (*transfer)(void *, uint8_t, const uint8_t *, size_t, uint8_t *, size_t);
    void (*delay_ms)(void *, unsigned);
    struct sensor_fault *fault;
};
struct sensor_sample {
    uint16_t battery_mv, output_mv;
    int16_t temperature_cc;
    uint16_t humidity_cpct;
    int32_t capacitance_ff[2];
    uint8_t capdac[2];
};
int sensor_start(const struct sensor_bus *, struct sensor_sample *);
int sensor_ota_start(const struct sensor_bus *);
int sensor_measure(const struct sensor_bus *, struct sensor_sample *);
/* Leave BOOST and the watchdog on while disconnecting the sensor supply. */
int sensor_sensors_off(const struct sensor_bus *);
/* Bench trial: automatic BOOST during BLE, with sensors off and watchdog armed. */
int sensor_radio_start(const struct sensor_bus *);
/* Feed only while the foreground radio/OTA loop is making progress. */
int sensor_watchdog_feed(const struct sensor_bus *);
int sensor_watchdog_start(const struct sensor_bus *, uint32_t seconds);
/* Only stops PMIC watchdog after the switched rail is confirmed disabled. */
int sensor_stop(const struct sensor_bus *);
uint8_t sensor_crc(const uint8_t *, size_t);
int sensor_retained_read(const struct sensor_bus *, uint8_t *, uint8_t *, uint8_t *);
int sensor_retained_state(const struct sensor_bus *, uint8_t);
int sensor_retained_stage(const struct sensor_bus *, uint8_t);
int sensor_battery_read(const struct sensor_bus *, uint16_t *);
int sensor_power_probe(const struct sensor_bus *, uint16_t *);
int sensor_hibernate(const struct sensor_bus *, uint32_t seconds);
bool sensor_power_allowed(uint16_t mv, uint8_t retained);
#endif
