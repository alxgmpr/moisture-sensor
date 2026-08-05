# BTHome firmware on the nRF54L15 DK — design

**Date:** 2026-08-04
**Status:** approved, ready for planning
**Target:** nRF54L15 DK (PCA10156), NCS v3.2.2

Firmware that advertises simulated soil-moisture data as BTHome v2 beacons and
appears in Home Assistant as five entities. It runs the real product cycle —
wake, read, advertise, System OFF — with only the sensor read faked.

## Why this now

The DK pin-assignment work is closed out (see [NEXT-STEPS.md](../../../NEXT-STEPS.md)),
and everything else in bring-up is blocked on the nPM1300 EK. This is the
largest remaining piece of work that needs no hardware we do not have.

BTHome is not a new choice. [HARDWARE.md §5](../../../HARDWARE.md) already
assumes it: the nPM1300 fuel gauge is described as "a straight upgrade" *for
BTHome battery reporting*.

**This is not power work.** [HARDWARE.md §7](../../../HARDWARE.md) puts the
entire hourly wake cycle at 3 mAh/yr — 1.8% of budget — and assumption 4 says
it is "a composite estimate, not measured. At 0.6% of budget, being wrong by 5×
changes nothing." Radio duty cycle is not where this design's battery life
lives. Do not optimise advertising intervals for energy.

## Scope

In scope: the wake/advertise/sleep cycle, the BTHome v2 encoder, simulated
values, and Home Assistant showing five entities.

Out of scope: real sensor drivers, encryption, the nPM1300 fuel gauge, and
anything requiring our board or the EK.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Artifact | Real cycle, stub sensors | The cycle is product code we would write anyway; the sensor interface is not, since we do not yet know the real drivers' shape |
| Encryption | Unencrypted, seam preserved | Houseplant threat model. One byte (`0x40` device info) flips to enable it |
| HA receive path | HA host's own Bluetooth adapter | Already working; no proxy hop to debug |
| Dev escape | Button 0 held at boot | Keeps the board programmable without a build variant |
| Simulated data | Drying curve, pure function of the clock | Constants make a working sensor and a dead one look identical in HA |
| Code split | Linear `main()` + pure encoder module | The encoder is the only piece with a correctness property worth testing off-target |

## Two facts that shape everything

**Waking from System OFF is a cold boot.** All RAM is lost. There is no state
to carry between cycles, which is why the cycle is linear and the simulation is
a pure function rather than an accumulator.

**GRTC SYSCOUNTER survives it.** Datasheet §8.10: "All GRTC registers are reset
during wakeup from System OFF mode. However, the SYSCOUNTER[m].SYSCOUNTERL and
SYSCOUNTER[m].SYSCOUNTERH registers are restored automatically on wakeup from
System OFF mode and after soft reset."

That gives a monotonic time base across cold boots for free — no NVS, no stored
counter, no RRAM wear from writing 8760 times a year. **GRTC must be clocked
from LFXO**, not LFRC: Table 21 makes LFRC System-ON only and requires stopping
GRTC before System OFF if it is used. The DK's 32.768 kHz crystal is connected
by default (SB3/SB4 closed) and our board has X1, so this holds in both places.

## Structure

```
firmware/bthome-sensor/
├── CMakeLists.txt
├── Kconfig                 interval, advertise window, device name
├── prj.conf
├── boards/nrf54l15dk_nrf54l15_cpuapp.overlay
├── src/
│   ├── main.c              the cycle + simulated values
│   ├── bthome.c
│   └── bthome.h            pure encoder, no Zephyr dependency
└── tests/bthome/           host-run unit tests
```

`main()` runs top to bottom and never returns:

1. **Escape hatch.** If Button 0 is held, print a notice and idle forever.
2. **Read the clock.** GRTC SYSCOUNTER — elapsed time since first power-on.
3. **Generate values.** Five numbers as a pure function of elapsed time.
4. **Encode.** `bthome_encode()` fills a byte buffer.
5. **Advertise.** `bt_enable()`, non-connectable, for the configured window.
6. **Sleep.** Arm the GRTC alarm, `sys_poweroff()`.

The simulation lives in `main.c` as a static function. It is about twenty lines
and it is the piece thrown away when real drivers land — giving it its own
module would imply a stability it does not have.

### Configuration

| Kconfig | Default | Notes |
|---|---|---|
| `SENSOR_CYCLE_SECONDS` | `3600` | Hourly, matching the 8760 wakes/yr in HARDWARE.md §7 |
| `SENSOR_ADV_WINDOW_MS` | `2000` | ~20 transmissions at a 100 ms interval |
| `SENSOR_ADV_INTERVAL_MS` | `100` | |
| `SENSOR_DEVICE_NAME` | `"Plant-1"` | 7 characters is the maximum the spare bytes allow |

A `dev.conf` overlay sets `SENSOR_CYCLE_SECONDS=30` so a cycle can be observed
without waiting an hour. The product default stays hourly so the committed
default is the real one.

Button 0 is P1.13 on the DK. **The escape hatch is DK-only and needs no
equivalent on our board.** Our board carries no button (no `SW` designator
exists) and all five test points are committed — TP1 SENSE1, TP2 SENSE2,
TP3 SHLD, TP4 SHPHLD, TP5 SOLAR_5V — but none is needed: with a debugger
attached the device is in Debug Interface mode and System OFF is *emulated*
(datasheet §5.2.1), so the CPU keeps running and stays reachable. Connecting
the Tag-Connect is the escape hatch. No layout change required.

## Packet layout

22 of 31 available bytes:

```
02 01 06                          Flags: LE General Discoverable, no BR/EDR
12 16 D2 FC 40                    Service Data, UUID 0xFCD2, BTHome v2 unencrypted
   01 <bat>                       battery      uint8   %
   02 <lo> <hi>                   temperature  sint16  ×0.01 °C
   03 <lo> <hi>                   humidity     uint16  ×0.01 %
   14 <lo> <hi>                   moisture     uint16  ×0.01 %   ← SENSE1
   14 <lo> <hi>                   moisture_2   uint16  ×0.01 %   ← SENSE2
```

Device info `0x40` is version 2 in bits 5–7 with the encryption bit clear. That
byte is the whole encryption seam.

Nine spare bytes leave room for a 7-character local name; without one, HA names
the device "BTHome sensor" plus a MAC fragment. If those bytes are needed later,
the uint8 variants (`0x2F` moisture, `0x2E` humidity) free five at the cost of
1% resolution instead of 0.01%.

### The ordering invariant

**Both `0x14` entries must be emitted SENSE1-then-SENSE2 on every advertisement.**
BTHome assigns the `_2` postfix positionally, and the spec is explicit: "you
will need to use the same order in each advertisement, to prevent measurements
being assigned to the wrong entity." A dropped SENSE1 silently rebinds SENSE2's
data to the `moisture` entity, with no error raised anywhere.

### Packet ID is omitted

BTHome's packet ID is optional and Home Assistant does not use it — HA has its
own deduplication. Omitting it removes the cold-boot counter problem entirely.
It becomes mandatory if encryption is ever enabled, and would then need
non-volatile storage to avoid rewinding on every wake.

### Address stability

The BLE identity address must be **identical across every cold boot**, or Home
Assistant registers a new device every hour and accumulates 24 dead sensors a
day. Zephyr's LBS sample logs `No ID address. App must call settings_load()`
and generates an identity, so the default is not something to rely on.

The firmware sets the identity explicitly: a static random address derived
deterministically from the chip's FICR device ID at boot. Stable forever, no
settings subsystem, no NVS.

### Radio parameters

Non-connectable, non-scannable undirected advertising, 100 ms interval, 2 s
window — roughly 20 transmissions per wake. Connectable advertising would keep
the radio up waiting for connections we do not want, and there is no GATT
service worth connecting to.

## Error handling

**Every path must reach `sys_poweroff()`.** At 1.5 µA, firmware that hits an
error and loops does not lose one reading, it flattens the cell. Failures during
a cycle are logged and swallowed.

**Except one, which points the other way.** If arming the GRTC alarm fails, do
**not** sleep — System OFF with no wake source never returns. That path takes a
system reset so the next boot retries. The two rules are opposites and the
instinct to "always sleep on error" is wrong exactly here.

**Partial packets are never sent.** `bthome_encode()` takes a fully populated
struct; there is no optional-field concept in the API. If a complete packet
cannot be built, the cycle skips advertising and sleeps. This follows from the
ordering invariant — wrong data bound to the wrong entity is worse than no data,
and HA marking an entity stale is honest about what happened. The stub cannot
fail; the API forbids it now so real drivers cannot reintroduce it later.

**A watchdog**, configured to halt in System OFF, with a timeout a few times the
awake window. Covers a hang while the radio is up. This is the one optional
piece in the design.

## Testing

**Encoder — host-run unit tests, no board.** This is where bugs produce
plausible-looking wrong numbers rather than errors:

- Golden byte vector for a known input, including total length
- SENSE1 emitted before SENSE2
- Negative temperature as two's-complement `sint16` — −5.00 °C must encode to
  `0C FE` little-endian
- Scale factors on each field
- A too-small buffer returns an error rather than overflowing

**Cycle — on target**, because its risks are physical:

- Several short-interval cycles observed on the console
- Button escape leaves the board programmable
- BLE address byte-identical across a sleep

**End to end:** HA shows five entities under one device, with `moisture` and
`moisture_2` trending down over a session.

## Open items

- The NCS fuel gauge library's availability for nRF54L15 and its RAM/flash cost
  for a design that cold-boots hourly — an open bracketed question in
  HARDWARE.md §5. Not needed here (battery is stubbed), but it wants answering
  before real battery reporting is written.

## Sources

- [BTHome v2 format](https://bthome.io/format/)
- nRF54L15 datasheet v1.0 §8.10 (GRTC), Table 21 (clocks)
- HARDWARE.md §5 (sensing, battery), §7 (power budget)
