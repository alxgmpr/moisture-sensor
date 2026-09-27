#ifndef SENSOR_CONFIG_SERVICE_H
#define SENSOR_CONFIG_SERVICE_H
#include "config.h"
#include "carrier.h"
int sensor_settings_init(void);
void sensor_settings_get(struct sensor_config *out);
/* Called only by foreground; no storage or I2C work in Bluetooth callbacks. */
void sensor_settings_process(void);
void sensor_status_sample(const struct carrier_sample *sample, int error);
bool sensor_sample_requested(void);
bool sensor_session_connected(void);
bool sensor_session_expired(void);
void sensor_session_disconnect(void);
void sensor_session_wait(uint32_t milliseconds);
void sensor_status_diagnostics(uint32_t reset, uint8_t pmic, uint8_t previous, uint8_t stage, uint8_t error);
#endif
