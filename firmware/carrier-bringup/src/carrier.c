#include "carrier.h"
#include <errno.h>
static int fault(const struct carrier_bus *b, int error, uint8_t address, uint8_t reg,
                 uint16_t observed, uint16_t mask, uint16_t expected) {
    if (b->fault && !b->fault->error)
        *b->fault = (struct carrier_fault){error, address, reg, observed, mask, expected};
    return error;
}

static int transfer(const struct carrier_bus *b, uint8_t address, const uint8_t *w,
                    size_t nw, uint8_t *r, size_t nr) {
    int rc = b->transfer(b->ctx, address, w, nw, r, nr);
    if (rc < 0)
        return fault(b, rc, address, nw ? w[0] : 0, 0, 0, 0);
    return rc;
}
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
    return transfer(b, 0x74, w, 2, 0, 0);
}
static int rd(const struct carrier_bus *b, uint8_t reg, uint8_t *value) {
    return transfer(b, 0x74, &reg, 1, value, 1);
}
static int checked(const struct carrier_bus *b, uint8_t reg, uint8_t value) {
    uint8_t v;
    TRY(wr(b, reg, value));
    TRY(rd(b, reg, &v));
    return v == value ? 0 : fault(b, -EIO, 0x74, reg, v, 0xff, value);
}
static int wait_pm(const struct carrier_bus *b, uint8_t reg, uint8_t mask, uint8_t value) {
    uint8_t v = 0;
    for (int i = 0; i < 30; i++) {
        TRY(rd(b, reg, &v));
        if ((v & mask) == value)
            return 0;
        b->delay_ms(b->ctx, 1);
    }
    return fault(b, -ETIMEDOUT, 0x74, reg, v, mask, value);
}
static int adc(const struct carrier_bus *b, uint8_t mode, uint16_t *mv) {
    uint8_t v, bit = mode == 4 ? 8 : 1;
    /* nPM2100 DS 7.1: a new conversion may only start when ADC is ready. */
    TRY(wait_pm(b, 0x9d, 3, 0));
    TRY(wr(b, 0x06, bit)); /* Clear stale ADC ready event before triggering. */
    TRY(checked(b, 0x91, mode));
    TRY(wr(b, 0x90, 1));
    TRY(wait_pm(b, 0x01, bit, bit));
    TRY(rd(b, mode == 4 ? 0x99 : 0x96, &v));
    *mv = mode == 4 ? 1800 + (1500 * (unsigned)v) / 256 : (3200 * (unsigned)v) / 256;
    return 0;
}
int carrier_watchdog_start(const struct carrier_bus *b, uint32_t seconds) {
    if (!seconds || seconds > 262144)
        return -EINVAL;
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    TRY(checked(b, 0xd6, 1)); /* Also disable LDOSW on watchdog reset. */
    uint32_t ticks = seconds * 64 - 1;
    TRY(checked(b, 0xb4, ticks >> 16));
    TRY(checked(b, 0xb5, ticks >> 8));
    TRY(checked(b, 0xb6, ticks));
    TRY(checked(b, 0xb3, 2));
    return wr(b, 0xb0, 1);
}
int carrier_start(const struct carrier_bus *b, struct carrier_sample *s) {
    /* nPM2100 remains powered across MCU System OFF and watchdog resets. */
    TRY(carrier_sensors_off(b));
    TRY(carrier_watchdog_start(b, 20));
    TRY(adc(b, 0, &s->battery_mv));
    if (s->battery_mv < CARRIER_MIN_BATTERY_MV)
        return -ERANGE; /* Board input floor; no cell-capacity claim. */
    TRY(checked(b, 0x22, 30));
    TRY(checked(b, 0x23, 1)); /* 3.3 V */
    TRY(checked(b, 0x24, 1)); /* Force HP for sensor conversion accuracy. */
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
int carrier_ota_start(const struct carrier_bus *b) {
    /* OTA can last minutes: do not arm the 20-second PMIC watchdog or
     * enable the switched sensor rail. Keep only the radio supply on. */
    TRY(carrier_sensors_off(b));
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    TRY(checked(b, 0x22, 30));
    TRY(checked(b, 0x23, 1));
    TRY(checked(b, 0x24, 1));
    TRY(wait_pm(b, 0x34, 7, 0));
    return 0;
}
static int fdc_read(const struct carrier_bus *b, uint8_t reg, uint16_t *v) {
    uint8_t r[2];
    TRY(transfer(b, 0x50, &reg, 1, r, 2));
    *v = ((uint16_t)r[0] << 8) | r[1];
    return 0;
}
static int fdc_write(const struct carrier_bus *b, uint8_t reg, uint16_t v) {
    uint8_t w[] = {reg, v >> 8, v};
    return transfer(b, 0x50, w, 3, 0, 0);
}
static int capacitance(const struct carrier_bus *b, unsigned ch, int32_t *ff, uint8_t *dac) {
    /* Only single-ended CAPDAC mode: this PCB physically ties SHLD1 to SHLD2. */
    for (unsigned d = 0; d < 32; d++) {
        TRY(fdc_write(b, 8, (ch << 13) | (4 << 10) | (d << 5)));
        TRY(fdc_write(b, 12, 0x480)); /* One measurement, 100 sps, no repeat. */
        unsigned i;
        uint16_t status = 0;
        for (i = 0; i < 30; i++) {
            TRY(fdc_read(b, 12, &status));
            if (status & 8)
                break;
            b->delay_ms(b->ctx, 1);
        }
        if (i == 30)
            return fault(b, -ETIMEDOUT, 0x50, 12, status, 8, 8);
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
    TRY(transfer(b, 0x44, &cmd, 1, 0, 0));
    b->delay_ms(b->ctx, 10);
    TRY(transfer(b, 0x44, 0, 0, r, 6));
    if (carrier_crc(r, 2) != r[2] || carrier_crc(r + 3, 2) != r[5])
        return -EBADMSG;
    uint32_t t = ((uint16_t)r[0] << 8) | r[1], h = ((uint16_t)r[3] << 8) | r[4];
    s->temperature_cc = -4500 + (17500 * t) / 65535;
    int rh = -600 + (12500 * h) / 65535;
    s->humidity_cpct = rh < 0 ? 0 : rh > 10000 ? 10000 : rh;
    TRY(adc(b, 0, &s->battery_mv));
    if (s->battery_mv < CARRIER_MIN_BATTERY_MV)
        return -ERANGE;
    return 0;
}
int carrier_sensors_off(const struct carrier_bus *b) {
    TRY(checked(b, 0x69, 0));
    /* STATUS.LDO (bit 0) is already zero while the load switch is ON.
     * Wait for both operating modes (HP/ULP) to clear. The observed disabled
     * load-switch status may retain SW (0x02); it must not retain HP/ULP. */
    return wait_pm(b, 0x6e, 0x0c, 0);
}
int carrier_watchdog_feed(const struct carrier_bus *b) {
    return wr(b, 0xb2, 1); /* TIMER.TASKS_KICK, DS 7.2.6.3. */
}
int carrier_radio_start(const struct carrier_bus *b) {
    uint16_t output_mv;
    TRY(carrier_sensors_off(b));
    TRY(checked(b, 0x24, 0)); /* Auto: allow HP on demand, LP/ULP between events. */
    TRY(adc(b, 4, &output_mv));
    /* This detects gross rail loss, not ripple or short radio transients. */
    return output_mv < 3150 ? -ERANGE : 0;
}
int carrier_stop(const struct carrier_bus *b) {
    /* Do not disarm recovery if I2C prevents safe shutdown. */
    TRY(carrier_sensors_off(b));
    TRY(checked(b, 0x24, 0)); /* Auto, LP/ULP allowed while MCU sleeps. */
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    return 0;
}

int carrier_retained_read(const struct carrier_bus *b, uint8_t *state, uint8_t *stage,
                          uint8_t *reset) {
    TRY(rd(b, 0xd9, state));
    TRY(rd(b, 0xda, stage));
    return rd(b, 0xd5, reset);
}
int carrier_retained_state(const struct carrier_bus *b, uint8_t state) {
    uint8_t observed;
    TRY(wr(b, 0xd7, state));
    TRY(wr(b, 0xd8, 1));
    TRY(rd(b, 0xd9, &observed));
    return observed == state ? 0 : fault(b, -EIO, 0x74, 0xd9, observed, 255, state);
}
int carrier_retained_stage(const struct carrier_bus *b, uint8_t stage) {
    return checked(b, 0xda, stage);
}
int carrier_power_probe(const struct carrier_bus *b, uint16_t *battery_mv) {
    /* Run before settings, MCU watchdog, forced HP, sensors, or Bluetooth.
     * Stop an inherited PMIC boot/watchdog timer before attempting recovery. */
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    TRY(carrier_sensors_off(b));
    TRY(checked(b, 0x24, 0));
    return adc(b, 0, battery_mv);
}
int carrier_hibernate(const struct carrier_bus *b, uint32_t seconds) {
    if (seconds < 1 || seconds > 262144)
        return -EINVAL;
    /* SCRATCHA is in the VBAT domain: survives MCU and PMIC power-cycle resets.
     * No flash writes at low voltage. Hibernate keeps BOOST alive in ULP and
     * removes VOUT; Hibernate_PT is unsuitable for a depleted input. */
    TRY(carrier_retained_state(b, CARRIER_POWER_BLOCKED));
    TRY(carrier_sensors_off(b));
    TRY(checked(b, 0x24, 0));
    TRY(wr(b, 0xb1, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 0));
    uint32_t ticks = seconds * 64 - 1;
    TRY(checked(b, 0xb4, ticks >> 16));
    TRY(checked(b, 0xb5, ticks >> 8));
    TRY(checked(b, 0xb6, ticks));
    TRY(checked(b, 0xb3, 3));
    TRY(wr(b, 0xb0, 1));
    TRY(wait_pm(b, 0xb7, 0xff, 1));
    return wr(b, 0xc8, 1);
}
bool carrier_power_allowed(uint16_t mv, uint8_t retained) {
    return mv >= (retained == CARRIER_POWER_BLOCKED ? CARRIER_RECOVER_BATTERY_MV :
                                                        CARRIER_MIN_BATTERY_MV);
}

int carrier_battery_read(const struct carrier_bus *b, uint16_t *mv) {
    return adc(b, 0, mv);
}
