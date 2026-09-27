#include "config_service.h"
#include <string.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/fs/zms.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/sys/byteorder.h>
#include <app_version.h>
#include <zephyr/dfu/mcuboot.h>

#define CONFIG_UUID(n) BT_UUID_128_ENCODE(0x6d6f6973, 0x7475, 0x7265, 0x8000, n)
static struct bt_uuid_128 service_uuid = BT_UUID_INIT_128(CONFIG_UUID(0x000000000001ULL));
static struct bt_uuid_128 config_uuid = BT_UUID_INIT_128(CONFIG_UUID(0x000000000002ULL));
static struct bt_uuid_128 status_uuid = BT_UUID_INIT_128(CONFIG_UUID(0x000000000003ULL));
static K_MUTEX_DEFINE(lock);
static K_SEM_DEFINE(wake, 0, 1);
static struct zms_fs storage;
static struct sensor_config current, pending;
static struct config_transaction transaction;
static struct sensor_sample last_sample;
static int storage_error, save_error, sample_error;
static uint32_t saves;
static uint8_t diagnostics[8];
void sensor_status_diagnostics(uint32_t reset, uint8_t pmic, uint8_t previous,
                               uint8_t stage, uint8_t error)
{
    sys_put_le32(reset, diagnostics);
    diagnostics[4] = pmic; diagnostics[5] = previous;
    diagnostics[6] = stage; diagnostics[7] = error;
}
static bool stored, save_pending, sample_pending, sample_valid;
static int64_t sampled_at, connected_at;
static uint16_t session_limit;
static uint8_t version_major = APP_VERSION_MAJOR, version_minor = APP_VERSION_MINOR;
static uint16_t version_patch = APP_PATCHLEVEL;
static struct bt_conn *connection;

int sensor_settings_init(void)
{
    struct mcuboot_img_header header;
    if (!boot_read_bank_header(FIXED_PARTITION_ID(slot0_partition), &header, sizeof(header)) &&
        header.mcuboot_version == 1) {
        version_major = header.h.v1.sem_ver.major;
        version_minor = header.h.v1.sem_ver.minor;
        version_patch = header.h.v1.sem_ver.revision;
    }
    current = (struct sensor_config){
        .cycle_s = CONFIG_SENSOR_CYCLE_SECONDS,
        .low_cycle_s = CONFIG_SENSOR_LOW_BATTERY_CYCLE_SECONDS,
        .window_ms = CONFIG_SENSOR_ADV_WINDOW_MS,
        .adv_ms = CONFIG_SENSOR_ADV_INTERVAL_MS,
        .session_s = CONFIG_SENSOR_SESSION_SECONDS,
        .low_mv = CONFIG_SENSOR_LOW_BATTERY_MV,
        .calibrated = IS_ENABLED(CONFIG_SENSOR_MOISTURE_CALIBRATED),
        .dry = {CONFIG_SENSOR_SENSE1_DRY_FF, CONFIG_SENSOR_SENSE2_DRY_FF},
        .wet = {CONFIG_SENSOR_SENSE1_WET_FF, CONFIG_SENSOR_SENSE2_WET_FF},
    };
    if (sensor_config_validate(&current)) return storage_error = -EINVAL;
    const struct flash_area *area;
    int rc = flash_area_open(FIXED_PARTITION_ID(zms_storage), &area);
    if (rc) return storage_error = rc;
    /* RRAM needs no erase; two 2 KB logical ZMS sectors fit the reserved 4 KB. */
    storage = (struct zms_fs){.flash_device = area->fa_dev, .offset = area->fa_off,
                              .sector_size = 2048, .sector_count = 2};
    if (area->fa_size != 4096 ||
        (flash_params_get_erase_cap(flash_get_parameters(area->fa_dev)) & FLASH_ERASE_C_EXPLICIT))
        rc = -ENOTSUP;
    else
        rc = zms_mount(&storage);
    flash_area_close(area);
    if (rc) return storage_error = rc;
    uint8_t wire[SENSOR_CONFIG_SIZE + 1];
    ssize_t n = zms_read(&storage, 1, wire, sizeof(wire));
    if (n == -ENOENT) return 0;
    if (n != SENSOR_CONFIG_SIZE || sensor_config_decode(&current, wire, n))
        return storage_error = n < 0 ? (int)n : -EBADMSG;
    stored = true;
    return 0;
}
void sensor_settings_get(struct sensor_config *out)
{
    k_mutex_lock(&lock, K_FOREVER);
    *out = current;
    k_mutex_unlock(&lock);
}
void sensor_settings_process(void)
{
    k_mutex_lock(&lock, K_FOREVER);
    if (save_pending) {
        uint8_t wire[SENSOR_CONFIG_SIZE];
        sensor_config_encode(&pending, wire);
        uint8_t previous[SENSOR_CONFIG_SIZE];
        sensor_config_encode(&current, previous);
        ssize_t n = stored && !memcmp(previous, wire, sizeof(wire)) ? 0 :
                    zms_write(&storage, 1, wire, sizeof(wire));
        /* Acknowledgement is durable only after a full CRC-checked readback. */
        uint8_t check[SENSOR_CONFIG_SIZE];
        save_error = n < 0 ? (int)n : 0;
        if (!save_error && (zms_read(&storage, 1, check, sizeof(check)) != sizeof(check) ||
                            memcmp(wire, check, sizeof(wire))))
            save_error = -EIO;
        if (!save_error) {
            current = pending;
            stored = true;
            saves++;
        }
        save_pending = false;
    }
    k_mutex_unlock(&lock);
}
void sensor_status_sample(const struct sensor_sample *s, int error)
{
    k_mutex_lock(&lock, K_FOREVER);
    if (s) last_sample = *s;
    sample_valid = s && !error;
    sample_error = error;
    sample_pending = false;
    sampled_at = k_uptime_get();
    k_mutex_unlock(&lock);
}
bool sensor_sample_requested(void)
{
    k_mutex_lock(&lock, K_FOREVER);
    bool requested = sample_pending;
    k_mutex_unlock(&lock);
    return requested;
}
static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) return;
    k_mutex_lock(&lock, K_FOREVER);
    connection = bt_conn_ref(conn);
    connected_at = k_uptime_get();
    session_limit = current.session_s;
    transaction = (struct config_transaction){0};
    k_mutex_unlock(&lock);
    k_sem_give(&wake);
}
static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    ARG_UNUSED(conn); ARG_UNUSED(reason);
    k_mutex_lock(&lock, K_FOREVER);
    if (connection) bt_conn_unref(connection);
    connection = NULL;
    transaction = (struct config_transaction){0};
    k_mutex_unlock(&lock);
    k_sem_give(&wake);
}
BT_CONN_CB_DEFINE(config_connections) = {.connected = connected, .disconnected = disconnected};
bool sensor_session_connected(void)
{
    k_mutex_lock(&lock, K_FOREVER);
    bool active = connection != NULL;
    k_mutex_unlock(&lock);
    return active;
}
bool sensor_session_expired(void)
{
    k_mutex_lock(&lock, K_FOREVER);
    bool expired = connection && k_uptime_get() - connected_at >= session_limit * 1000;
    k_mutex_unlock(&lock);
    return expired;
}
void sensor_session_disconnect(void)
{
    k_mutex_lock(&lock, K_FOREVER);
    struct bt_conn *conn = connection ? bt_conn_ref(connection) : NULL;
    k_mutex_unlock(&lock);
    if (conn) {
        bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
        bt_conn_unref(conn);
    }
}
void sensor_session_wait(uint32_t milliseconds) { k_sem_take(&wake, K_MSEC(milliseconds)); }
static ssize_t read_config(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                           void *buf, uint16_t len, uint16_t offset)
{
    uint8_t wire[SENSOR_CONFIG_SIZE];
    k_mutex_lock(&lock, K_FOREVER);
    sensor_config_encode(&current, wire);
    k_mutex_unlock(&lock);
    return bt_gatt_attr_read(conn, attr, buf, len, offset, wire, sizeof(wire));
}
static ssize_t write_config(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                            const void *buf, uint16_t len, uint16_t offset, uint8_t flags)
{
    ARG_UNUSED(conn); ARG_UNUSED(attr);
    if (offset || flags) return BT_GATT_ERR(BT_ATT_ERR_NOT_SUPPORTED);
    const uint8_t *data = buf;
    k_mutex_lock(&lock, K_FOREVER);
    int rc;
    if (save_pending || sample_pending) rc = -EBUSY;
    else if (len == 1 && data[0] == 4 && !IS_ENABLED(CONFIG_SENSOR_OTA)) {
        sample_pending = true;
        sample_valid = false;
        rc = 0;
    } else if (storage_error) rc = storage_error;
    else {
        rc = sensor_config_command(&transaction, data, len, &pending);
        if (rc == 1) {
            save_pending = true;
            save_error = 0;
        }
    }
    k_mutex_unlock(&lock);
    if (rc < 0) return BT_GATT_ERR(rc == -EINVAL ? BT_ATT_ERR_VALUE_NOT_ALLOWED : BT_ATT_ERR_UNLIKELY);
    k_sem_give(&wake);
    return len;
}
static ssize_t read_status(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                           void *buf, uint16_t len, uint16_t offset)
{
    uint8_t wire[48] = {1};
    k_mutex_lock(&lock, K_FOREVER);
    wire[1] = sample_valid | (stored << 1) | (save_pending << 2) |
              ((storage_error != 0) << 3) | (IS_ENABLED(CONFIG_SENSOR_OTA) << 4) |
              (sample_pending << 5);
    sys_put_le16(last_sample.battery_mv, wire + 2);
    sys_put_le16(last_sample.temperature_cc, wire + 4);
    sys_put_le16(last_sample.humidity_cpct, wire + 6);
    sys_put_le32(last_sample.capacitance_ff[0], wire + 8);
    sys_put_le32(last_sample.capacitance_ff[1], wire + 12);
    sys_put_le32((uint32_t)(k_uptime_get() - sampled_at) / 1000, wire + 16);
    sys_put_le32(sample_error, wire + 20);
    sys_put_le32(storage_error ? storage_error : save_error, wire + 24);
    sys_put_le32(saves, wire + 28);
    int64_t remaining = connection ? session_limit - (k_uptime_get() - connected_at) / 1000 : 0;
    sys_put_le16(remaining > 0 ? remaining : 0, wire + 32);
    wire[34] = version_major; wire[35] = version_minor; wire[36] = version_patch;
    wire[39] = version_patch >> 8;
    wire[37] = last_sample.capdac[0]; wire[38] = last_sample.capdac[1];
    memcpy(wire + 40, diagnostics, sizeof(diagnostics));
    k_mutex_unlock(&lock);
    return bt_gatt_attr_read(conn, attr, buf, len, offset, wire, sizeof(wire));
}
BT_GATT_SERVICE_DEFINE(sensor_configuration,
    BT_GATT_PRIMARY_SERVICE(&service_uuid),
    BT_GATT_CHARACTERISTIC(&config_uuid.uuid, BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE,
        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE | BT_GATT_PERM_PREPARE_WRITE,
        read_config, write_config, NULL),
    BT_GATT_CHARACTERISTIC(&status_uuid.uuid, BT_GATT_CHRC_READ,
        BT_GATT_PERM_READ, read_status, NULL, NULL));
