/* Real board qualification image. One cold boot per cycle. */
#include "carrier.h"
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/timer/nrf_grtc_timer.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/kernel.h>
#include <zephyr/pm/device.h>
#include <zephyr/pm/device_runtime.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/sys/reboot.h>

struct carrier_devices {
    const struct device *main;
    const struct device *fdc;
};

/* Runtime PM applies the no-pull, disconnected sleep pinctrl state. */
static int fdc_bus_is_asleep(const struct device *dev) {
    enum pm_device_state state;
    int rc = pm_device_state_get(dev, &state);
    if (rc)
        return rc;
    return pm_device_runtime_is_enabled(dev) && state == PM_DEVICE_STATE_SUSPENDED ? 0 : -EBUSY;
}

static int transfer(void *ctx, uint8_t address, const uint8_t *w, size_t nw, uint8_t *r,
                    size_t nr) {
    const struct carrier_devices *devices = ctx;
    const struct device *dev = address == 0x50 ? devices->fdc : devices->main;
    if (nw && nr)
        return i2c_write_read(dev, address, w, nw, r, nr);
    if (nw)
        return i2c_write(dev, w, nw, address);
    return i2c_read(dev, r, nr, address);
}
static void delay(void *ctx, unsigned ms) {
    (void)ctx;
    k_msleep(ms);
}
static char hex_digit(uint8_t v) {
    return v < 10 ? (char)('0' + v) : (char)('A' + v - 10);
}
#if CONFIG_SENSOR_MOISTURE_CALIBRATED
static uint16_t moisture_from_cap(int32_t cap_ff, int32_t dry_ff, int32_t wet_ff) {
    const int32_t span = wet_ff - dry_ff;
    int32_t value;
    if (!span)
        return 0;
    value = (int32_t)(((int64_t)(cap_ff - dry_ff) * 10000) / span);
    if (value < 0)
        value = 0;
    if (value > 10000)
        value = 10000;
    return (uint16_t)value;
}
#endif
static int arm_watchdog(void) {
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(wdt31));
    struct wdt_timeout_cfg cfg = {.window = {0, 15000}, .flags = WDT_FLAG_RESET_SOC};
    if (!device_is_ready(dev))
        return -ENODEV;
    int rc = wdt_install_timeout(dev, &cfg);
    if (rc < 0)
        return rc;
    return wdt_setup(dev, WDT_OPT_PAUSE_HALTED_BY_DBG);
}
static int radio_window(const struct carrier_sample *sample) {
    uint8_t id[16];
    bt_addr_le_t addr = {.type = BT_ADDR_LE_RANDOM};
    ssize_t n = hwinfo_get_device_id(id, sizeof(id));
    if (n < 6)
        return -EIO;
    for (ssize_t i = 0; i < n; i++)
        addr.a.val[i % 6] ^= id[i];
    addr.a.val[5] |= 0xc0;
    int rc = bt_id_create(&addr, NULL);
    if (rc < 0)
        return rc;
    rc = bt_enable(NULL);
    if (rc)
        return rc;
    char name[] = {
        'S', 'o', 'i', 'l', '-',
        hex_digit(addr.a.val[1] >> 4), hex_digit(addr.a.val[1] & 0x0f),
        hex_digit(addr.a.val[0] >> 4), hex_digit(addr.a.val[0] & 0x0f),
    };
    /* BTHome v2 service data: UUID FCD2, unencrypted/regular packet, then
     * temperature (0.01 C), humidity (0.01 %), voltage (0.001 V), and either
     * calibrated moisture or the two raw capacitance values. */
#if CONFIG_SENSOR_MOISTURE_CALIBRATED
    uint16_t m1 = moisture_from_cap(sample->capacitance_ff[0], CONFIG_SENSOR_SENSE1_DRY_FF,
                                    CONFIG_SENSOR_SENSE1_WET_FF);
    uint16_t m2 = moisture_from_cap(sample->capacitance_ff[1], CONFIG_SENSOR_SENSE2_DRY_FF,
                                    CONFIG_SENSOR_SENSE2_WET_FF);
#endif
#if CONFIG_SENSOR_MOISTURE_CALIBRATED
    uint8_t bthome[] = {
        0xd2, 0xfc, 0x40,
        0x02, (uint8_t)sample->temperature_cc, (uint8_t)(sample->temperature_cc >> 8),
        0x03, (uint8_t)sample->humidity_cpct, (uint8_t)(sample->humidity_cpct >> 8),
        0x0c, (uint8_t)sample->battery_mv, (uint8_t)(sample->battery_mv >> 8),
        0x14, (uint8_t)m1, (uint8_t)(m1 >> 8),
        0x14, (uint8_t)m2, (uint8_t)(m2 >> 8),
    };
#else
    uint32_t c1 = (uint32_t)sample->capacitance_ff[0];
    uint32_t c2 = (uint32_t)sample->capacitance_ff[1];
    uint8_t bthome[] = {
        0xd2, 0xfc, 0x40,
        0x02, (uint8_t)sample->temperature_cc, (uint8_t)(sample->temperature_cc >> 8),
        0x03, (uint8_t)sample->humidity_cpct, (uint8_t)(sample->humidity_cpct >> 8),
        0x0c, (uint8_t)sample->battery_mv, (uint8_t)(sample->battery_mv >> 8),
        0x54, 4, (uint8_t)c1, (uint8_t)(c1 >> 8), (uint8_t)(c1 >> 16), (uint8_t)(c1 >> 24),
        0x54, 4, (uint8_t)c2, (uint8_t)(c2 >> 8), (uint8_t)(c2 >> 16), (uint8_t)(c2 >> 24),
    };
#endif
    const struct bt_data ad[] = {
        BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
        BT_DATA(0x16, bthome, sizeof bthome),
    };
    const struct bt_data sd[] = {
        BT_DATA(BT_DATA_NAME_COMPLETE, name, sizeof name),
    };
    rc = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_USE_IDENTITY | BT_LE_ADV_OPT_SCANNABLE,
                                         BT_GAP_ADV_FAST_INT_MIN_2, BT_GAP_ADV_FAST_INT_MAX_2,
                                         NULL),
                         ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (rc)
        return rc;
    k_msleep(CONFIG_SENSOR_ADV_WINDOW_MS);
    return bt_le_adv_stop();
}
int main(void) {
    struct carrier_devices devices = {
        .main = DEVICE_DT_GET(DT_NODELABEL(i2c22)),
        .fdc = DEVICE_DT_GET(DT_NODELABEL(i2c20)),
    };
    struct carrier_bus bus = {&devices, transfer, delay};
    struct carrier_sample sample = {0};
    int rc = arm_watchdog();
    if (!rc && (!device_is_ready(devices.main) || !device_is_ready(devices.fdc)))
        rc = -ENODEV;
    if (!rc)
        rc = fdc_bus_is_asleep(devices.fdc);
    if (rc) {
        sys_reboot(SYS_REBOOT_COLD);
    }
    /* Allow the nPM2100 state machine and VOUT rail to settle after a cold
     * battery application before the first control transaction. */
    k_msleep(250);
    for (int attempt = 0; attempt < 3; attempt++) {
        rc = carrier_start(&bus, &sample);
        if (rc != -ETIMEDOUT || attempt == 2)
            break;
        k_msleep(100);
    }
    if (!rc)
        rc = carrier_measure(&bus, &sample);
    if (!rc)
        rc = radio_window(&sample); /* Supply remains force-HP, including bt_enable(). */
    /* The PMIC remains accessible while the dedicated FDC pins are disconnected.
     * Do not switch the rail off unless the final transfer released those pins. */
    int stop = fdc_bus_is_asleep(devices.fdc);
    if (!stop)
        stop = carrier_stop(&bus);
    if (stop) {
        for (;;)
            k_sleep(K_FOREVER);
    }
    uint32_t cycle_seconds = CONFIG_SENSOR_CYCLE_SECONDS;
    if (sample.battery_mv && sample.battery_mv < CONFIG_SENSOR_LOW_BATTERY_MV)
        cycle_seconds = CONFIG_SENSOR_LOW_BATTERY_CYCLE_SECONDS;
    /* No kernel work after GRTC wake preparation. */
    k_msleep(20);
    if (z_nrf_grtc_wakeup_prepare((uint64_t)cycle_seconds * USEC_PER_SEC))
        sys_reboot(SYS_REBOOT_COLD);
    sys_poweroff();
    return 0;
}
