# Firmware 0.2.11 power trial

This is the user-requested bench experiment for automatic nPM2100 BOOST operation during normal BLE advertising and operation below the former 2.2 V input cutoff. It is not a release qualification for CR2032 discharge or the module supply.

## Behavior

- Sensor conversion retains forced BOOST HP and its status check. VOUT stays at 3.3 V.
- Before normal BLE initialization/advertising, `sensor_radio_start()` confirms the sensor load switch is off, writes and reads back `BOOST.OPER=Auto`, and requires the output ADC to report at least 3.15 V. Auto permits the converter to enter HP on demand; it does not forbid HP.
- Connected configuration and SMP traffic use Auto too. A connected Measure-now request temporarily returns to HP for sensing and restores Auto afterwards. The MCU watchdog and independent PMIC watchdog remain in use.
- Normal defaults are 900 s measurement cadence, 5000 ms advertising window, and 500 ms event spacing (approximately ten events). Persistent settings override defaults; deployment explicitly writes and verifies the intended values without changing identity or calibration.
- Low-battery backoff remains 2500 mV and 3600 s. The configurable backoff threshold accepts 800–3300 mV in both firmware and dashboard. Older firmware only accepts thresholds at or above 2200 mV.
- The experimental fixed input floor is 800 mV. The application checks input before loading and after measurement, and requires the regulated output to pass its existing 3.15 V check. Detected undervoltage skips normal operation and schedules the low-battery interval. Other shutdown failures keep the existing watchdog recovery path.
- The separate 0.2.12 maintenance image remains forced HP for recovery. MCUboot slots, configuration record encoding, storage location, and signing key are unchanged. The deployed prototype still uses the previously installed SDK development key.

The 800 mV floor allows an experiment; it is not a promise that a depleted CR2032 can start or sustain the circuit there. A cell-induced collapse can occur before firmware checks complete, and the PPK's stiff supply does not model that failure. The voltage-to-percentage approximation still reports 0% at/below 2200 mV; it is not a fuel gauge or a shutdown command.

## Constraints being tested

The nPM2100 datasheet v1.0, Table 4 (page 10), gives a 0.7 V loaded operating minimum, 0.8 V loaded cold-start minimum, and typical 10 mA source capability during cold start. Full HP power/accuracy specifications have additional input-voltage conditions (page 17). Firmware uses 0.8 V as the experimental floor, not 0.7 V.

LP/ULP typical output ripple is 70 mV peak-to-peak. Ezurio specifies at most 10 mV supply ripple/noise for undisturbed BL54L15 radio operation. Successful advertising or an averaged PMIC ADC reading cannot prove ripple compliance. This trial deliberately evaluates Auto at the user's request; the hardware supply requirement has not been waived or proven met.

Nordic also warns that PPK2 may miss narrow boost-refresh pulses under light load. A reduction in the recorded current is evidence for comparison, but the very low absolute sleep reading remains uncertain.

## Validation completed before OTA

- Host sensor tests pass, including failures injected throughout sensing, transition to Auto, and shutdown; 800/1000/1500/2000 mV simulated acceptance with a healthy rail; rejection below 800 mV; input collapse during measurement; low output after entering Auto; sensor rail refusing to turn off; repeated connected measurements returning to Auto; and watchdog operation during the radio window.
- Configuration/transaction tests and six browser protocol tests pass, including compatible decoding of old 10 s / 1000 ms settings and new threshold boundaries.
- NCS v3.2.2 sysbuild succeeds using the deployed `nrf54l15dk/nrf54l15/cpuapp` base plus the sensor overlay.
- RSA signature verification succeeds; image version is 0.2.11+0. MCUboot image digest: `da25bec728742c5f82673b6b0e18077ec89fb3fb3aab719c5c3564d67971fc5b`.
- DFU manifest/header/version/hash checks and generated partition checks pass. An incremental build initially retained an old archive manifest version; explicit sysbuild reconfiguration regenerated the correct 0.2.11 manifest before deployment.

Build output, signed package, device deployment script, and logs are in `output/firmware-0.2.11/` (ignored by Git). The 0.2.9 package is preserved under `output/firmware-0.2.9/`.

## Hardware validation completed

- Updated the existing device over BLE SMP from confirmed 0.2.9 to signed 0.2.11. Upload took approximately 35 seconds. The new image was marked for a test boot; the application subsequently confirmed itself after a successful cycle. No debugger was used.
- Verified active image digest `da25bec728742c5f82673b6b0e18077ec89fb3fb3aab719c5c3564d67971fc5b` after a PPK power cycle. MCUboot reported it active, bootable, confirmed, and not pending. The old 0.2.9 image remains in the other slot.
- Saved and read back 900 / 3600 s intervals, 5000 ms window, 500 ms spacing, 2500 mV backoff, and 300 s connection limit. A subsequent cold boot returned the identical configuration and zero saves during that boot. Preserved the name `Soil 1` and all four calibration values (2655, 5658, 2618, 5571).
- Three connected Measure-now requests returned valid fresh readings with no sample or storage errors. Input readings were approximately 2950–2962 mV with the PPK set to 3000 mV. This exercises the HP sensing / Auto radio transition repeatedly.
- Captured a separate 38.21 s startup trace at 3.0 V / 100 Hz with power initially off and no BLE client connected. PPK displayed 717.61 µC total charge and 4.76 mA maximum. The long approximately 2.8 mA plateau from the original run was absent; the brief active event was followed by low readings. This is preliminary functional/power evidence, not a complete measurement interval or lifetime estimate.
- Native PPK Save remained disabled. Preserved the first 3000 samples already flushed to its temporary file as `output/firmware-0.2.11/auto-startup-3v-first-30s.raw`, with format/provenance and UI statistics in `auto-startup-summary.json`. Those 30 seconds integrate to 497.89 µC. The complete short trace remains unsaved in the PPK UI, so do not equate this partial raw integral with the full UI total.

Deployment evidence: `ota-upload.jsonl`, `ota-configuration.jsonl`, and `persistence.jsonl` in the artifact directory. The last script disconnected normally. PPK was left at 3000 mV, output enabled, sampling stopped, with a one-hour / 100 Hz capture selected.

## Hardware validation remaining

1. For the user's hour-long PPK run, disconnect BLE clients and the debugger and leave the input at 3.0 V. Turn output off, start capture, then enable power, as before. Integrate complete wake-to-wake cycles so a final extra wake is not counted as a full extra period. Compare charge per event, sleep current, cadence, and reset/retry activity with the original recording.
2. A scope at module VDD is required to evaluate ripple and transients during Auto-mode radio. Packet reception, sensor validity, and OTA operation establish functional evidence only.
3. Low-voltage testing is separate: use the PPK at progressively lower inputs, establish regulated rail and repeatable successful cycles, and observe whether undervoltage enters the intended backoff. Battery tests must subsequently establish the selected cell's pulse sag, usable capacity, and restart behavior. No claim of successful 0.8 V hardware operation follows from host tests.

Sources: [nPM2100 datasheet](https://www.nordicsemi.com/Products/nPM2100/Documentation), [Ezurio BL54L15 supply specification](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series), and [Nordic nPM2100/PPK FAQ](https://devzone.nordicsemi.com/nordic/nordic-blog/b/blog/posts/frequently-asked-questions-for-the-npm2100-pmic).
