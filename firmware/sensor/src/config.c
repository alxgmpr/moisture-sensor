#include "config.h"
#include <errno.h>
#include <string.h>
static uint16_t get16(const uint8_t *p) { return p[0] | (uint16_t)p[1] << 8; }
static uint32_t get32(const uint8_t *p) { return get16(p) | (uint32_t)get16(p + 2) << 16; }
static void put16(uint8_t *p, uint16_t v) { p[0] = v; p[1] = v >> 8; }
static void put32(uint8_t *p, uint32_t v) { put16(p, v); put16(p + 2, v >> 16); }
int sensor_config_validate(const struct sensor_config *c)
{
    if (c->cycle_s < 60 || c->cycle_s > 86400 || c->low_cycle_s < c->cycle_s ||
        c->low_cycle_s > 604800 || c->window_ms < 5000 || c->window_ms > 300000 ||
        c->window_ms > (uint64_t)c->cycle_s * 500 ||
        c->adv_ms < 100 || c->adv_ms > 5000 || c->adv_ms % 5 ||
        c->window_ms < (uint32_t)c->adv_ms * 5 ||
        c->session_s < 30 || c->session_s > 900 || c->low_mv < 800 || c->low_mv > 3300)
        return -EINVAL;
    size_t n = 0;
    while (n <= SENSOR_NAME_MAX && c->name[n]) {
        if (c->name[n] < 32 || c->name[n] > 126)
            return -EINVAL;
        n++;
    }
    if (n > SENSOR_NAME_MAX)
        return -EINVAL;
    for (unsigned i = 0; i < 2; i++) {
        if (c->dry[i] < -15000 || c->dry[i] > 115000 ||
            c->wet[i] < -15000 || c->wet[i] > 115000 || c->dry[i] == c->wet[i])
            return -EINVAL;
    }
    return 0;
}
void sensor_config_encode(const struct sensor_config *c, uint8_t p[SENSOR_CONFIG_SIZE])
{
    memset(p, 0, SENSOR_CONFIG_SIZE);
    p[0] = 1;
    p[1] = c->calibrated;
    p[2] = strlen(c->name);
    put32(p + 4, c->cycle_s); put32(p + 8, c->low_cycle_s); put32(p + 12, c->window_ms);
    put16(p + 16, c->adv_ms); put16(p + 18, c->session_s); put16(p + 20, c->low_mv);
    put32(p + 24, c->dry[0]); put32(p + 28, c->wet[0]);
    put32(p + 32, c->dry[1]); put32(p + 36, c->wet[1]);
    memcpy(p + 40, c->name, p[2]);
}
int sensor_config_decode(struct sensor_config *c, const uint8_t *p, size_t len)
{
    if (len != SENSOR_CONFIG_SIZE || p[0] != 1 || p[1] > 1 || p[2] > SENSOR_NAME_MAX ||
        p[3] || p[22] || p[23])
        return -EINVAL;
    for (unsigned i = 40 + p[2]; i < SENSOR_CONFIG_SIZE; i++)
        if (p[i]) return -EINVAL;
    struct sensor_config v = {
        .cycle_s = get32(p + 4), .low_cycle_s = get32(p + 8), .window_ms = get32(p + 12),
        .adv_ms = get16(p + 16), .session_s = get16(p + 18), .low_mv = get16(p + 20),
        .dry = {(int32_t)get32(p + 24), (int32_t)get32(p + 32)},
        .wet = {(int32_t)get32(p + 28), (int32_t)get32(p + 36)}, .calibrated = p[1],
    };
    memcpy(v.name, p + 40, p[2]);
    /* Reject embedded NULs so each configuration has one canonical encoding. */
    if (strlen(v.name) != p[2] || sensor_config_validate(&v)) return -EINVAL;
    *c = v;
    return 0;
}
uint16_t sensor_moisture(int32_t ff, int32_t dry, int32_t wet)
{
    int64_t span = (int64_t)wet - dry;
    if (!span) return 0;
    int64_t v = ((int64_t)ff - dry) * 10000 / span;
    return v < 0 ? 0 : v > 10000 ? 10000 : (uint16_t)v;
}
uint32_t sensor_sleep_seconds(const struct sensor_config *c, bool low, uint64_t elapsed_ms)
{
    uint32_t interval = low ? c->low_cycle_s : c->cycle_s;
    uint64_t elapsed_s = (elapsed_ms + 999) / 1000;
    /* Never spin through cold boots after a long configuration/OTA session. */
    return elapsed_s >= interval ? interval : interval - (uint32_t)elapsed_s;
}
uint32_t sensor_config_crc(const uint8_t *data, size_t len)
{
    uint32_t crc = UINT32_MAX;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (unsigned b = 0; b < 8; b++)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1)));
    }
    return ~crc;
}
int sensor_config_command(struct config_transaction *t, const uint8_t *p, size_t len,
                          struct sensor_config *ready)
{
    if (!len || len > 20) return -EINVAL;
    if (p[0] == 1 && len == 1) {
        *t = (struct config_transaction){.active = true};
        return 0;
    }
    if (!t->active) return -EINVAL;
    if (p[0] == 2 && len >= 3 && p[1] + len - 2 <= SENSOR_CONFIG_SIZE) {
        for (size_t i = 2; i < len; i++) {
            t->data[p[1] + i - 2] = p[i];
            t->received |= UINT64_C(1) << (p[1] + i - 2);
        }
        return 0;
    }
    if (p[0] == 3 && len == 5 && t->received == UINT64_MAX &&
        get32(p + 1) == sensor_config_crc(t->data, sizeof(t->data))) {
        t->active = false;
        return sensor_config_decode(ready, t->data, sizeof(t->data)) ? -EINVAL : 1;
    }
    return -EINVAL;
}
