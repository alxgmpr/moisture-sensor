# PMIC/FDC timeout investigation

## Findings

The connected Soil-402A sensor reported MCUboot version 0.2.4, confirmed and
active. Its flash was backed up before any programming. The running application
was slightly older than the local ELF, so breakpoint locations were verified
against the downloaded executable rather than assumed from that ELF.

Two power-lifecycle defects are confirmed in the firmware:

1. `carrier_start()` arms a 20-second nPM2100 power-cycle watchdog, but the
   foreground BLE loop only fed the MCU watchdog. Development advertising lasts
   300 seconds, and a connected OTA session has no fixed duration. A healthy
   radio session therefore outlives the PMIC watchdog. This resets both the
   supply and the PMIC register state during normal operation.
2. A battery cutoff or failed measurement entered a long recovery advertising
   window, published fabricated zero measurements, and immediately rebooted.
   This repeatedly loaded a depleted cell instead of following the documented
   low-battery sleep policy. The FDC supply was also left enabled throughout
   advertising and error recovery.

The current battery initially reported approximately 2.2–2.3 V. A hardware
breakpoint immediately after `carrier_start()` subsequently captured `-ERANGE`
(-34) with battery readings of 1925, 1887, 1862, and 1825 mV. These are below the
existing 2200 mV cutoff. The user elected to continue with this battery and
defer a fresh-cell measurement run until the firmware work is complete.

**The reported -116 itself was not reproduced in this session.** Carrier status
polls return `-ETIMEDOUT`; the documented NCS v3.2.2 TWIM driver returns `-EIO`
on transfer timeout. A generic stage or errno therefore does not identify a
PMIC or FDC hardware defect. No claim is made that a specific FDC silicon,
I2C waveform, or board electrical fault has been demonstrated or eliminated.

## Changes

- Keep the independent PMIC watchdog, and kick it once per second alongside
  the MCU watchdog only from the foreground radio/OTA loop. Sampling still
  runs with a fixed watchdog deadline and no feeding. A stalled radio loop
  still expires the PMIC watchdog.
- Disconnect the FDC bus and shut down its supply immediately after sampling,
  including sample failures. Keep BOOST in HP for BLE.
- Check LDOSW HP and ULP status bits when disabling the rail. The previous
  check used `STATUS.LDO`, which is already zero while a load switch is ON.
  Allow the observed disabled status to retain the SW bit (0x02).
- Respect the unchanged 2200 mV battery cutoff: release the rail, return BOOST
  to automatic mode, stop the PMIC watchdog, and enter System OFF for the
  low-battery interval. Do not start a recovery radio window on undervoltage.
- Wait for `ADC.STATUS.ADC == Ready` before clearing a completion event and
  triggering another ADC conversion, as required by the nPM2100 datasheet.
- Remove the three-attempt startup retry and the arbitrary 250 ms pre-start
  delay. Keep bounded status checks and the existing 25 ms I2C timeout.
- Capture the first failed transaction or status wait: address, register,
  observed value, mask, expected value, and errno. Preserve it across cleanup.
  Initialize retained diagnostics fully when their magic/layout is invalid;
  do not interpret uninitialized SRAM as a historical error. Count boots once
  per boot. Store the sample and planned sleep interval for bench inspection.
- A failed sample with a verified radio supply advertises diagnostic count
  objects and SMP only, without invented temperature/moisture/voltage values.
  Failure paths sleep after cleanup and leave a staged image unconfirmed.
- Finish MCUboot confirmation before GRTC wake preparation disables kernel
  compare channels; leave only trace stores and System OFF after preparation.
  This means a later wake-preparation failure cannot trigger MCUboot rollback
  of an already confirmed image; it remains an explicit stage-81 error.
- Pin RSA-2048 signatures and SHA-256 image/key hashes to match the installed
  bootloader. Incompatible SDK signing defaults were rejected by comparison
  with the running image before programming. The package validator checks this
  format and the actual
  image digest; `DFU_PACKAGE` selects the package being tested explicitly.
- Build sensor 0.2.5 and maintenance 0.2.6. Remove aliases to deleted DK
  LEDs/buttons, and use the documented SDK's `BT_LE_ADV_OPT_CONN` option.

## Sources and scope

- [nPM2100 datasheet](https://docs.nordicsemi.com/r/bundle/ps_npm2100/), locally
  archived as `doc/datasheets/nPM2100_Datasheet_v1.0.pdf`: sections 6.2.4.7
  (LDOSW status), 7.1 / 7.1.2.14 (ADC availability), and 7.2.2 / 7.2.6.3
  (watchdog power cycle and kick task).
- [TI FDC1004 Rev. C](https://www.ti.com/lit/ds/symlink/fdc1004.pdf), sections
  6.5.2 and 6.6.1.3: I2C transaction requirements and conversion/DONE fields.
  The single-shot trigger, completion check, and full two-byte register reads
  remain in use. No sensor reset/retry workaround was added.
- NCS v3.2.2 local sources: `zephyr/drivers/i2c/i2c_nrfx_twim.c` maps transfer
  failures to `-EIO`; `zephyr/include/zephyr/bluetooth/bluetooth.h` defines the
  connectable advertising option used by this build.

Host tests model conversion delay, an ADC busy across an MCU reset, delayed and
stuck rail shutdown, and a five-minute radio session. They distinguish PMIC
and FDC status timeouts from transport failures, retain the first fault during
cleanup, and verify that an unserviced PMIC watchdog still expires. The existing
transaction-by-transaction fault injection, range and CRC tests also pass,
including an undefined-behavior sanitizer run. Packet tests verify that a
diagnostic-only advertisement contains no measurement objects.

## Hardware validation

Sensor 0.2.5 was built with NCS v3.2.2, `--sysbuild -p always`,
`nrf54l15dk/nrf54l15/cpuapp`, this application's overlay, and `dev.conf`.
This preserves the DK base used by the deployed firmware; the README's Ezurio
DVK target was not the target tested in this session. A pristine build was
required after changing the signature algorithm to discard cached crypto settings.

Both the signed binary and signed HEX passed cryptographic verification with
the same RSA-2048 key as the original firmware. Only the application slot was
programmed; the signed HEX covers `0x0000e000..0x000346d0` (end exclusive).
The first flash attempt
lost SWD communication during programming; the second completed. The cause of
that interruption was not established. Full signed-application readback then
matched the HEX, and the original bootloader bytes were unchanged.

The first boot read 2125 mV and reached stage 83 with `-ERANGE` and a 3600-second
wake interval: the sensor supply was disabled, BOOST returned to automatic
mode, and the PMIC watchdog was stopped. A debugger inspection located the CPU
in the System OFF wait loop. This establishes execution of the shutdown path,
not the board's actual sleep current.

After resting, the same battery recovered enough for a complete second sample:

| Reading | Value |
| --- | --- |
| Battery under sensing load | 2225 mV |
| BOOST output ADC | 3294 mV |
| SENSE1 / SENSE2 | 2318 / 2324 fF |
| CAPDAC | 0 / 0 |
| Temperature | 24.44 °C |
| Relative humidity | 41.01% |

Read-only debugger observations showed that sample and boot count 2 unchanged
through 40 seconds of advertising, past both watchdog deadlines. BLE scanning
received the corresponding BTHome packet from Soil-402A. Its diagnostic stage 50,
errno 34 referred to the earlier low-battery boot, not a new failure. SMP image
list independently reported the active, bootable 0.2.5 image and matching hash.
The existing primary-slot confirmation marker was retained by this direct SWD
update; this session does not qualify an OTA test-image rollback.

A read-only SMP connection then remained live for 270.66 seconds, with ten
successful image-list responses. Together with advertising before connection,
the same cycle ran for over 342 seconds without resetting, beyond the full
300-second development window. The client disconnected cleanly. Reattaching
SWD afterward found the SRAM trace lost and `RESETREAS=0x400`. The nRF54L15 MDK
defines bit 10 as DIF, reset triggered by the debug interface. This is consistent
with System OFF clearing unretained SRAM and debug attachment waking the board;
the attempted assertion that stage 83 would still be readable was invalid.
It is not evidence of a new sensor timeout. A subsequent 12-second BLE scan
found no Soil-402A advertisement. Do not use post-System-OFF `.noinit` reads as
proof of a completed cycle or as persistent error storage.

Local build artifacts, the original flash backup, and validation logs are in
`output/firmware-0.2.5/` (ignored by Git). The application image hash is
`86b0df2cebf2446f885bd08bf40b37ca15d797a64e5e57bd1032eaa8b7404838`.
For this exact ELF, `sensor_trace` is at `0x200040d0`, size 60 bytes; its full
field layout is in `src/main.c`. Maintenance 0.2.6 also built and passed
signature/package validation, but was not flashed.

## Fresh battery follow-up

The user replaced the cell and measured the removed cell at 2.2 V with a DMM.
The first fresh-cell sample reported 3187 mV under sensing load, 3288 mV at
BOOST, 2275/2322 fF with CAPDAC 0/0, 25.46 °C, and 41.66% RH. The first boot's
failure stage, error, and register-level fault record were all zero. Firmware
was left unchanged at 0.2.5.

Cycle validation uses repeated five-second BLE scans with no connection,
reset, or SWD access during observation. An initial read-only SWD snapshot
was taken while the board was already advertising, then the debugger session
was closed. macOS can suppress duplicate advertisements within a scan, so
each observation starts a new scan. Logs include other discovered devices to
distinguish target silence from a scanner failure. Evidence is stored in
`output/fresh-battery-validation-2026-09-21/`.

The follow-up passed over 582 seconds of observation (17:28:38–17:38:16 UTC):

| Sample | Loaded battery | Temperature | Relative humidity | Diagnostic stage / errno |
| --- | --- | --- | --- | --- |
| Initial fresh-cell boot | 3187 mV | 25.46 °C | 41.66% | 0 / 0 |
| First automatic wakeup | 3062 mV | 25.19 °C | 41.72% | 0 / 0 |
| Second automatic wakeup | 3000 mV | 24.92 °C | 40.73% | 0 / 0 |

The two observed advertising gaps were 62.02 and 67.97 seconds. The complete
middle advertising window was observed for 296.85 seconds; its first packet to
the next cycle's first packet took 364.83 seconds. These observations are
consistent with 300 seconds advertising plus 60 seconds System OFF, allowing
for boot/sensing time and the five-second scan / one-second pause resolution.
Other devices remained visible while Soil-402A was silent. Each advertising
window kept a consistent payload, and each wake produced new sensor values.
No -116 or other diagnostic fault was observed.

After cycle observation finished, a read-only debugger snapshot was taken
while the third window was already advertising. It showed `RESETREAS=0x800`,
the nRF54L15 GRTC wakeup bit, with no other reset source set. The fault record
was zero, BOOST read 3294 mV, and the raw channels were 2263/2316 fF at CAPDAC
0/0. This confirms a timer wakeup rather than a watchdog or debug-triggered
restart. SRAM history and the boot count correctly restarted after System OFF.
The probe session was closed afterward.

An actual OTA upload/test/rollback, long-term reliability run, and sleep-current
measurement remain separate validation work. If -116 recurs, use the new
register-level fault record to identify its source before changing timing or
the sensor protocol. This finite bench run validates the tested cycles; it
cannot establish an error-free operating rate indefinitely.
