/* Real battery-powered sensor image. One cold boot per cycle. */
#include "carrier.h"
#include "bthome.h"
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/mgmt/mcumgr/transport/smp_bt.h>
#include <zephyr/dfu/mcuboot.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/timer/nrf_grtc_timer.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/kernel.h>
#include <zephyr/pm/device.h>
#include <zephyr/pm/device_runtime.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/sys/reboot.h>

struct sensor_boot_trace {
    uint32_t magic;
    uint32_t boots;
    uint32_t stage;
    int32_t error;
    uint32_t last_failure_stage;
    int32_t last_failure_error;
    struct carrier_fault fault;
    struct carrier_sample sample;
    uint32_t wake_seconds;
};

static struct sensor_boot_trace sensor_trace __attribute__((section(".noinit")));
static struct carrier_fault cycle_fault;

static void trace_boot(void)
{
    /* A new layout/magic must never interpret old or power-on SRAM as errors. */
    if (sensor_trace.magic != 0x53454e54u)
        sensor_trace = (struct sensor_boot_trace){.magic = 0x53454e54u};
    sensor_trace.boots++;
}

static void trace_stage(uint32_t stage, int error)
{
    sensor_trace.stage = stage;
    sensor_trace.error = error;
}

static void trace_failure(uint32_t stage, int error)
{
    trace_stage(stage, error);
    sensor_trace.last_failure_stage = stage;
    sensor_trace.last_failure_error = error;
    sensor_trace.fault = cycle_fault;
    printk("sensor failure stage=%u error=%d addr=0x%02x reg=0x%02x "
           "observed=0x%04x mask=0x%04x expected=0x%04x\n",
           (unsigned)stage, error, cycle_fault.address, cycle_fault.reg,
           cycle_fault.observed, cycle_fault.mask, cycle_fault.expected);
}

static uint16_t diagnostic_error(void)
{
    int64_t error = sensor_trace.last_failure_error;

    if (error < 0)
        error = -error;
    return error > UINT16_MAX ? UINT16_MAX : (uint16_t)error;
}

static atomic_t sensor_ble_connected;
static K_SEM_DEFINE(sensor_ble_session_done, 0, 1);

#if !CONFIG_SENSOR_OTA
static const struct device *sensor_wdt;

static void sensor_ble_connected_cb(struct bt_conn *conn, uint8_t err)
{
    ARG_UNUSED(conn);
    if (!err) {
        atomic_set(&sensor_ble_connected, 1);
        printk("BLE connection accepted; SMP OTA is available\n");
    }
}

static void sensor_ble_disconnected_cb(struct bt_conn *conn, uint8_t reason)
{
    ARG_UNUSED(conn);
    ARG_UNUSED(reason);
    atomic_set(&sensor_ble_connected, 0);
    k_sem_give(&sensor_ble_session_done);
}

BT_CONN_CB_DEFINE(sensor_ble_conn_callbacks) = {
    .connected = sensor_ble_connected_cb,
    .disconnected = sensor_ble_disconnected_cb,
};
#endif

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
static uint8_t battery_percent(uint16_t millivolts) {
    /* Provisional voltage-only estimate for the CR2032 prototype. */
    if (millivolts <= 2200)
        return 0;
    if (millivolts >= 3000)
        return 100;
    return (uint8_t)(((uint32_t)(millivolts - 2200) * 100U) / 800U);
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
#if !CONFIG_SENSOR_OTA
static int arm_watchdog(void) {
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(wdt31));
    struct wdt_timeout_cfg cfg = {.window = {0, 15000}, .flags = WDT_FLAG_RESET_SOC};
    if (!device_is_ready(dev))
        return -ENODEV;
    int rc = wdt_install_timeout(dev, &cfg);
    if (rc < 0)
        return rc;
    rc = wdt_setup(dev, WDT_OPT_PAUSE_HALTED_BY_DBG);
    if (!rc)
        sensor_wdt = dev;
    return rc;
}

static void feed_watchdog(void)
{
    if (sensor_wdt)
        (void)wdt_feed(sensor_wdt, 0);
}
#else
static void feed_watchdog(void) { }
#endif
static int radio_window(const struct carrier_bus *bus, const struct carrier_sample *sample) {
    trace_stage(70, 0);
    uint8_t id[16];
    bt_addr_le_t addr = {.type = BT_ADDR_LE_RANDOM};
    ssize_t n = hwinfo_get_device_id(id, sizeof(id));
    if (n < 6) {
        trace_failure(71, -EIO);
        return -EIO;
    }
    for (ssize_t i = 0; i < n; i++)
        addr.a.val[i % 6] ^= id[i];
    addr.a.val[5] |= 0xc0;
    int rc = bt_id_create(&addr, NULL);
    if (rc < 0) {
        trace_failure(72, rc);
        return rc;
    }
    rc = bt_enable(NULL);
    if (rc) {
        trace_failure(73, rc);
        return rc;
    }
    char name[] = {
        'S', 'o', 'i', 'l', '-',
        hex_digit(addr.a.val[1] >> 4), hex_digit(addr.a.val[1] & 0x0f),
        hex_digit(addr.a.val[0] >> 4), hex_digit(addr.a.val[0] & 0x0f),
    };
    /* BTHome v2 service data uses UUID FCD2, standard object IDs, and the
     * calibrated moisture values configured below. */
    uint8_t bthome[BOARD_BTHOME_PAYLOAD_LEN];
    int payload_len;
    if (sample) {
#if CONFIG_SENSOR_MOISTURE_CALIBRATED
        uint16_t m1 = moisture_from_cap(sample->capacitance_ff[0], CONFIG_SENSOR_SENSE1_DRY_FF,
                                       CONFIG_SENSOR_SENSE1_WET_FF);
        uint16_t m2 = moisture_from_cap(sample->capacitance_ff[1], CONFIG_SENSOR_SENSE2_DRY_FF,
                                       CONFIG_SENSOR_SENSE2_WET_FF);
        struct board_bthome_values values = {
            .temperature_cc = sample->temperature_cc,
            .humidity_cpct = sample->humidity_cpct,
            .battery_pct = battery_percent(sample->battery_mv),
            .battery_mv = sample->battery_mv,
            .moisture1_cpct = m1,
            .moisture2_cpct = m2,
            .diagnostic_stage = sensor_trace.last_failure_stage,
            .diagnostic_error = diagnostic_error(),
        };
        payload_len = board_bthome_encode(&values, bthome, sizeof bthome);
#else
        trace_failure(79, -ENOTSUP);
        return -ENOTSUP;
#endif
    } else {
        payload_len = board_bthome_encode_diagnostic(sensor_trace.last_failure_stage,
                                                    diagnostic_error(), bthome,
                                                    sizeof bthome);
    }
    if (payload_len < 0) {
        trace_failure(74, -EINVAL);
        return -EINVAL;
    }
    const struct bt_data ad[] = {
        BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
        BT_DATA(0x16, bthome, payload_len),
    };
    const struct bt_data sd[] = {
        BT_DATA(BT_DATA_NAME_COMPLETE, name, sizeof name),
        /* SMP is in scan response; BTHome remains in the primary packet. */
        BT_DATA_BYTES(BT_DATA_UUID128_ALL, SMP_BT_SVC_UUID_VAL),
    };
    rc = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_USE_IDENTITY |
                                         BT_LE_ADV_OPT_SCANNABLE |
                                         BT_LE_ADV_OPT_CONN,
                                         BT_GAP_ADV_FAST_INT_MIN_2, BT_GAP_ADV_FAST_INT_MAX_2,
                                         NULL),
                         ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (rc) {
        trace_failure(75, rc);
        return rc;
    }
    trace_stage(76, sample ? sample->battery_mv : 0);
    int64_t deadline = k_uptime_get() + CONFIG_SENSOR_ADV_WINDOW_MS;
    int64_t next_feed = 0;
    while (atomic_get(&sensor_ble_connected) || k_uptime_get() < deadline) {
        if (k_uptime_get() >= next_feed) {
            /* The PMIC is independent of the MCU watchdog. A healthy OTA
             * session can outlast both timeouts, so service both here. Never
             * feed from an interrupt or during a stalled measurement. */
            rc = carrier_watchdog_feed(bus);
            if (rc) {
                trace_failure(78, rc);
                (void)bt_le_adv_stop();
                return rc;
            }
            feed_watchdog();
            next_feed = k_uptime_get() + 1000;
        }
        if (k_sem_take(&sensor_ble_session_done, K_MSEC(50)) == 0)
            break;
    }
    feed_watchdog();
    rc = bt_le_adv_stop();
    if (rc != -EALREADY && rc)
        trace_failure(77, rc);
    else
        trace_stage(77, 0);
    return rc == -EALREADY ? 0 : rc;
}

#if CONFIG_SENSOR_OTA
static const struct bt_data ota_ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, SMP_BT_SVC_UUID_VAL),
};
static const struct bt_data ota_sd[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
            sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};
static void ota_advertise(void) {
    int rc = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1, ota_ad, ARRAY_SIZE(ota_ad),
                             ota_sd, ARRAY_SIZE(ota_sd));
    if (rc)
        printk("OTA advertising failed (%d)\n", rc);
    else
        printk("OTA ready: connect over BLE using MCUmgr/SMP\n");
}
static void ota_disconnected(struct bt_conn *conn, uint8_t reason) {
    ARG_UNUSED(conn);
    printk("OTA disconnected (reason 0x%02x)\n", reason);
    ota_advertise();
}
BT_CONN_CB_DEFINE(sensor_ota_conn_callbacks) = {
    .disconnected = ota_disconnected,
};
static int ota_identity(void) {
    uint8_t id[16];
    bt_addr_le_t addr = {.type = BT_ADDR_LE_RANDOM};
    ssize_t n = hwinfo_get_device_id(id, sizeof(id));
    if (n < 6)
        return -EIO;
    for (ssize_t i = 0; i < n; i++)
        addr.a.val[i % 6] ^= id[i];
    addr.a.val[5] |= 0xc0;
    return bt_id_create(&addr, NULL) < 0 ? -EIO : 0;
}
static int ota_run(const struct carrier_bus *bus) {
    int rc = carrier_ota_start(bus);
    if (rc)
        return rc;
    rc = ota_identity();
    if (rc)
        return rc;
    rc = bt_enable(NULL);
    if (rc)
        return rc;
    rc = boot_write_img_confirmed();
    if (rc)
        return rc;
    ota_advertise();
    printk("OTA maintenance active\n");
    k_sleep(K_FOREVER);
    return 0;
}
#endif
int main(void) {
    trace_boot();
    trace_stage(1, 0);
    struct carrier_devices devices = {
        .main = DEVICE_DT_GET(DT_NODELABEL(i2c22)),
        .fdc = DEVICE_DT_GET(DT_NODELABEL(i2c20)),
    };
    struct carrier_bus bus = {&devices, transfer, delay, &cycle_fault};
    struct carrier_sample sample = {0};
    int rc = 0;
#if !CONFIG_SENSOR_OTA
    /* Watchdog protection is useful, but it must not prevent the radio
     * recovery path from starting on silicon/boot states where wdt31 is not
     * ready. The PMIC and MCUboot rollback paths remain authoritative. */
    (void)arm_watchdog();
    trace_stage(2, 0);
#endif
    if (!rc && (!device_is_ready(devices.main) || !device_is_ready(devices.fdc)))
        rc = -ENODEV;
    trace_stage(3, rc);
    if (!rc)
        rc = fdc_bus_is_asleep(devices.fdc);
    if (rc) {
        trace_failure(3, rc);
        sys_reboot(SYS_REBOOT_COLD);
    }
#if CONFIG_SENSOR_OTA
    rc = ota_run(&bus);
    if (rc)
        sys_reboot(SYS_REBOOT_COLD);
    return 0;
#endif
    trace_stage(40, 0);
    rc = carrier_start(&bus, &sample);
    bool power_ready = rc == 0;
    trace_stage(50, rc);
    if (rc)
        trace_failure(50, rc);
    if (!rc) {
        trace_stage(60, 0);
        rc = carrier_measure(&bus, &sample);
        if (rc)
            trace_failure(61, rc);
    }
    sensor_trace.sample = sample;
    /* The PMIC remains accessible while the dedicated FDC pins are disconnected.
     * Release the sensor supply before radio/OTA, which may last minutes. */
    int stop = fdc_bus_is_asleep(devices.fdc);
    if (!stop)
        stop = carrier_sensors_off(&bus);
    if (stop) {
        trace_failure(80, stop);
        sys_reboot(SYS_REBOOT_COLD);
    }
    bool low_battery = sample.battery_mv < CARRIER_MIN_BATTERY_MV && rc == -ERANGE;
    if (power_ready && !low_battery) {
        int radio = radio_window(&bus, rc ? NULL : &sample);
        if (!rc)
            rc = radio;
    }
    stop = carrier_stop(&bus);
    if (stop) {
        trace_failure(80, stop);
        sys_reboot(SYS_REBOOT_COLD);
    }
    /* A depleted battery or a failed sample must not cause an immediate
     * measurement/radio/reboot loop. Preserve the error and retry next wake. */
    uint32_t cycle_seconds = CONFIG_SENSOR_CYCLE_SECONDS;
    if (low_battery || (sample.battery_mv && sample.battery_mv < CONFIG_SENSOR_LOW_BATTERY_MV))
        cycle_seconds = CONFIG_SENSOR_LOW_BATTERY_CYCLE_SECONDS;
    sensor_trace.wake_seconds = cycle_seconds;
#if !CONFIG_SENSOR_OTA && defined(CONFIG_BOOTLOADER_MCUBOOT)
    /* Finish flash/MCUboot work while kernel timeouts still function. GRTC
     * wake preparation disables the kernel compare channels (SDK timer
     * driver); only the final poweroff may follow it. Failed samples must
     * remain unconfirmed for rollback on the next boot. */
    if (!rc && boot_write_img_confirmed()) {
        trace_failure(82, -EIO);
        printk("sensor image confirmation failed\n");
        sys_reboot(SYS_REBOOT_COLD);
    }
#endif
    k_msleep(20);
    int wake = z_nrf_grtc_wakeup_prepare((uint64_t)cycle_seconds * USEC_PER_SEC);
    if (wake) {
        trace_failure(81, wake);
        sys_reboot(SYS_REBOOT_COLD);
    }
    trace_stage(83, rc);
    sys_poweroff();
    return 0;
}
