# BTHome recovery regression — 2026-09-22

## Report and reproduced observations

Soil 1 on 0.2.25 stopped updating Home Assistant after input tests at 1.0–2.0 V, despite restoring the PPK source to 3.0 V. Nordic's log records mostly 2–8-second output interruptions during these tests. The source was enabled when this investigation began. The existing 30-hour, 10 samples/s Nordic recording was left running; a raw prefix was copied before changes.

Firmware 0.2.25 deliberately slept for **3600 seconds after undervoltage or interrupted startup**, in both MCUboot and the application. Raising the input voltage did not cancel that timer. This couples fault recovery to an unnecessarily long delay. A brief power interruption is not a reliable way to clear PMIC retention. The initial quiet recording alone does not identify a reset cause.

A longer off interval (10:56:34–11:00:53 local) was tried. The first captured BTHome payload occurred around a subsequent SWD attachment, so this trial **does not prove autonomous cold-start recovery**. SWD attachment wakes the MCU from System OFF and changes the experiment. No output-rail or capacitor-discharge transient was measured.

Home Assistant subsequently displayed a fresh humidity reading, and a BLE read of 0.2.25 showed the original production settings, valid sensors, no storage error, and previous completed stage 83. A temporary 60-second measurement schedule then produced a normal GRTC wake (reset cause 2048), without debugger intervention. Evidence is in `output/bthome-regression-2026-09-22/`.

## Repair

0.2.27 changes both fault retry intervals from 3600 to 60 seconds. This is independent of the normal 900-second measurement and 3600-second low-battery measurement intervals. Each undervoltage retry runs the existing early MCUboot voltage gate before image hashing/signature verification, sensors, or BLE. Below recovery voltage it returns to PMIC Hibernate. It does not write settings flash on each retry.

The existing ADC cutoff/recovery remain 1800/2000 mV. These are conservative bench thresholds; this repair does not establish the lowest usable CR2032 endpoint. Prior lower-voltage trials and limitations remain in `low-voltage-investigation-2026-09-21.md`. A stiff PPK source does not qualify a depleted coin cell's resistance, sag, temperature behavior, or usable capacity. More frequent guarded retries consume more energy than hourly retries; the tradeoff is prompt recovery when useful power returns.

The bootloader is updated by SWD because application OTA does not update the early boot gate. The application uses the existing signed OTA path. Partition layout, signing trust, device identity, calibration, and user settings are preserved. Bootloader readback and before/after protected-region hashes are recorded. 0.2.25 remains an archived rollback artifact.

## Validation

Build and host tests, partition/package checks, and RSA signature validation passed. The OTA image is active and confirmed with digest `14bdbab84791fb412280e0c237efc6467f612b5c5aad33588c96bf8a4cea811f`; 0.2.25 is in the secondary slot. The first post-OTA scan timed out, but a subsequent diagnostic read verified the new image had already completed a cycle and confirmed itself. That diagnostic reset is not counted as autonomous recovery.

At 11:09:17.543 local, Nordic changed the source from 3000 to 1700 mV while BLE was connected. The connection dropped within about one second. The source remained at 1700 mV for 84.975 seconds, spanning a guarded retry. At 11:10:42.518 it returned to 3000 mV. Fresh BTHome data appeared at 11:11:22.590 (40.072 seconds later). No SWD, reset command, or power cycle occurred during recovery. Status readback reported 2962 mV, PMIC wake reason 16, previous stage 0xd0, no sensing/storage errors, and unchanged calibration/name. See `recovery27.jsonl`.

The running Nordic 10 Hz recording was preserved as a second raw prefix. It is insufficient for rail-transient claims or precise radio-pulse characterization. The next scheduled wake at 11:12:26 reported reset cause 2048 (GRTC), previous completed stage 83, valid measurements, and unchanged settings. This used a temporary 60-second measurement interval to exercise the same wake path. The full 15-minute/hourly wall-clock intervals were not re-run in this repair session. Final production restoration is recorded separately in `finish27.jsonl`.

Home Assistant displayed 40.76% humidity from 0.2.27 before the undervoltage test (matching the BLE payload). The browser frontend subsequently showed a blank page after refresh; this does not invalidate the captured firmware recovery packets, but final post-recovery UI confirmation is tracked separately.


## Final handoff

0.2.27 is active and confirmed. `final_verify27.jsonl` verifies the original full production configuration after a debugger-requested reboot: Soil 1 identity, calibration 2655/5658 and 2618/5571 fF, 900/3600-second schedule, 2500 mV low-battery cadence threshold, 5000 ms advertising window, 500 ms advertising interval, and 300-second connected-session limit. ADC input was 2962 mV at the 3000 mV PPK setting. Sensing and storage errors were zero. A final SMP reset was allowed to disconnect the target itself, rather than immediately closing the client connection.

The first finalization script's post-reset reconnection timed out/could not complete; its restored settings were subsequently verified by a fresh connection after SWD reset. Do not count this as an autonomous cold-start pass. Likewise, this session does not establish why every brief PPK interruption failed to produce an immediate boot; retained power and debugger influence have not been measured electrically. The demonstrated fix is bounded automatic undervoltage recovery, not a guarantee that every short output toggle physically cold-resets the board.

Nordic remains connected in Source mode at 3000 mV with output enabled and the user's recording still running. No serial-port controller was opened during this repair. Recording prefixes and logs are preserved alongside the evidence. The original 0.2.25 artifacts and protected-region backups remain available. No unrelated PCB changes were altered.

Remaining limits: single-board bench test, no depleted-CR2032 qualification, no output-rail transient instrument, no new minimum-voltage sweep, and no full 15-minute/hourly duration run in this repair. Home Assistant received 0.2.27 before the final undervoltage test; its blank frontend after refresh prevented a final post-recovery UI confirmation. BTHome packets and autonomous recovery were captured independently. A lower cutoff should only follow battery/sag qualification, not the PMIC's advertised 0.8 V startup figure.
