/* Board power gate, before MCUboot performs image hashing, RSA, or swapping.
 * This does not bypass image verification or change the trusted signing key. */
#include "carrier.h"
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/timer/nrf_grtc_timer.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/poweroff.h>

static int transfer(void *ctx, uint8_t address, const uint8_t *w, size_t nw,
                    uint8_t *r, size_t nr)
{
    const struct device *dev = ctx;
    if (nw && nr)
        return i2c_write_read(dev, address, w, nw, r, nr);
    if (nw)
        return i2c_write(dev, w, nw, address);
    return i2c_read(dev, r, nr, address);
}

static void delay(void *ctx, unsigned ms)
{
    ARG_UNUSED(ctx);
    k_msleep(ms);
}

static int guard(void)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(i2c22));
    struct carrier_fault fault = {0};
    struct carrier_bus bus = {(void *)dev, transfer, delay, &fault};
    uint16_t mv = 0;
    uint8_t retained = 0, stage = 0, pmic = 0;
    uint32_t cause = 0;
    (void)hwinfo_get_reset_cause(&cause); /* Application still needs these flags. */
    int rc = device_is_ready(dev) ?
        carrier_retained_read(&bus, &retained, &stage, &pmic) : -ENODEV;
    if (!rc)
        rc = carrier_power_probe(&bus, &mv);
    bool planned = (cause & RESET_SOFTWARE) && mv >= CARRIER_RECOVER_BATTERY_MV;
    /* An explicit software reset at a healthy supply is also used by SWD
     * bootloader updates. Watchdog/power-cycle resets must still back off. */
    bool interrupted = !planned && (retained == CARRIER_POWER_BOOTING ||
                                    retained == CARRIER_POWER_ATTEMPT);
    if (!rc && !interrupted && carrier_power_allowed(mv, retained)) {
        rc = carrier_retained_state(&bus, CARRIER_POWER_BOOTING);
        if (!rc)
            rc = carrier_watchdog_start(&bus, 60);
        if (!rc)
            return 0;
    }
    if (device_is_ready(dev)) {
        uint8_t reason = cause & RESET_WATCHDOG ? 0xe1 :
                         ((pmic >> 1) & 15) == 5 ? 0xe2 :
                         interrupted ? 0xe3 : 0xd0;
        (void)carrier_retained_stage(&bus, reason);
        (void)carrier_hibernate(&bus, CONFIG_SENSOR_BOOT_RETRY_SECONDS);
        k_msleep(20);
        (void)carrier_stop(&bus);
    }
    /* If PMIC communication is unavailable, remove the MCU load anyway.
     * After GRTC preparation, use no I2C, logging, or kernel timeouts. */
    (void)z_nrf_grtc_wakeup_prepare((uint64_t)CONFIG_SENSOR_BOOT_RETRY_SECONDS *
                                  USEC_PER_SEC);
    sys_poweroff();
    return 0;
}

SYS_INIT(guard, APPLICATION, 0);
