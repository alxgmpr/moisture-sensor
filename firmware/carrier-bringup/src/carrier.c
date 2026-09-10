#include "carrier.h"
#include <errno.h>
uint8_t carrier_crc(const uint8_t *d, size_t n) {
    uint8_t crc = 0xff;
    for (size_t i = 0; i < n; i++) {
        crc ^= d[i];
        for (int j = 0; j < 8; j++)
            crc = (crc & 0x80) ? (crc << 1) ^ 0x31 : crc << 1;
    }
    return crc;
}
#define TRY(expr)                                                                                  \
    do {                                                                                           \
        int rc = (expr);                                                                           \
        if (rc < 0)                                                                                \
            return rc;                                                                             \
    } while (0)
static int wr(const struct carrier_bus *b, uint8_t reg, uint8_t value) {
    uint8_t w[] = {reg, value};
    return b->transfer(b->ctx, 0x74, w, 2, 0, 0);
}
static int rd(const struct carrier_bus *b, uint8_t reg, uint8_t *value) {
    return b->transfer(b->ctx, 0x74, &reg, 1, value, 1);
}
static int checked(const struct carrier_bus *b, uint8_t reg, uint8_t value) {
    uint8_t v;
    TRY(wr(b, reg, value));
    TRY(rd(b, reg, &v));
    return v == value ? 0 : -EIO;
}
static int wait_pm(const struct carrier_bus *b, uint8_t reg, uint8_t mask, uint8_t value) {
    for (int i = 0; i < 30; i++) {
        uint8_t v;
        TRY(rd(b, reg, &v));
        if ((v & mask) == value)
            return 0;
        b->delay_ms(b->ctx, 1);
    }
    return -ETIMEDOUT;
}
static int adc(const struct carrier_bus *b, uint8_t mode, uint16_t *mv) {
    uint8_t v, bit = mode == 4 ? 8 : 1;
    TRY(wr(b, 0x06, bit)); /* Clear stale ADC ready event before triggering. */
    TRY(checked(b, 0x91, mode));
    TRY(wr(b, 0x90, 1));
    TRY(wait_pm(b, 0x01, bit, bit));
    TRY(rd(b, mode == 4 ? 0x99 : 0x96, &v));
    *mv = mode == 4 ? 1800 + (1500 * (unsigned)v) / 256 : (3200 * (unsigned)v) / 256;
    return 0;
}
int carrier_start(const struct carrier_bus *b, struct carrier_sample *s) {
    /* nPM2100 remains powered across MCU System OFF and watchdog resets. */
    TRY(checked(b, 0x69, 0));
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    TRY(checked(b, 0xd6, 1)); /* Also disable LDOSW on watchdog reset. */
    /* 20 s watchdog with power cycle: 20*64-1=1279, big endian. */
    TRY(checked(b, 0xb4, 0));
    TRY(checked(b, 0xb5, 4));
    TRY(checked(b, 0xb6, 255));
    TRY(checked(b, 0xb3, 2));
    TRY(wr(b, 0xb0, 1));
    TRY(adc(b, 0, &s->battery_mv));
    if (s->battery_mv < 2200)
        return -ERANGE; /* Provisional CR2032 load cutoff. */
    TRY(checked(b, 0x22, 30));
    TRY(checked(b, 0x23, 1)); /* 3.3 V */
    TRY(checked(b, 0x24, 1)); /* Force HP throughout sensing and advertising. */
    TRY(wait_pm(b, 0x34, 7, 0)); /* Confirm actual converter state is HP. */
    b->delay_ms(b->ctx, 5);
    TRY(adc(b, 4, &s->output_mv));
    if (s->output_mv < 3150)
        return -ERANGE;
    TRY(checked(b, 0x6a, 5));    /* Load switch, forced HP, not default LDO. */
    TRY(checked(b, 0x6f, 0x14)); /* 40 mA load-switch OCP, retain LDO default. */
    TRY(checked(b, 0x6c, 1));
    TRY(checked(b, 0x69, 1));
    TRY(wait_pm(b, 0x6e, 0x16, 6));
    b->delay_ms(b->ctx, 5);
    return 0;
}
static int fdc_read(const struct carrier_bus *b, uint8_t reg, uint16_t *v) {
    uint8_t r[2];
    TRY(b->transfer(b->ctx, 0x50, &reg, 1, r, 2));
    *v = ((uint16_t)r[0] << 8) | r[1];
    return 0;
}
static int fdc_write(const struct carrier_bus *b, uint8_t reg, uint16_t v) {
    uint8_t w[] = {reg, v >> 8, v};
    return b->transfer(b->ctx, 0x50, w, 3, 0, 0);
}
static int capacitance(const struct carrier_bus *b, unsigned ch, int32_t *ff, uint8_t *dac) {
    /* Only single-ended CAPDAC mode: this PCB physically ties SHLD1 to SHLD2. */
    for (unsigned d = 0; d < 32; d++) {
        TRY(fdc_write(b, 8, (ch << 13) | (4 << 10) | (d << 5)));
        TRY(fdc_write(b, 12, 0x480)); /* One measurement, 100 sps, no repeat. */
        unsigned i;
        for (i = 0; i < 30; i++) {
            uint16_t status;
            TRY(fdc_read(b, 12, &status));
            if (status & 8)
                break;
            b->delay_ms(b->ctx, 1);
        }
        if (i == 30)
            return -ETIMEDOUT;
        uint16_t hi, lo;
        TRY(fdc_read(b, 0, &hi));
        TRY(fdc_read(b, 1, &lo));
        uint32_t u = ((uint32_t)hi << 8) | (lo >> 8);
        int32_t raw = u & 0x800000 ? (int32_t)u - 0x1000000 : (int32_t)u;
        /* Keep 2 pF margin from the +/-15 pF specified measurement limits. */
        int32_t residual = (int64_t)raw * 1000 / 524288;
        if (residual > 13000)
            continue;
        if (residual < -13000)
            return -ERANGE;
        *ff = residual + (int32_t)d * 3125;
        *dac = d;
        return 0;
    }
    return -ERANGE;
}
int carrier_measure(const struct carrier_bus *b, struct carrier_sample *s) {
    uint16_t id;
    TRY(fdc_read(b, 0xfe, &id));
    if (id != 0x5449)
        return -ENODEV;
    TRY(fdc_read(b, 0xff, &id));
    if (id != 0x1004)
        return -ENODEV;
    TRY(capacitance(b, 0, &s->capacitance_ff[0], &s->capdac[0]));
    TRY(capacitance(b, 1, &s->capacitance_ff[1], &s->capdac[1]));
    const uint8_t cmd = 0xfd;
    uint8_t r[6]; /* No heater command exists here. */
    TRY(b->transfer(b->ctx, 0x44, &cmd, 1, 0, 0));
    b->delay_ms(b->ctx, 10);
    TRY(b->transfer(b->ctx, 0x44, 0, 0, r, 6));
    if (carrier_crc(r, 2) != r[2] || carrier_crc(r + 3, 2) != r[5])
        return -EBADMSG;
    uint32_t t = ((uint16_t)r[0] << 8) | r[1], h = ((uint16_t)r[3] << 8) | r[4];
    s->temperature_cc = -4500 + (17500 * t) / 65535;
    int rh = -600 + (12500 * h) / 65535;
    s->humidity_cpct = rh < 0 ? 0 : rh > 10000 ? 10000 : rh;
    TRY(adc(b, 0, &s->battery_mv));
    if (s->battery_mv < 2200)
        return -ERANGE;
    return 0;
}
int carrier_stop(const struct carrier_bus *b) {
    /* Do not disarm recovery if I2C prevents safe shutdown. */
    TRY(checked(b, 0x69, 0));
    TRY(wait_pm(b, 0x6e, 3, 0));
    TRY(checked(b, 0x24, 0)); /* Auto, LP/ULP allowed while MCU sleeps. */
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    return 0;
}
