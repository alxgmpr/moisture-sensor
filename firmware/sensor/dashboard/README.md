# Local sensor dashboard

Run from the repository root with Node.js (no npm install):

```sh
node firmware/sensor/dashboard/serve.mjs
```

Open <http://127.0.0.1:8766> in Chrome or Edge on a Bluetooth-capable computer.
The server binds only to loopback and serves only the dashboard assets. No
cloud, external scripts, account, or Internet connection is needed after the
files are present. Web Bluetooth requires a secure context: localhost works;
a remotely hosted copy needs HTTPS. Safari/Firefox are not supported. The
in-app preview can display the page; use Chrome/Edge if its Bluetooth chooser
is unavailable. `PORT=9000` overrides the local server port.

Use **Explore with demo data** to review the interface without a sensor.
Demo saves are memory-only and clearly labelled.

## Connect and configure

1. Install the normal **0.2.9 or newer configuration-capable image** once using
   the existing signed MCUmgr/SMP update process. Firmware 0.2.5 has no custom
   configuration service. This dashboard configures the device over BLE; image
   upload still uses an SMP client and the generated `dfu_application.zip`.
2. Click **Connect a sensor**, then reinsert the battery or wait for the sensor's
   next advertising window. Only awake devices appear. The default production
   window in 0.2.11 is 5 seconds every 15 minutes; existing saved settings override defaults. Bluetooth cannot wake System OFF.
3. Read the device's settings before editing. Select name, measurement interval,
   advertising spacing/window, connection limit, and low-battery backoff.
4. For calibration, place the probe in its dry reference, click **Measure now**,
   and capture dry. Repeat for the wet reference. Capture requires a valid sample
   at most 30 seconds old. The two channels are independent. Existing defaults
   are provisional water endpoints, not a validated soil-water-content model.
5. **Save to sensor** stages the entire configuration, commits it, waits for the
   durable save counter, and compares a full readback. A lost connection produces
   an unconfirmed-save message: reconnect and reload before retrying.
6. Disconnect. Radio settings, advertised name, and calibration affect the next
   wake. The updated measurement cadence selects the upcoming sleep. Changing
   the connection limit never extends the current connection; it affects the
   next one. A five-minute limit is the default; allow up to 15 minutes in a
   subsequent connection when an SMP upload needs it.

Saved values override build defaults across cold boots, battery removal, and
compatible OTA updates. A full-chip erase erases them. Updates must preserve
`pm_static.yml` and the configuration protocol/storage format. Maintenance mode
can edit settings but cannot take sensor measurements, and stays awake by design.

This prototype retains the existing open BLE access model. The browser chooser
restricts which websites get access on the host; it does **not** authenticate a
nearby BLE client to the sensor. Reads and configuration writes are unencrypted
and unpaired. Before field deployment, choose an ownership/commissioning scheme.
MCUboot signature verification applies to firmware images, not configuration.

Firmware 0.2.11 accepts a low-battery backoff threshold down to 800 mV; older firmware requires at least 2200 mV. This configurable threshold selects the longer interval. The separate fixed cutoff in 0.2.11 is an experimental 800 mV input floor, with regulated-output checks still required. The default backoff remains 2500 mV.

## Protocol v1

Discovery filters on existing SMP UUID `8d53dc1d-1db7-4cd3-868b-8a527460aa84`
in the scan response. Custom service `6d6f6973-7475-7265-8000-000000000001`
contains configuration characteristic `…0002` (read/write with response) and
status characteristic `…0003` (read). All integers below are little-endian.
A name of at most 11 ASCII bytes keeps name + SMP UUID within the 31-byte scan
response. The BTHome measurement packet remains primary advertising data.

Configuration is exactly 64 bytes:

| Offset | Field |
| --- | --- |
| 0 | Version = 1 |
| 1 | Calibrated moisture enabled (0/1) |
| 2 | Name byte length (0–11; empty = chip-derived name) |
| 3 | Reserved zero |
| 4, 8, 12 | uint32 measurement seconds, low-battery seconds, advertising window ms |
| 16, 18, 20 | uint16 advertising spacing ms, connection seconds, low-battery mV |
| 22–23 | Reserved zero |
| 24, 28, 32, 36 | int32 SENSE1 dry/wet and SENSE2 dry/wet in fF |
| 40–50 | Name bytes; unused bytes zero |
| 51–63 | Zero |

Validation in `src/config.c` and `protocol.mjs` agrees on bounds and canonical
encoding. It prevents equal calibration endpoints, out-of-range values,
unbounded sessions, excessive window duty (>50%), and fewer than five nominal
advertising events per window. Actual reception count is not guaranteed.

Writes are explicit transactions, each at most 20 bytes (works at ATT MTU 23):

- `01`: begin a new staging buffer; discard incomplete prior staging.
- `02 offset data…`: write 1–18 bytes at offset 0–63. All 64 bytes must arrive.
- `03 crc32_le`: validate complete data and CRC-32/ISO-HDLC, queue a single save.
- `04`: queue one fresh sample (normal image only); no persistent write.

ATT success for commit means **queued**, not saved. The foreground loop handles
RRAM/I2C, never the Bluetooth callback. Prepared/long writes are rejected.
Incomplete staging is discarded on disconnect. An already accepted commit is
finished even after disconnect. Only one connection/request can run at a time.

Status is 48 bytes:

| Offset | Field |
| --- | --- |
| 0 | Protocol = 1 |
| 1 | Bits: valid sample, persisted settings, save pending, storage fault, maintenance, sample pending |
| 2, 4, 6 | uint16 battery mV, int16 temperature ×100, uint16 RH ×100 |
| 8, 12 | int32 raw SENSE1/2 fF |
| 16 | uint32 sample age seconds |
| 20, 24 | int32 sample error, storage/save error (0 = success) |
| 28 | uint32 successful-save counter for this boot |
| 32 | uint16 connection seconds remaining |
| 34, 35, 36 | MCUboot version major, minor, patch low byte |
| 37, 38 | CAPDAC for SENSE1/2 |
| 39 | Patch high byte |
| 40–47 | Reserved |

ZMS stores one CRC-protected canonical record in two 2 KB logical RRAM sectors
at `0x164000..0x165000`, replacing only the old `EMPTY_1` partition. No MCUboot
slot changes. No sample, boot counter, or periodic status writes go to storage.
Unchanged saves skip writing. Storage errors keep build defaults and disable
saves; the application never automatically wipes a failed mount.

The SDK v3.2.2 implementation of `CONFIG_ZMS_NO_DOUBLE_WRITE` fails to compile
without a lookup-cache-related declaration. The application performs its own
unchanged-record comparison and leaves that option off.

## Validation

```sh
sh firmware/sensor/tests/run.sh
CFLAGS='-fsanitize=undefined' sh firmware/sensor/tests/run.sh
```

Host tests cover configuration bounds, malformed/partial/replayed transactions,
CRC failure, reversed calibration, overflow edges, start-to-start timing, and
C/browser binary compatibility, plus existing sensor fault injection and
BTHome packets. Browser demo checks exercise presets, saves and rendering.
Direct BLE saves, fresh samples, cold-boot persistence, and retention across a signed OTA update were checked on Soil-402A. See the [validation record](../../../docs/power-and-configuration-2026-09-21.md). Browser-to-device interaction through Chrome’s chooser, power removal, interrupted flash writes, and actual current measurements remain separate checks; a build or demo is not evidence of those behaviors.

References: [Chrome Web Bluetooth](https://developer.chrome.com/docs/capabilities/bluetooth),
[Zephyr ZMS](https://docs.zephyrproject.org/latest/services/storage/zms/zms.html).
The implementation was built against the repository's NCS v3.2.2 sources.
