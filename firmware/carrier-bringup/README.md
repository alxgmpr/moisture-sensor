# Battery-powered moisture sensor firmware

This image exercises the actual BL54L15/nPM2100/FDC1004/SHT40 board. Development and production modes broadcast calibrated BTHome moisture values using the configured dry/wet endpoints.

The low-voltage policy uses a 1.8 V PMIC-ADC cutoff and 2.0 V recovery threshold. MCUboot checks input before image verification or swapping; the application repeats the check before settings, sensing and radio work. Undervoltage and interrupted attempts enter a 60-second PMIC hibernate retry, with timed MCU System OFF as a fallback. These are conservative bench thresholds, not a qualified CR2032 discharge endpoint. After undervoltage, recovery waits for the next 60-second retry even if the battery voltage rises. A brief input power cycle may preserve PMIC Hibernate state; it is not a guaranteed immediate wake. See [the investigation](../../docs/low-voltage-investigation-2026-09-21.md).

Version 0.2.9 added [local browser configuration](dashboard/README.md) with persistent name, intervals, and two-point calibration over BLE. Run `node firmware/carrier-bringup/dashboard/serve.mjs` from the repository root and open http://127.0.0.1:8766 in Chrome/Edge. Existing 0.2.5 devices need one firmware update before configuration is available.

Production defaults to a 15-minute measurement interval, a 5-second BLE window with 500 ms advertising spacing, and a 1-hour interval below 2.5 V. Development mode (`dev.conf`) uses a 60-second interval and 30-second window. These intervals include application awake time. An established connection may last up to 300 seconds by default; configure up to 900 seconds before reconnecting for longer SMP uploads. Stored settings override build defaults. See the [power audit](../../docs/power-and-configuration-2026-09-21.md) for calculations, limits, and measurement priorities.

The current provisional two-point water calibration is SENSE1 2655 fF dry / 5658 fF wet and SENSE2 2618 fF dry / 5571 fF wet. These wet endpoints are the median of recent raw submerged readings. They are a provisional water reference, not final soil calibration.

## Implemented sequence

1. MCUboot disables the DK UART pins that overlap the FDC bus, reads the PMIC input and retained retry marker, and gates image processing. A retained BOOTING marker and independent 60-second PMIC watchdog cover image verification and swapping.
2. The application verifies the FDC bus is suspended, disables the sensor rail, and repeats the voltage/retained-state check before loading settings. It arms the 15-second MCU watchdog, then the 20-second PMIC power-cycle watchdog before sensing. The BLE foreground loop feeds both once per second.
3. Below 1.8 V, or after an interrupted attempt, skip sensor/radio work. Save BLOCKED in the PMIC VBAT-domain scratch register, switch off the sensor rail, select Auto and enter timed Hibernate. Recovery requires at least 2.0 V. No flash writes or immediate application-error reboots occur on this path.
4. Set boost to 3.3 V, force HP, confirm the actual HP status, and check output ADC ≥3.15 V. The ADC saturates near 3.3 V; it cannot prove absence of overvoltage or measure 10 mV ripple.
5. Configure LDOSW as a **load switch**, force HP and enable its lowest 40 mA current limit. This protects that output only; it is not a battery fuse or whole-board current limit.
6. Identify FDC1004, measure CIN1/CIN2 single-ended at 100 samples/s, automatically increase CAPDAC until the residual is within ±13 pF. Differential mode is never used because the board ties SHLD1/2 together. Return an error when range is exhausted.
7. Read SHT40 temperature and humidity with CRC validation. No heater command is implemented. Recheck battery voltage under the sensing load, verify the FDC bus is suspended, and disable the sensor rail before starting BLE/OTA.
8. Confirm the sensor supply is off, select automatic BOOST, and require output ADC ≥3.15 V before starting the radio. A connected Measure-now operation forces HP for sensing and restores Auto afterwards. Advertise the stable chip-derived `Soil-XXXX` identity with BTHome v2 battery percentage, temperature, humidity, battery voltage, and two calibrated moisture objects. Last failure stage and errno remain available through the status characteristic and `.noinit` trace while SRAM survives a reset; battery removal and PMIC power cycles clear that history. Failed samples enter backoff without starting the radio. The percentage is a provisional voltage-to-SoC estimate for the CR2032 prototype; the voltage remains available for calibration. The same wake is connectable and exposes MCUmgr/SMP in the scan response; a client connection keeps the device awake for configuration/OTA until its configured deadline.
9. Confirm LDOSW disabled using its HP/ULP status bits, return boost to auto, and disarm the PMIC watchdog. If shutdown cannot be confirmed, enter the same bounded backoff path. SCRATCHA survives MCU resets and PMIC watchdog power cycles while VBAT remains above the PMIC retention limit. If GRTC preparation fails, stay off and require an external wake rather than repeatedly rebooting. Only a fully successful cycle confirms a staged MCUboot image.

Normal wake uses GRTC System OFF with the configured 15-minute/hourly schedule. Nothing using I2C, logging or kernel timeouts executes after GRTC wake preparation. Both bootloader and application fault retry defaults are 60 seconds, independently of the production 900/3600-second measurement schedule. A bootloader update requires SWD; application OTA alone cannot install its early gate.

Both buses run at 100 kHz with a 25 ms transaction timeout; conversion/status polling is also bounded. Startup performs one sequence, without blanket retries or an arbitrary cold-start delay. ADC conversions wait for the PMIC ADC to become idle before clearing the ready event and triggering a new measurement. Host tests inject a transient failure at every transaction in a successful cycle and cover CRC, range, timeout, undervoltage and a converter that fails to enter HP.

## Build and test

Nordic nRF Connect SDK **v3.2.2**, board `bl54l15_dvk/nrf54l15/cpuapp`, with this application's `app.overlay`. The overlay removes the DVK LEDs/buttons/external flash/UART, assigns TWIM22 to main-bus SDA=P1.10 and SCL=P1.11 and TWIM20 to FDC SDA=P1.05 and SCL=P1.04, enables WDT31, and sets the provisional X1 internal load to 12 pF per leg. HFXO retains the Ezurio DVK's 15 pF setting. Verify crystal frequency and cold startup on the board.

```sh
west build --sysbuild -p always -b bl54l15_dvk/nrf54l15/cpuapp firmware/carrier-bringup
sh firmware/carrier-bringup/tests/run.sh
# Validate the package being deployed, rather than a stale cached archive:
DFU_PACKAGE=/path/to/dfu_application.zip sh firmware/carrier-bringup/tests/run.sh
# Optional host undefined-behavior checks:
CFLAGS=-fsanitize=undefined sh firmware/carrier-bringup/tests/run.sh
```

The original shared-bus build is archived in `docs/reliability-2026-09-07/firmware/` and is obsolete for this wiring. The dedicated-bus build evidence is in `docs/fdc-bus-update-2026-09-09/`. Compilation verifies SDK integration, not hardware operation. The original DK demo remains available separately.

To build the fast bench image, add `-- -DEXTRA_CONF_FILE=dev.conf`. The production defaults are used without that override. The current default dry/wet endpoints are SENSE1=2655/5658 fF and SENSE2=2618/5571 fF.

## OTA maintenance image and deployed OTA path

The OTA variant is selected with `ota.conf` and is built as an MCUboot image
for `bl54l15_dvk/nrf54l15/cpuapp`. It powers only the radio supply, leaves the
sensor rail off, does not arm the 20-second PMIC power-cycle watchdog, and
advertises as `Soil-OTA` using MCUmgr/SMP over BLE. The generated
`dfu_application.zip` is the package to upload with Nordic Device Manager.

```sh
west build --sysbuild -p always \
  -b bl54l15_dvk/nrf54l15/cpuapp \
  -d build-sensor-ota carrier-bringup \
  -- -DEXTRA_CONF_FILE=ota.conf
```

The sensor image is version `0.2.28` and remains OTA-capable: connect
during any configured advertising window, discover the SMP service, run image
list, upload, test, reset, and confirm. A connected session prevents System OFF
until the client disconnects or the image reboots. The maintenance image is
version `0.2.29`, advertises as `Soil-OTA`, and is a radio-only SWD/recovery
image; it is not the normal sensor image.

MCUboot uses the generated primary and secondary slots. A staged image boots
from secondary as a test image and remains unconfirmed until the sensor has
initialized both buses, completed a valid measurement, published BTHome,
completed BLE/OTA handling, and shut down the switched rail. Confirmation
finishes before GRTC wake preparation disables the kernel compare channels. If any of those checks fails, the image is not confirmed and MCUboot selects
the previous primary image on the next reset. The normal sensor build contains
MCUmgr/SMP, so future updates do not need to replace the OTA path.

The current key is the SDK development key and must never be used for a field
release. Generate a protected production key, pass it explicitly to imgtool
through the NCS signing configuration, record its public-key hash, and keep the
private key outside this repository. CI should fail if the development key is
selected for a production profile.

## Build, BLE OTA, and recovery

```sh
# Production sensor image; no EXTRA_CONF_FILE
west build --sysbuild -p always -b bl54l15_dvk/nrf54l15/cpuapp \
  -d build-sensor firmware/carrier-bringup -- \
  -DSB_CONFIG_BOOT_SIGNATURE_KEY_FILE=/secure/keys/sensor-rsa-2048.pem

# Development cadence: 60 s measurement, 30 s advertising
west build --sysbuild -p always -b bl54l15_dvk/nrf54l15/cpuapp \
  -d build-sensor-dev firmware/carrier-bringup -- \
  -DEXTRA_CONF_FILE=dev.conf

# SWD/recovery maintenance image
west build --sysbuild -p always -b bl54l15_dvk/nrf54l15/cpuapp \
  -d build-sensor-ota firmware/carrier-bringup -- \
  -DEXTRA_CONF_FILE=ota.conf \
  -DSB_CONFIG_BOOT_SIGNATURE_KEY_FILE=/secure/keys/sensor-rsa-2048.pem
```

Set `SENSOR_PRODUCTION_BUILD=1` for release CI. The build then fails unless
`CONFIG_MCUBOOT_SIGNATURE_KEY_FILE` names a protected non-SDK key. The SDK
`root-rsa-2048.pem` key remains development-only.

Use `dfu_application.zip` from the sensor build with an SMP client. Verify the
target by image list and reject any package whose version is not greater than
the running image. Use image test, reset, image list, and image confirm only
after the new image advertises correctly. Verify Home Assistant by repeated
BLE scans for service data UUID `FCD2`, a `Soil-XXXX` name, and decoded
temperature, humidity, voltage and moisture objects.

For SWD recovery, keep the battery installed only with the safe wiring: GP2
to J4 pin 4/SWDCLK, GP3 to pin 2/SWDIO, and GND to pin 3, 5 or 9. Leave J4
pin 1/VTref and probe 3V3 disconnected. Use the read-only pyOCD command in
the project instructions first; flash only after confirming the image and
slot layout.

The PCB inspection confirms the TC2050 mapping: J4-1 is `+3V3`/VTref, J4-2
is `SWDIO_EXT`, J4-3/5/9 are GND, J4-4 is `SWDCLK_EXT`, J4-6 is SWO, J4-7/8
are no-connects, and J4-10 is `RESET_EXT`. The Raspberry Pi probe's GP1 is
UART RX and is not reset.

## Local configuration and storage

See [dashboard usage and protocol](dashboard/README.md). The configuration occupies
the former 4 KB `EMPTY_1` gap as `zms_storage`; neither image slot moves.
Calibration can be disabled without suppressing temperature, humidity or battery.
The dashboard's moisture cards preview its editable endpoints, while BTHome uses
the saved endpoints on the next wake. The normal image powers down after its
connection limit; the explicit maintenance image remains continuously awake.

## First hardware session

Use current-limited battery-equivalent power with the coin cell removed, or the coin cell with J4 used strictly as debugger voltage reference. Record startup and low-voltage behavior, FDC rail on/off voltages and leakage, 60-second wakes without a debugger, and 10-second RF current bursts. Confirm FDC_SDA/FDC_SCL and the switched rail remain low/unpowered while off, including main-bus traffic and reset transitions. The PMIC ADC cannot replace a scope for supply ripple and transients.

Log raw fF and CAPDAC values for air, dry soil, wet soil and saline water with the final coating and enclosure. CAPDAC steps are nominal and have device error; calibrate using actual readings and check continuity around CAPDAC changes. Observe shield amplitude and phase as load increases. No software guard can prove that a 400 pF shield-load limit is met.

## Dedicated FDC bus

Address 0x50 uses TWIM20; PMIC 0x74 and SHT40 0x44 use TWIM22. R36/R37
pull up to +3V3_FDC_SW. Runtime device PM starts TWIM20 suspended and applies
its no-pull sleep pinctrl state after every transfer, including failures.
No FDC transfer occurs until the sensor start sequence has enabled and settled
the rail. The application checks runtime PM and suspended state before the
start and stop sequences; a failure retains watchdog recovery. SPI20/UART20 remain
disabled because they share the peripheral instance. Verify these electrical
states on hardware; a successful build cannot measure leakage.

## Timeout investigation (2026-09-21)

See [the investigation and validation record](../../docs/timeout-investigation-2026-09-21.md).
`-ETIMEDOUT` from the carrier code records the chip address, register, last
observed value, mask, and expected value in `sensor_trace.fault`; an I2C error
has a zero mask. `sensor_trace.sample` and `wake_seconds` record the last cycle's
voltage and planned sleep. Stage 83 means shutdown and GRTC preparation completed.
Use the ELF from the exact flashed build to locate these symbols. A historical
BLE diagnostic is the last recorded failure, not a count of new errors.

In 0.2.5 the long development advertising window remained 300 seconds, with the sensor
supply off for that entire window. Version 0.2.9 reduces this to 30 seconds by default. The PMIC watchdog is serviced alongside
the MCU watchdog. Undervoltage does not start a recovery radio window.

The deployed bootloader uses RSA-2048 signatures over SHA-256 image hashes.
`sysbuild.conf` pins this format; package validation checks the image digest,
header, version and TLV formats. Do not change it to the newer SDK's SHA-512
default without planning a bootloader migration.
