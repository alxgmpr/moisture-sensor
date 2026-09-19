# Carrier qualification firmware

This image exercises the actual BL54L15/nPM2100/FDC1004/SHT40 board. Development and production modes broadcast calibrated BTHome moisture values using the configured dry/wet endpoints.

Development mode uses a 60-second cycle and a 2-second BLE window. Production defaults to a 15-minute cycle, a 1.6-second BLE window, and backs off to a 1-hour cycle below 2.5 V. The current development image is selected with `dev.conf`.

The current provisional two-point water calibration is SENSE1 2655 fF dry / 5658 fF wet and SENSE2 2618 fF dry / 5571 fF wet. These wet endpoints are the median of recent raw submerged readings. They are a provisional water reference, not final soil calibration.

## Implemented sequence

1. Arm the MCU watchdog (15 seconds). Verify the dedicated FDC bus is suspended with no internal pull-ups, then disable any sensor rail left enabled across an MCU reset.
2. Configure the nPM2100's independent 20-second **power-cycle** watchdog, including LDOSW-off on watchdog reset. No watchdog feeding can conceal an indefinitely long cycle.
3. Read battery voltage. Below the provisional 2.2 V cutoff, skip sensing/radio and shut down normally. This threshold is a starting point for CR2032 load testing, not a battery state-of-charge curve.
4. Set boost to 3.3 V, force HP, confirm the actual HP status, and check output ADC ≥3.15 V. The ADC saturates near 3.3 V; it cannot prove absence of overvoltage or measure 10 mV ripple.
5. Configure LDOSW as a **load switch**, force HP and enable its lowest 40 mA current limit. This protects that output only; it is not a battery fuse or whole-board current limit.
6. Identify FDC1004, measure CIN1/CIN2 single-ended at 100 samples/s, automatically increase CAPDAC until the residual is within ±13 pF. Differential mode is never used because the board ties SHLD1/2 together. Return an error when range is exhausted.
7. Read SHT40 temperature and humidity with CRC validation. No heater command is implemented. Recheck battery voltage under the sensing load.
8. Advertise the stable chip-derived identity with standard BTHome temperature, humidity and voltage objects, plus either calibrated moisture objects or raw SENSE1/SENSE2 capacitance.
9. Verify the dedicated FDC bus has returned to its disconnected sleep state, then confirm LDOSW disabled, return boost to auto, then disarm the PMIC watchdog. If shutdown cannot be confirmed, wait for watchdog recovery. Prepare GRTC and immediately enter System OFF; wake after 60 seconds.

Both buses run at 100 kHz with a 25 ms transaction timeout; conversion/status polling is also bounded. Host tests inject a transient failure at every transaction in a successful cycle and cover CRC, range, timeout, undervoltage and a converter that fails to enter HP.

## Build and test

Nordic nRF Connect SDK **v3.2.2**, board `bl54l15_dvk/nrf54l15/cpuapp`, with this application's `app.overlay`. The overlay removes the DVK LEDs/buttons/external flash/UART, assigns TWIM22 to main-bus SDA=P1.10 and SCL=P1.11 and TWIM20 to FDC SDA=P1.05 and SCL=P1.04, enables WDT31, and sets the provisional X1 internal load to 12 pF per leg. HFXO retains the Ezurio DVK's 15 pF setting. Verify crystal frequency and cold startup on the carrier.

```sh
west build -p always -b bl54l15_dvk/nrf54l15/cpuapp firmware/carrier-bringup
sh firmware/carrier-bringup/tests/run.sh
# Optional host undefined-behavior checks:
CFLAGS=-fsanitize=undefined sh firmware/carrier-bringup/tests/run.sh
```

The original shared-bus build is archived in `docs/reliability-2026-09-07/firmware/` and is obsolete for this wiring. The dedicated-bus build evidence is in `docs/fdc-bus-update-2026-09-09/`. Compilation verifies SDK integration, not hardware operation. The original DK demo remains available separately.

To build the fast bench image, add `-- -DEXTRA_CONF_FILE=dev.conf`. The production defaults are used without that override. The current default dry/wet endpoints are SENSE1=2655/5658 fF and SENSE2=2618/5571 fF.

## First hardware session

Use current-limited battery-equivalent power with the coin cell removed, or the coin cell with J4 used strictly as debugger voltage reference. Record startup and low-voltage behavior, FDC rail on/off voltages and leakage, 60-second wakes without a debugger, and two-second RF current bursts. Confirm FDC_SDA/FDC_SCL and the switched rail remain low/unpowered while off, including main-bus traffic and reset transitions. The PMIC ADC cannot replace a scope for supply ripple and transients.

Log raw fF and CAPDAC values for air, dry soil, wet soil and saline water with the final coating and enclosure. CAPDAC steps are nominal and have device error; calibrate using actual readings and check continuity around CAPDAC changes. Observe shield amplitude and phase as load increases. No software guard can prove that a 400 pF shield-load limit is met.

## Dedicated FDC bus

Address 0x50 uses TWIM20; PMIC 0x74 and SHT40 0x44 use TWIM22. R36/R37
pull up to +3V3_FDC_SW. Runtime device PM starts TWIM20 suspended and applies
its no-pull sleep pinctrl state after every transfer, including failures.
No FDC transfer occurs until carrier_start has enabled and settled the rail.
The application checks runtime PM and suspended state before carrier_start
and carrier_stop; a failure retains watchdog recovery. SPI20/UART20 remain
disabled because they share the peripheral instance. Verify these electrical
states on hardware; a successful build cannot measure leakage.
