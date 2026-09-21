#include "../src/carrier.h"
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
struct fixture {
    uint8_t pm[256];
    uint16_t fdc[256];
    int calls, fail_at, delays;
    bool timeout, bad_crc, unsafe_mode, heater;
    int32_t input_ff[2];
    struct carrier_fault fault;
    unsigned now_ms, fdc_ready_ms, adc_busy_ms, off_delay_ms;
    unsigned watchdog_ms;
    bool stuck_on, watchdog_expired;
};
static int transfer(void *ctx, uint8_t addr, const uint8_t *w, size_t nw, uint8_t *r, size_t nr) {
    struct fixture *f = ctx;
    if (++f->calls == f->fail_at)
        return -EIO;
    if (addr == 0x74) {
        assert(nw >= 1);
        if (nr) {
            assert(nr == 1);
            *r = f->pm[w[0]];
            return 0;
        }
        for (size_t i = 1; i < nw; i++)
            f->pm[w[0] + i - 1] = w[i];
        if (w[0] == 0xb1) {
            f->pm[0xb7] = 0;
            f->watchdog_ms = 0;
        }
        if (w[0] == 0xb0) {
            f->pm[0xb7] = 1;
            unsigned ticks = (f->pm[0xb4] << 16) | (f->pm[0xb5] << 8) | f->pm[0xb6];
            f->watchdog_ms = ((ticks + 1) * 1000) / 64;
        }
        if (w[0] == 0xb2 && f->pm[0xb7])
            f->watchdog_ms = 20000;
        if (w[0] == 0x06)
            f->pm[1] &= ~w[1];
        if (w[0] == 0x90) {
            assert(!(f->pm[0x9d] & 3)); /* A busy ADC ignores a new trigger. */
            if (!f->timeout)
                f->pm[1] |= f->pm[0x91] == 4 ? 8 : 1;
        }
        if (w[0] == 0x69) {
            if (w[1])
                f->pm[0x6e] = 6;
            else if (!f->off_delay_ms && !f->stuck_on)
                f->pm[0x6e] &= ~0x0c; /* SW may remain set while disabled. */
        }
        return 0;
    }
    if (addr == 0x50) {
        assert(f->pm[0x69] == 1 && f->pm[0x24] == 1);
        if (nr) {
            assert(nw == 1 && nr == 2);
            if (*w == 12 && !f->timeout && f->now_ms >= f->fdc_ready_ms)
                f->fdc[12] |= 8;
            r[0] = f->fdc[*w] >> 8;
            r[1] = f->fdc[*w];
            return 0;
        }
        assert(nw == 3);
        uint16_t v = (w[1] << 8) | w[2];
        f->fdc[w[0]] = v;
        if (w[0] == 8 || w[0] == 9)
            f->unsafe_mode |= ((v >> 10) & 7) != 4;
        if (w[0] == 12 && (v & 0x80)) {
            int ch = f->fdc[8] >> 13;
            int dac = (f->fdc[8] >> 5) & 31;
            int64_t val = (int64_t)(f->input_ff[ch] - dac * 3125) * 524288 / 1000;
            if (val > 8388607)
                val = 8388607;
            if (val < -8388608)
                val = -8388608;
            uint32_t raw = (uint32_t)val & 0xffffff;
            f->fdc[0] = raw >> 8;
            f->fdc[1] = (raw & 255) << 8;
            f->fdc_ready_ms = f->now_ms + 10; /* 100 samples/s, not instantaneous. */
        }
        return 0;
    }
    assert(addr == 0x44);
    if (nw) {
        assert(nw == 1);
        f->heater |= *w != 0xfd;
        return 0;
    }
    assert(nr == 6);
    r[0] = 0x66;
    r[1] = 0x66;
    r[2] = carrier_crc(r, 2);
    r[3] = 0x80;
    r[4] = 0;
    r[5] = carrier_crc(r + 3, 2);
    if (f->bad_crc)
        r[5] ^= 1;
    return 0;
}
static void delay(void *ctx, unsigned ms) {
    struct fixture *f = ctx;
    f->delays += ms;
    f->now_ms += ms;
    if (f->adc_busy_ms) {
        if (ms >= f->adc_busy_ms)
            f->pm[0x9d] &= ~3;
        f->adc_busy_ms = ms >= f->adc_busy_ms ? 0 : f->adc_busy_ms - ms;
    }
    if (!f->pm[0x69] && !f->stuck_on && f->off_delay_ms) {
        if (ms >= f->off_delay_ms)
            f->pm[0x6e] &= ~0x0c;
        f->off_delay_ms = ms >= f->off_delay_ms ? 0 : f->off_delay_ms - ms;
    }
    if (f->pm[0xb7]) {
        if (ms >= f->watchdog_ms) {
            f->watchdog_expired = true;
            f->watchdog_ms = 0;
        } else {
            f->watchdog_ms -= ms;
        }
    }
}
static void init(struct fixture *f) {
    memset(f, 0, sizeof(*f));
    f->pm[0x96] = 240;
    f->pm[0x99] = 255;
    f->fdc[0xfe] = 0x5449;
    f->fdc[0xff] = 0x1004;
    f->input_ff[0] = 52000;
    f->input_ff[1] = 9000;
}
int main(void) {
    struct fixture f;
    struct carrier_sample s;
    struct carrier_bus b = {&f, transfer, delay, &f.fault};
    uint8_t check[] = {0xbe, 0xef};
    assert(carrier_crc(check, 2) == 0x92);
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    assert(s.battery_mv == 3000 && s.output_mv >= 3290);
    assert(f.pm[0x22] == 30 && f.pm[0x23] == 1 && f.pm[0x24] == 1);
    assert(f.pm[0x6f] == 0x14 && f.pm[0x6c] == 1 && f.pm[0xb3] == 2);
    assert(carrier_measure(&b, &s) == 0);
    assert(s.temperature_cc == 2500 && s.humidity_cpct == 5650);
    assert(s.capacitance_ff[0] >= 51998 && s.capacitance_ff[0] <= 52001);
    assert(s.capacitance_ff[1] >= 8998 && s.capacitance_ff[1] <= 9001);
    assert(!f.unsafe_mode && !f.heater);
    assert(carrier_stop(&b) == 0 && !f.pm[0x69] && !f.pm[0xb7] && !f.pm[0x24]);
    int total = f.calls;
    /* A single transient bus failure at every transaction must remain recoverable. */
    for (int i = 1; i <= total; i++) {
        init(&f);
        f.fail_at = i;
        int rc = carrier_start(&b, &s);
        if (!rc)
            rc = carrier_measure(&b, &s);
        int stop = carrier_stop(&b);
        if (stop) {
            f.fail_at = 0;
            assert(carrier_stop(&b) == 0);
        }
        assert(!f.pm[0x69] && !f.unsafe_mode && !f.heater);
    }
    init(&f);
    f.pm[0x96] = 150;
    assert(carrier_start(&b, &s) == -ERANGE);
    assert(!f.pm[0x69]);
    assert(carrier_stop(&b) == 0);
    init(&f);
    f.timeout = true;
    assert(carrier_start(&b, &s) == -ETIMEDOUT);
    assert(f.fault.address == 0x74 && f.fault.reg == 0x01 && f.fault.mask == 1);
    assert(f.delays < 200);
    assert(carrier_stop(&b) == 0);
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    f.timeout = true;
    assert(carrier_measure(&b, &s) == -ETIMEDOUT);
    assert(f.fault.address == 0x50 && f.fault.reg == 0x0c && f.fault.observed == 0x480);
    assert(f.delays < 500);
    assert(carrier_stop(&b) == 0);
    assert(f.fault.address == 0x50); /* Cleanup must retain the failing chip/register. */
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    f.bad_crc = true;
    assert(carrier_measure(&b, &s) == -EBADMSG);
    assert(carrier_stop(&b) == 0);
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    f.input_ff[0] = 130000;
    assert(carrier_measure(&b, &s) == -ERANGE);
    assert(carrier_stop(&b) == 0);
    init(&f);
    f.pm[0x34] = 1; /* PMIC reports LP despite accepted force-HP setting. */
    assert(carrier_start(&b, &s) == -ETIMEDOUT);
    assert(f.fault.reg == 0x34 && f.fault.observed == 1 && f.fault.expected == 0);
    assert(!f.pm[0x69]);
    assert(carrier_stop(&b) == 0);
    init(&f);
    f.pm[0x9d] = 2;
    f.adc_busy_ms = 7; /* Conversion survived an MCU reset. */
    assert(carrier_start(&b, &s) == 0);
    assert(carrier_stop(&b) == 0);
    init(&f);
    f.pm[0x9d] = 2; /* ADC never becomes available. */
    assert(carrier_start(&b, &s) == -ETIMEDOUT);
    assert(f.fault.reg == 0x9d && !f.pm[0x90]);
    assert(carrier_stop(&b) == 0);
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    f.off_delay_ms = 7;
    unsigned before = f.now_ms;
    assert(carrier_sensors_off(&b) == 0);
    assert(f.now_ms >= before + 7 && f.pm[0x6e] == 2);
    assert(f.pm[0xb7] && f.pm[0x24]);
    /* A five-minute BLE window must not trip the independent 20 s watchdog. */
    for (unsigned i = 0; i < 300; i++) {
        assert(carrier_watchdog_feed(&b) == 0);
        delay(&f, 1000);
        assert(!f.pm[0x69] && !f.watchdog_expired);
    }
    assert(carrier_stop(&b) == 0);
    delay(&f, 60000);
    assert(!f.watchdog_expired);
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    assert(carrier_sensors_off(&b) == 0);
    delay(&f, 20000); /* A stalled foreground must still power-cycle. */
    assert(f.watchdog_expired);
    init(&f);
    assert(carrier_start(&b, &s) == 0);
    f.stuck_on = true;
    assert(carrier_stop(&b) == -ETIMEDOUT);
    assert(f.fault.reg == 0x6e && f.pm[0xb7] && f.pm[0x24]);
    f.stuck_on = false;
    assert(carrier_stop(&b) == 0);
    init(&f);
    f.fail_at = 1;
    assert(carrier_watchdog_feed(&b) == -EIO);
    assert(f.fault.address == 0x74 && f.fault.reg == 0xb2 && f.fault.mask == 0);
    puts("carrier: measurements, CRC, range, bounded waits and bus-fault cleanup passed");
}
