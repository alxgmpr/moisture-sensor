# Firmware power audit and browser configuration

## Findings in the previous 0.2.5 image

The largest demonstrated waste is the development cadence. It held a fresh
sample in advertising for **300 seconds**, then slept **60 seconds**. The
measurement-to-measurement interval was therefore about six minutes, not one
minute. The preceding hardware log measured 364.83 seconds between cycle starts.
Every window transmitted the same reading with no benefit from fresher data.

The radio used `BT_GAP_ADV_FAST_INT_MIN_2/MAX_2`, 100–150 ms in the pinned SDK.
Depending on controller interval choice, a five-minute window requests roughly
1,900–2,900 events, each potentially transmitting on three primary channels.
The firmware allowed any connected client to keep the device awake indefinitely.
The foreground loop woke every 50 ms although watchdog service was needed only
once per second. Name, cadence and calibration were compile-time settings.

Existing good behavior is preserved: FDC single-shot conversions, dedicated
runtime-suspended FDC I2C pins, the sensor rail off during advertising, no SHT
heater, a fixed 2.2 V cutoff, low-battery backoff, bounded I2C and conversion
waits, independent watchdog protection, and GRTC System OFF between cycles.
These are code behaviors, not a measurement of quiescent current.

## Implemented in 0.2.9

| Setting | Old development | Old production | New development defaults | New production defaults |
| --- | --- | --- | --- | --- |
| Measurement cadence | ~360 s + boot/sense | ~910 s + boot/sense | ~60 s | ~900 s |
| Advertising window | 300 s | 10 s | 30 s | 10 s |
| Event spacing | 100–150 ms | 100–150 ms | 1000 ms | 1000 ms |
| Connected session | Unbounded | Unbounded | 300 s maximum | 300 s maximum |
| Foreground idle wait | 50 ms | 50 ms | Up to 1000 ms, event driven | Up to 1000 ms, event driven |

Cadence now subtracts this boot's uptime before scheduling System OFF. It excludes
MCUboot/pre-kernel time and rounds to seconds, so it is not a precision clock.
If an interactive session overruns a period, it sleeps a full period rather
than immediately taking another measurement. The low-battery interval follows
the same policy. A disconnect ends an established normal-mode session; normal
mode does not reopen a perpetual connectable window.

At 1000 ms plus a mean 5 ms BLE random delay, new production requests about
10 events/wake × 96 wakes/day = **955 advertising events/day**. The former
production profile requested roughly **6,100–9,000/day** (interval selection
and boot time affect the result), so this is about **84–89% fewer events**.
Against the old development schedule's ~465,000–686,000/day it is about
**99.8% fewer**. These are schedule calculations, not captured packet counts,
receiver delivery guarantees, battery capacity estimates or lifetime claims.
The dashboard shows the same model, with an explicitly assumed 125 ms midpoint
for comparison to the old development image.

The new development profile still spends half its time in the radio window and
samples much more often than before. It is useful for configuration/bench work,
not a battery-life profile. Persisted settings override either build profile.

The [local dashboard](../firmware/sensor/dashboard/README.md) edits
measurement and low-battery intervals, window length, event spacing, connection
limit, name, and both dry/wet calibration pairs. It can request a sample, show
raw fF and CAPDAC, and capture an endpoint. Browser writes are chunked, checked,
and committed as one CRC-protected record. The browser waits for a successful
storage readback before reporting success. Full-chip erase still removes data.
Both firmware slots keep their deployed addresses and sizes; the former 4 KB
tail gap holds two logical ZMS sectors. There are no per-measurement writes.

Disabling calibrated publication omits the moisture objects, while retaining
valid battery, temperature, humidity and diagnostic objects. Failed measurements
still do not turn into zero-valued sensor readings. Existing provisional
calibration remains the default; changing firmware is no longer necessary to
replace those endpoints.

## Remaining opportunities, ordered by measurement value

1. **Measure forced-HP radio-window overhead.** The PMIC remains in forced HP
   even between one-second advertising events. This may dominate any savings
   from packet reduction. Evaluate automatic/ULP operation during radio only
   with a scope and battery-side power trace; preserve peak-voltage margin and
   watchdog recovery. No speculative PMIC mode change is included.
2. **Qualify receiver delivery before cutting repetitions further.** Measure
   BTHome discovery/update rates at the intended Home Assistant receiver and
   distances, including packet loss, active scans and coexistence. A five-event
   minimum is a configuration guard, not proof that five events are enough.
3. **Measure boot cost and System OFF current.** MCUboot runs every sample.
   Compare charge/boot and sleep current against System ON RTC idle at realistic
   cadences. Include boost quiescent current, GRTC, module clocks, leakage and
   probe disconnection. Keep debugger and UART detached during final traces.
4. **Optimize conversions only after radio/power data.** FDC currently polls DONE
   at 1 ms and starts CAPDAC at zero for each channel; high capacitance can require
   several conversions. Saved/cached CAPDAC guesses or a timed wait may reduce
   work, but need range and settling validation. Typical recent samples used
   CAPDAC 0, so this is currently a smaller opportunity. SHT high-precision
   measurement is already a single shot without heater.
5. **Commissioning and ownership.** The board currently permits open SMP and
   configuration connections. Add a deliberate ownership/pairing strategy for
   field use. Browser permission is not sensor-side authorization. A wake button
   or authenticated commissioning window could also improve discovery without
   lengthening every advertising window; no hardware changes are made here.

## Bench acceptance record to collect

Use the same cell-equivalent supply and receiver for old/new traces. Capture
battery-side charge per full cycle, resting and loaded voltage, peak current,
System OFF current, and boost/rail settling. Estimate average current as
`(Q_boot + Q_sense + Q_window + I_sleep × T_sleep) / T_cycle`, with consistent
units and energy-conversion losses included. CR2032 loaded capacity and pulse
limits must be measured before estimating life from nominal capacity.

For persistence: save nondefault endpoints/name, disconnect, reconnect after
GRTC wake, remove/reinsert the battery, and compare settings each time. Interrupt
chunk upload, interrupt an accepted commit, and verify either the previous or
new complete record survives. Exercise full-sector recycling and unchanged saves.
For sessions: test expiry, a lost browser, disconnect before window end, low
battery during Measure now, and a signed SMP upload/test/rollback. Confirm the
bootloader and slot layout remain compatible with the deployed image.

## Sources

- Repository `src/main.c`, `src/sensor.c`, `Kconfig`, `dev.conf`, and pinned NCS
  v3.2.2 Bluetooth/GRTC/RRAM/ZMS sources.
- [Previous hardware observation](timeout-investigation-2026-09-21.md).
- [Zephyr ZMS design](https://docs.zephyrproject.org/latest/services/storage/zms/zms.html).
- [Chrome Web Bluetooth](https://developer.chrome.com/docs/capabilities/bluetooth).
- [Reference Telink tool](https://pvvx.github.io/ATC_MiThermometer/TelinkMiFlasher.html).
  We reuse the browser-to-BLE configuration approach; this Nordic board continues
  to use its existing MCUboot/SMP firmware update path, not Telink commands.

## Validation completed on 2026-09-21

- Production 0.2.9, development 0.2.9 and maintenance 0.2.10 build with the pinned
  NCS v3.2.2 toolchain, `--sysbuild`, and the deployed DK base target plus the
  sensor overlay. All three generated partition maps preserve the deployed
  bootloader, application budget and primary/secondary slots. The partition
  validator catches an SDK-generated extra ZMS reservation; the final build
  explicitly names the tail reservation `zms_storage` to prevent it.
- All three DFU packages pass the header, slot, version, image-digest and
  RSA-2048/SHA-256 format checks. The deployed production binary also passes
  cryptographic signature verification with the existing prototype key.
- Sensor fault-injection tests, BTHome payload tests, new configuration tests,
  and six browser protocol tests pass, including an undefined-behavior sanitizer
  run. The browser encoder is compared byte-for-byte with the actual compiled
  C encoder. An AddressSanitizer run stalled before test output and was stopped;
  no ASan success is claimed.
- Desktop and narrow-layout browser previews were inspected. Demo presets and
  save confirmation work; at 375 CSS pixels the document has no horizontal
  overflow. Actual Chrome Bluetooth-chooser automation failed at the native UI
  layer; the complete browser-to-hardware click path is not qualified by this
  session. Direct BLE protocol checks are distinguished below.
- Soil-402A accepted an OTA test image from its confirmed 0.2.5 installation.
  The initial 0.2.7 integration build exposed the new configuration service.
  A partial write/commit was rejected without changing live configuration.
  A complete 64-byte record was committed, read back and marked persisted.
  A manual sample succeeded, with valid raw measurements and no sample error.
- A later cold boot read the identical settings, persisted flag set and the
  per-boot save count reset to zero. MCUboot reported the integration image
  confirmed. Some short scan/connection attempts missed radio windows; a
  debugger attachment was used during diagnosis and can itself wake System OFF.
  This is persistence evidence, not an uninterrupted timing/power measurement.
- The final **production 0.2.9 image** was uploaded over SMP, tested and observed
  active and confirmed. Its image hash is
  `349afcea87d94db3b57be2a241aa42bddcf6f1515efc6ed65046cf326007013c`.
  Its first checked cold boot retained the exact configuration saved by 0.2.7,
  demonstrating compatible persistence across this OTA update. No bootloader
  programming or full-chip erase was performed.

Builds, signed images, protocol validation scripts, image-state responses,
configuration records and hardware logs are under `output/firmware-0.2.9/`
(ignored by Git); initial integration evidence is in `output/firmware-0.2.7/`.
The current key is still the pre-existing SDK development key. Field release
requires the existing production-key process.

Battery removal, interrupted physical storage writes, sector wear/garbage
collection endurance, deliberate OTA rollback, connection-deadline expiry,
receiver delivery statistics and measured power consumption remain unqualified.

The final on-device configuration was saved and read back again after a cold
boot: normal interval **900 s**, low-battery interval **3600 s**, window
**10000 ms**, spacing **1000 ms**, connection limit **300 s**, and low-battery
threshold **2500 mV**. The default chip name and all four calibration endpoints
were preserved. The final read reported firmware **0.2.9**, persisted settings,
a reset save counter, valid sensor data, and zero sample/storage errors. The
client disconnected and the device was left to sleep. This final reconnection
used a read-only debugger attachment to wake the sensor after a short-window
connection attempt failed; it does not qualify a complete 15-minute autonomous
cycle or measure sleep current.
