# Low-voltage investigation — Soil 1

Production wrap-up is recorded below. Original application 0.2.11 and rollback artifacts are preserved. Earlier diagnostic results and temporary settings are distinguished from the final production state.

## Evidence correction — 2026-09-22

The user found PPK output OFF after the previous investigation. Claims of failed Hibernate/GRTC recovery, absent scheduled activity, and SWD No ACK are not established device failures until repeated with verified power. Supply-command logs alone do not prove DUT power. Powered revalidation evidence is in `output/low-voltage-2026-09-22/`. A fresh Nordic-enabled 3.0 V baseline returned confirmed app 0.2.19, valid sensing, preserved temporary settings and PMIC ADC 2987 mV. Production 0.2.25 was subsequently installed and confirmed; see the final verification section below. Two controlled tests now reproduce DUT disconnect when the PPK serial port closes, including a bare `ser.close()` with no intervening power command. Explicit source re-enable restores a fresh successful boot. Keep the serial connection open through recovery trials; commanding ON before closing it does not leave verified power.

## Powered watchdog validation — 2026-09-22

With diagnostic app 0.2.19, 60-second backoff, and a temporary 20-second advertising window, both injected watchdog paths recovered while the same PPK serial connection remained open at commanded 3.0 V. Each injection had a valid precondition status with PMIC ADC 2962 mV and the exact saved configuration.

- MCU watchdog: a bounded busy wait with interrupts masked caused watchdog recovery through Hibernate; the recovered status reported PMIC reason 16 and retained stage 0xe1, valid sensing at 2950 mV, and unchanged settings. Current activity ended around 16 seconds and restarted around 77 seconds.
- PMIC watchdog: the debugger halted the CPU, with the MCU watchdog configured to pause during debug halt. The recovered status reported PMIC reason 16 and retained stage 0xe2, valid sensing at 2962 mV, and unchanged settings.

Evidence: `output/low-voltage-2026-09-22/watchdogs-run2.jsonl`, `watchdogmcu-3000-1790092501.serial`, and `watchdogpmic-3000-1790092648.serial`. Both traces decoded without sequence discontinuities. These are single trials of each injected mechanism, not repeated low-voltage or production-build qualification. The first injection attempt failed before modifying CPU registers because the script did not wait for halt completion; it is excluded from the successful trials. These watchdog trials preceded the final production deployment.

## Production wrap-up decision — 2026-09-22

The user requested that the investigation be wrapped up with documented evidence and finished device firmware, rather than extending the characterization campaign. Production application 0.2.25 and its matching early boot guard select **1800 mV cutoff, 2000 mV recovery, and 3600-second undervoltage retries**. Deployment and final verification are recorded separately; this section describes the selected build and is not itself proof of installation.

This is a conservative operating policy, not a claim that the hardware cannot operate below 1.8 V. Powered diagnostic cold starts and three fresh samples passed twice at commanded 1.6 V. At 1.45 V, one trial entered backoff and another passed three samples. Trials at 1.425 V entered backoff twice; one 1.4 V trial also entered backoff. Every completed refinement trial recovered at 3.0 V with preserved settings. Quiet portions of the first 1.45/1.425/1.4 V recordings averaged approximately 0.58–0.67 µA on the PPK.

Conversely, warm downward transitions disconnected at commanded 1.6 V, including a 25 mV ramp after a valid response at 1.625 V (PMIC reading 1650 mV). Subsequent Hibernate recovery at commanded 1.8 V was verified with PMIC reason16/prior0xd0, followed by a normal scheduled wake at 3.0 V. The initial transition mechanism remains unresolved. The production 1800 mV ADC threshold is 150 mV above that last reported 1650 mV reading; conservatively allowing 64 mV ADC uncertainty plus 12.5 mV quantization leaves approximately 74 mV of additional margin. This is an engineering margin around the observed transition region, not a measured guarantee against rail sag. Recovery hysteresis is 200 mV. PPK setpoints are not interchangeable with ADC thresholds.

The software defects established by inspection are late undervoltage handling, immediate reboot paths on early errors, and a bootloader UART pin conflict. A prior low-input debugger snapshot also showed execution in RSA verification before application policy. The changes move voltage gating before expensive boot verification, retain interrupted-attempt state in the PMIC, remove immediate error reboots, add independent watchdog/backoff paths, and disable the conflicting UART. The final build also preserves an already-recorded failure stage rather than replacing it with generic backoff stage 84.

The final one-hour retry interval will be checked in application and bootloader build configurations; a full one-hour timed recovery is not part of the shortened wrap-up. Timed Hibernate recovery and both watchdog origins were validated using 60-second diagnostic retries. Operation on a depleted CR2032, rail transients, temperature and unit variation remain unqualified. Firmware cannot guarantee quiet shutdown on a deeply depleted cold input that cannot execute the early guard; prior 0.8 V cold tests did not establish backoff. Guaranteeing that condition would require a hardware undervoltage disconnect or qualified external wake circuit.

## Provisional prior bench findings

The original voltage check was too late: settings initialization and PMIC transactions preceded it, and several early I2C/shutdown errors explicitly rebooted. At 0.825 V a debugger snapshot located execution in MCUboot RSA verification (`mbedtls_mpi_core_mla`, PC 0x666e, VTOR 0), before application policy. Sustained input current and absent BLE at 0.800–0.825 V are failed conditions, but do not identify the exact rail transient or prove each pulse is a reset. The Nordic hwinfo implementation does not report POR/BOR here; reset-cause zero is not conclusive evidence of brownout.

The original MCUboot also enabled UART20 on P1.4/P1.5, the board's FDC I2C pins. These pins have external 4.7 kΩ pullups to the switched sensor supply. Disabling the UART removes that conflict, but the comparison did not eliminate low-voltage failures. No sensor-rail backfeed or voltage transient was measured.

| Test, diagnostic 0.2.17 | Evidence/result |
|---|---|
| Cold starts, original MCUboot | 3.0 and 2.0 V passed; repeated 1.0 and 0.9 V passed in this series. 0.875 and 0.850 V failed BLE twice each; 0.825 twice and 0.800 failed. |
| UART-disabled bootloader comparison | 3.0 V passed; 0.875 V passed once, 0.900 V passed once and failed once. 0.850/0.825/0.800 V failed. The lower boundary is intermittent. |
| Connected sensing/advertising | Three fresh samples each at 2.0, 1.6, 1.5, 1.4, 1.2, 1.0, 0.9, 1.4 and 1.0 V passed (27 requests). |
| Abrupt 2.0→1.4 V transition | One disconnect; separate steady 1.4 V tests passed twice. This remains a transition failure. |
| Scheduled wake at 1.0 V | Startup and +60-second advertisements captured. |
| 0.850 V followed by 3.0 V without power cycle | Quiet interval followed by scheduled wake; RESET_CLOCK=2048, previous stage83. This was timed sleep, not a demonstrated reset loop. |
| 0.825/0.800 V followed by 3.0 V | Fresh startup within seconds; application retained stage0. |

Failures were bounded to 12 seconds in the refined sweeps, followed by restoration to 3.0 V. Cold trials used 10 seconds of input power-off. Debugger wiring remained connected, so final clean-power validation must distinguish that condition. The single earlier 2.0 V scheduled-wake capture with no BLE is not counted as a pass.

## Earlier diagnostic policy (superseded for production)

The earlier diagnostic policy used 1400 mV PMIC-ADC cutoff and 1600 mV recovery, with a proposed 3600-second production retry. Production now selects the more conservative 1800/2000 mV thresholds below. The 200 mV hysteresis exceeds ADC quantization and avoids repeated attempts near the boundary. The cutoff also leaves margin above the datasheet's 1.25 V lower end of the fully specified HP operating range, rather than targeting its advertised 0.8 V loaded cold-start limit. Conservatively allowing 64 mV for the ADC's ±2% specification as a full-scale bound plus 12.5 mV quantization still leaves roughly 74 mV above 1.25 V. PPK setpoint and PMIC readings differ; thresholds are ADC values, not calibrated PPK setpoints.

MCUboot's early gate runs before hashing/RSA/swapping, disables the conflicting UART, and uses a retained BOOTING marker plus a 60-second PMIC watchdog. The application checks before settings and expensive work and marks ATTEMPT/CLEAN. BLOCKED survives MCU reset and PMIC watchdog power cycling in SCRATCHA while VBAT remains above its retention threshold. Undervoltage or interrupted work enters PMIC Hibernate with a verified timer; I2C failure falls back to timed System OFF. No I2C, logging or kernel timeouts follow GRTC wake preparation. If timed wake preparation itself fails, stay off pending external wake instead of rebooting repeatedly.

This requires enough power to execute the early gate and communicate with the PMIC. Firmware cannot guarantee protection below that hardware execution limit.

## Evidence and preservation

Raw captures, calibration, decoded summaries and JSONL BLE/status logs are in `output/low-voltage-2026-09-21/`. Key series: `cold17`, `fixed17`, `low-recovery17`, `low-swd17`, `wake17`, `uartcold17`. Debugger full RRAM, settings, UICR and RAM backups were taken before programming. Bootloader-only programming keeps both application slots and settings intact; `boot-program-1790051932/verified.json` records readback and preservation checks. Existing recordings were saved before new measurements.

Signed application artifacts and source snapshots are in each `output/firmware-0.2.xx/` directory. The original RSA trust key, partition layout, calibration endpoints, BLE identity and saved configuration are preserved. Existing unrelated PCB and firmware workspace changes were not reverted.

No oscilloscope was available. PPK current traces and the PMIC ADC cannot establish MCU rail ripple, brownout transients, or depleted-CR2032 resistance/sag behavior. Bench thresholds require separate battery, temperature and unit-to-unit qualification before being treated as battery-qualified limits.

## Guard validation to date

At 1.300 and 1.000 V, the early guard established Hibernate. Raising input to 3.0 V after 12 seconds did not cause immediate startup: recovery occurred around 65–66 seconds after initial power-on. PMIC reset byte16 identifies timer wake from Hibernate; previous stage0xd0 identifies the early undervoltage gate. Valid sensing and the exact saved configuration were read after recovery. At 1.3 V, the input-current mean during seconds2–10 was approximately0.61 µA; this is a PPK bench observation with debugger wiring present.

At 0.800 V, both new-guard trials still consumed sustained mA-level input current and recovered shortly after restoring3.0 V with PMIC reset0/previous stage0. Thus the early gate did **not** establish backoff at that cold-start condition. Do not label these successful guarded recoveries merely because BLE returned after voltage restoration.

The PMIC wake timer automatically becomes a10-second boot monitor on Hibernate exit. Its watchdog actions are reset or power cycle, not a configurable return-to-Hibernate action. Its programmable VBATMIN thresholds regulate allowed battery draw; they are not documented as a voltage-triggered latched Hibernate mechanism. See the [official Zephyr nPM2100 VBAT binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/sensor/nordic,npm2100-vbat.html) and nPM2100 datasheet sections6.1.6,7.2. This does not guarantee protection when a fresh/deeply depleted supply cannot execute the early gate. A hardware undervoltage disconnect or externally qualified wake circuit would be needed for that guarantee; disabling the boot monitor alone is not a safe substitute.

One hysteresis trial stayed quiet at1.5 V and showed startup/activity at the second timed wake after restoration to1.8 V, but BLE recovery timed out. It remains inconclusive pending debugger-disconnected repeat. The activity waveform alone is not proof of successful advertising.

## Final production verification

Application **0.2.25** is active and MCUboot-confirmed with image digest `6aec2339873fab22ab24624246ad1993f44940d3fe347191b462b9db390d5d13`. The production bootloader readback matches SHA-256 `b2c3b0a095c4bb480f93f3b8d513d341dace655933f78ed033a5c8be76f396cb`; its update preserved settings, UICR and application-slot boundaries. Evidence: `output/low-voltage-2026-09-22/boot25-1790094092/verified.json` and `deploy25-run4.jsonl`.

`final25-checks.jsonl` and `final25-checks-run2.jsonl` verify exact original production configuration: Soil 1 identity/name, calibration endpoints 2655/5658 and 2618/5571 fF, 900/3600-second measurement periods, 2500 mV slow-schedule threshold, 5000 ms advertising window and 500 ms advertising interval. Production sensing passed at commanded 3.0 V (ADC 2950–2962 mV) and 2.0 V (ADC 1975 mV). Both application and bootloader configurations specify 3600-second undervoltage retry. The new application completed a scheduled wake while temporary 60-second settings were still active before restoration.

The production cutoff trial dropped from commanded 2.0 V to 1.7 V. BLE disconnected and the saved trace averaged 0.521 µA during seconds 2–10, with no 10 ms bin above 100 µA and no sample-counter discontinuities in that interval (`finalpolicy-quiet.json`). Restoration to 3.0 V was observed for 10 seconds, not a full hourly retry. A 20-second off/on did not establish recovery; retained Hibernate state is a possible explanation, not proven by missing BLE alone. A 120-second off interval then produced a successful cold recovery, confirmed image and exact production settings (`final25-recover.jsonl`).

Firmware artifacts, signatures, exact source archive, build settings, tests and corrected OTA package are under `output/firmware-0.2.25/`. The first generated ZIP contained stale 0.2.21 metadata while its signed image was 0.2.25; only that metadata was corrected, and the resulting package passed the DFU validator. Signed firmware bytes were not changed by that correction.

Operational limitation: recovery after undervoltage can take up to one hour after voltage returns above 2.0 V. A brief battery/input interruption may retain the PMIC's blocked state. This is intentional backoff, not an immediate-wake guarantee.

**Final state verified at 10:32 local on September 22:** Nordic Power Profiler has PPK2 F6CD1618AFA2 selected, Source meter mode, 3000 mV, and Enable power output checked. A separate BLE read after Nordic enabled output returned PMIC ADC 2950 mV, application 0.2.25 active/confirmed with the expected digest, valid sensing and the exact original production settings (`nordic-final-verified.jsonl`). Nordic remains connected; no scripted supply controller remains. The visible Nordic graph is the earlier stopped recording, not a claimed live final trace. Final scripted recordings were saved separately.

The selected production cutoff is conservative. The exact electrical source of the 1.6 V transition disconnect remains unresolved, and the full one-hour retry and depleted-cell behavior remain unqualified. No rail-transient measurements are claimed. These limitations were retained when the user requested the shortened production wrap-up.
