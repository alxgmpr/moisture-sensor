# bthome-sensor

BTHome v2 BLE beacon for the **nRF54L15 DK (PCA10156)**, NCS v3.2.2. Advertises
five simulated soil-sensor values — battery, temperature, humidity, and two
moisture readings — over standard BTHome v2 service data, which Home
Assistant's Bluetooth integration is designed to pick up automatically as one
device with five entities. It runs the real product cycle end to end; only
the sensor read is faked, since our own board and sensors are not built yet.

Console-verified: the cycle, the payload bytes, the stable BLE identity across
resets, and moisture reading above moisture_2 on the wire, all as designed.
**Actual discovery in Home Assistant has not yet been verified** — that check
needs a human watching the HA integration over several cycles. See
[NEXT-STEPS.md](../../NEXT-STEPS.md) ("BTHome firmware on the DK") for the
current status of that check.

Design and rationale: [docs/superpowers/specs/2026-08-04-bthome-firmware-design.md](../../docs/superpowers/specs/2026-08-04-bthome-firmware-design.md).
This README covers how to build, run and verify it; the design doc covers why
it is built this way.

## The cycle

One cold boot is one cycle. Waking from System OFF resets the chip, so there
is no loop and no state carried between wakes — everything needed is either a
pure function of elapsed time or re-derived from the chip itself:

1. **Escape check.** If Button 0 is held at boot, stay awake indefinitely so
   the board can be flashed (see below).
2. **Watchdog armed.** Covers a hang while the radio is up; halted implicitly
   by System OFF removing its power, not by anything the firmware does at
   sleep time.
3. **Read the clock.** GRTC SYSCOUNTER, which survives System OFF, gives
   elapsed time since first power-on.
4. **Generate values.** A simulated drying curve, a pure function of that
   elapsed time.
5. **Encode.** `bthome_encode()` fills a 17-byte BTHome v2 payload.
6. **Advertise.** Non-connectable, for `CONFIG_SENSOR_ADV_WINDOW_MS`
   (2000 ms by default).
7. **Sleep.** Drain the console, arm the GRTC wake alarm, `sys_poweroff()`. Order
   matters here: `z_nrf_grtc_wakeup_prepare()` disables every other GRTC
   channel and expects `sys_poweroff()` to follow immediately, so any kernel
   timer activity after the arm (even a `k_msleep()`) runs through the
   channels it just cleared and undoes it — the device never wakes. See the
   comment in `sleep_until_next_cycle()` in `src/main.c`.

The product default is an hourly cycle (`CONFIG_SENSOR_CYCLE_SECONDS=3600`).
`dev.conf` overrides that to 30 seconds so a full cycle can be watched without
waiting an hour — see Building below.

## Building

Built in the `ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2` container against
`nrf54l15dk/nrf54l15/cpuapp`.

**Product default (hourly cycle, what ships):**

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

**Dev build (30 s cycle, for watching it work without waiting an hour):**

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor -- -DEXTRA_CONF_FILE=dev.conf && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

Either way, confirm the console reports the cycle length you expect
(`sleeping 3600 s` or `sleeping 30 s`) — it is easy to flash the wrong variant
and not notice for an hour.

## Flashing

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

**The device is in System OFF most of the time and does not answer the
debugger then.** Flash promptly after a reset (or while holding the escape
button, see below), and retry on failure — a timing-out `nrfutil` call usually
just means the board went back to sleep first. If it gets stuck, recover with:

```bash
nrfutil device recover --serial-number 1057774579
```

## Console

The console is **VCOM1**, `/dev/cu.usbmodem0010577745793` at 115200 8N1.
VCOM0 is silent and looks identical to a dead board — if nothing is printing,
check which VCOM the terminal is attached to before suspecting the firmware.

## The escape hatch

Hold **Button 0** and press RESET. The firmware is written to print a notice
and idle forever instead of running a cycle, keeping the board reachable for
flashing. **This has not yet been verified on hardware** — only the
console-observed behaviors above (cycles repeating, payload bytes, stable BLE
identity, elapsed climbing across System OFF) have. See
[NEXT-STEPS.md](../../NEXT-STEPS.md) ("BTHome firmware on the DK") for the
current status of that check.

Without it, a one-hour (or even 30-second) cycle leaves a very small window to
flash into before the device drops into System OFF and stops answering the
debugger.

DK-only: our own board carries no button, and needs no equivalent — with a
debugger attached it runs in Debug Interface mode, which emulates System OFF
rather than entering it, so the board stays reachable regardless.

## Host tests

The BTHome encoder (`src/bthome.c`, `src/bthome.h`) has no Zephyr dependency
by design, so its tests run on the host with the system `cc` — no container,
no board, under a second:

```bash
./tests/bthome/run.sh
```

Covers the golden byte vector, negative temperature as two's-complement
`sint16`, the SENSE1-before-SENSE2 ordering, and buffer/argument validation.

## Packet layout

22 of 31 available advertising bytes. The remaining 9 are exactly consumed by
the `BT_DATA_NAME_COMPLETE` element carrying `"Plant-1"` — the advertisement
is full, and the 7-character `SENSOR_DEVICE_NAME` limit has no headroom (see
the design doc for the byte accounting).

```
02 01 06                          Flags: LE General Discoverable, no BR/EDR
12 16 D2 FC 40                    Service Data, UUID 0xFCD2, BTHome v2 unencrypted
   01 <bat>                       battery      uint8   %
   02 <lo> <hi>                   temperature  sint16  ×0.01 °C
   03 <lo> <hi>                   humidity     uint16  ×0.01 %
   14 <lo> <hi>                   moisture     uint16  ×0.01 %   ← SENSE1
   14 <lo> <hi>                   moisture_2   uint16  ×0.01 %   ← SENSE2
```

The service-data payload itself (`BTHOME_ADV_DATA_LEN`, 17 bytes: UUID + device
info + five measurements) is what `bthome_encode()` produces; the AD wrapping
around it is the Bluetooth stack's job.

**Measurement order is load-bearing.** Both `0x14` moisture entries must be
emitted SENSE1-then-SENSE2 on every single advertisement. Home Assistant
assigns the `_2` suffix *positionally* — by which `0x14` object shows up
second in the payload — not by any field inside it. Swap the order, even once,
and SENSE2's reading silently rebinds to the `moisture` entity with no error
raised anywhere. This is why the encoder's host tests pin the byte offsets of
each field directly (`test_moisture_order` in `tests/bthome/test_bthome.c`),
and why it is worth re-checking against a live Home Assistant instance after
any change near the encoder: `moisture` should read a few points above
`moisture_2`, not the reverse.

## What is stubbed

Battery, temperature, humidity and both moisture values are a simulated
drying curve, a pure function of elapsed time — not real sensor reads. See
[NEXT-STEPS.md](../../NEXT-STEPS.md) for what real hardware needs before that
changes.

The simulated battery declines monotonically from 100% and never resets — it
is driven off GRTC elapsed time, which survives even a chip erase. After
roughly 49.5 hours of accumulated DK uptime it pins at 1% permanently, while
the moisture curve keeps cycling every 6 hours as usual. That is expected
behavior of the stub, not a fault — worth knowing before a future Home
Assistant demo makes it look like a dead cell.
