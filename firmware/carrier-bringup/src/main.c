/* Real carrier qualification image. Raw capacitance over RTT, no invented
 * soil calibration or battery state-of-charge. One cold boot per cycle. */
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
#include <zephyr/sys/printk.h>
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
static int radio_window(void) {
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
    const struct bt_data ad[] = {
        BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
        BT_DATA(BT_DATA_NAME_COMPLETE, "ProbeQA", 7),
    };
    rc = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_USE_IDENTITY, BT_GAP_ADV_FAST_INT_MIN_2,
                                         BT_GAP_ADV_FAST_INT_MAX_2, NULL),
                         ad, ARRAY_SIZE(ad), NULL, 0);
    if (rc)
        return rc;
    k_msleep(2000);
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
        printk("Carrier initialization failed: %d\n", rc);
        sys_reboot(SYS_REBOOT_COLD);
    }
    rc = carrier_start(&bus, &sample);
    if (!rc)
        rc = carrier_measure(&bus, &sample);
    if (!rc) {
        printk("VBAT=%u mV VOUT=%u mV T=%d cC RH=%u c%% C1=%d fF C2=%d fF DAC=%u,%u\n",
               sample.battery_mv, sample.output_mv, sample.temperature_cc, sample.humidity_cpct,
               sample.capacitance_ff[0], sample.capacitance_ff[1], sample.capdac[0],
               sample.capdac[1]);
        rc = radio_window(); /* Supply remains force-HP, including bt_enable(). */
    }
    printk("Cycle result=%d; shutting down\n", rc);
    /* The PMIC remains accessible while the dedicated FDC pins are disconnected.
     * Do not switch the rail off unless the final transfer released those pins. */
    int stop = fdc_bus_is_asleep(devices.fdc);
    if (!stop)
        stop = carrier_stop(&bus);
    if (stop) {
        printk("Power shutdown failed=%d; waiting for watchdog recovery\n", stop);
        for (;;)
            k_sleep(K_FOREVER);
    }
    /* Qualification cadence. No kernel work after GRTC wake preparation. */
    k_msleep(20);
    if (z_nrf_grtc_wakeup_prepare(60ULL * USEC_PER_SEC))
        sys_reboot(SYS_REBOOT_COLD);
    sys_poweroff();
    return 0;
}
