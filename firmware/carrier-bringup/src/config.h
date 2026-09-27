#ifndef SENSOR_CONFIG_H
#define SENSOR_CONFIG_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define SENSOR_CONFIG_SIZE 64
#define SENSOR_NAME_MAX 11
/* Explicit little-endian wire format, shared by GATT and ZMS. */
struct sensor_config {
    uint32_t cycle_s, low_cycle_s, window_ms;
    uint16_t adv_ms, session_s, low_mv;
    int32_t dry[2], wet[2];
    bool calibrated;
    char name[SENSOR_NAME_MAX + 1];
};
int sensor_config_validate(const struct sensor_config *c);
int sensor_config_decode(struct sensor_config *c, const uint8_t *data, size_t len);
void sensor_config_encode(const struct sensor_config *c, uint8_t out[SENSOR_CONFIG_SIZE]);
uint16_t sensor_moisture(int32_t ff, int32_t dry, int32_t wet);
uint32_t sensor_sleep_seconds(const struct sensor_config *c, bool low, uint64_t elapsed_ms);
/* MTU-23-safe transaction: begin=1, chunk=2/offset/data, commit=3/CRC32. */
struct config_transaction {
    uint8_t data[SENSOR_CONFIG_SIZE];
    uint64_t received;
    bool active;
};
uint32_t sensor_config_crc(const uint8_t *data, size_t len);
int sensor_config_command(struct config_transaction *t, const uint8_t *data, size_t len,
                          struct sensor_config *ready);
#endif
