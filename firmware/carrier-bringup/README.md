# Battery-powered moisture sensor firmware

This image exercises the actual BL54L15/nPM2100/FDC1004/SHT40 board. Development and production modes broadcast calibrated BTHome moisture values using the configured dry/wet endpoints.

Development mode uses a 60-second cycle and a 300-second BLE window so a host can complete a full image upload. Production defaults to a 15-minute cycle, a 10-second BLE window, and backs off to a 1-hour cycle below 2.5 V. The current development image is selected with `dev.conf`.

The current provisional two-point water calibration is SENSE1 2655 fF dry / 5658 fF wet and SENSE2 2618 fF dry / 5571 fF wet. These wet endpoints are the median of recent raw submerged readings. They are a provisional water reference, not final soil calibration.

## Implemented sequence

1. Arm the MCU watchdog (15 seconds). Verify the dedicated FDC bus is suspended with no internal pull-ups, then disable any sensor rail left enabled across an MCU reset.
2. Configure the nPM2100's independent 20-second **power-cycle** watchdog, including LDOSW-off on watchdog reset. Sampling is bounded without watchdog feeding. The foreground BLE/OTA loop feeds both watchdogs once per second; a stalled loop still expires the independent watchdog.
3. Read battery voltage. Below the provisional 2.2 V cutoff, skip sensing/radio and shut down normally. This threshold is a starting point for CR2032 load testing, not a battery state-of-charge curve.
4. Set boost to 3.3 V, force HP, confirm the actual HP status, and check output ADC ≥3.15 V. The ADC saturates near 3.3 V; it cannot prove absence of overvoltage or measure 10 mV ripple.
5. Configure LDOSW as a **load switch**, force HP and enable its lowest 40 mA current limit. This protects that output only; it is not a battery fuse or whole-board current limit.
6. Identify FDC1004, measure CIN1/CIN2 single-ended at 100 samples/s, automatically increase CAPDAC until the residual is within ±13 pF. Differential mode is never used because the board ties SHLD1/2 together. Return an error when range is exhausted.
7. Read SHT40 temperature and humidity with CRC validation. No heater command is implemented. Recheck battery voltage under the sensing load, verify the FDC bus is suspended, and disable the sensor rail before starting BLE/OTA.
8. Advertise the stable chip-derived `Soil-XXXX` identity with BTHome v2 battery percentage, temperature, humidity, battery voltage, two calibrated moisture objects, and two diagnostic count objects. The first diagnostic count is the last failure stage and the second is the absolute errno value. These are kept in `.noinit` while SRAM survives a reset; battery removal and PMIC power cycles clear that history. Failed samples advertise diagnostics only, never zero-valued measurements. The percentage is a provisional voltage-to-SoC estimate for the CR2032 prototype; the voltage remains available for calibration. The same wake is connectable and exposes MCUmgr/SMP in the scan response; a client connection keeps the device awake for OTA.
9. Confirm LDOSW disabled using its HP/ULP status bits, return boost to auto, and disarm the PMIC watchdog. If shutdown cannot be confirmed, reboot with watchdog recovery still armed. A low-battery cutoff skips BLE and enters System OFF with the low-battery interval, rather than immediately rebooting. Only a fully successful cycle confirms a staged MCUboot image.

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

The sensor image is version `0.2.5` and remains OTA-capable: connect
during any 10-second advertising window, discover the SMP service, run image
list, upload, test, reset, and confirm. A connected session prevents System OFF
until the client disconnects or the image reboots. The maintenance image is
version `0.2.6`, advertises as `Soil-OTA`, and is a radio-only SWD/recovery
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

# Development cadence: 60 s measurement, 300 s advertising
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

The long development advertising window remains 300 seconds, but the sensor
supply is now off for that entire window. The PMIC watchdog is serviced alongside
the MCU watchdog. Undervoltage does not start a recovery radio window.

The deployed bootloader uses RSA-2048 signatures over SHA-256 image hashes.
`sysbuild.conf` pins this format; package validation checks the image digest,
header, version and TLV formats. Do not change it to the newer SDK's SHA-512
default without planning a bootloader migration.
