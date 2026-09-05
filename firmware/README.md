# Firmware — DK fire-tests

The carrier now uses BL54L15 453-00001R. See [the carrier port requirements](BL54L15-port.md); these DK test targets remain unchanged.


Bench tests that run on an **nRF54L15 DK (PCA10156)**, not on our board. They
exist to settle the pin assignment in [HARDWARE.md](../HARDWARE.md) §6 before
the board is fabricated, because those three claims are datasheet readings and
each one moves pins if it is wrong.

Nothing else in the bring-up list can be tested on the DK. Its board-controller
PMIC is not the production nPM2100 and is not on the nRF54L15's bus — see
[NEXT-STEPS.md](../NEXT-STEPS.md) for the DK limitations.

For the BTHome BLE beacon firmware (also DK-only, not a fire-test), see
[bthome-sensor/](bthome-sensor/README.md).

Each test declares its own expected outcome and reports an `*** UNEXPECTED ***`
line when the result disagrees. A negative control that quietly passes is the
result we most need to notice.

## What is being tested

| | Test | Pins | Expect | Claim |
|---|---|---|---|---|
| T1 | `pin-assignment` baseline | SCL P1.11, SDA P1.10 | PASS | our pinout works at all |
| T2 | `pin-assignment` t2 | SCL P1.14, SDA P1.10 | **FAIL** | TWIM SCL needs a dedicated clock pin (Table 77) |
| T3 | `pin-assignment` t3 | SCL P1.11, SDA P0.04 | **FAIL** | peripherals cannot cross ports (§8.8.3) |
| T4a | `systemoff-wake` baseline | P0.04 | wakes | P0 is a wake source (Table 40) |
| T4b | `systemoff-wake` t4b | P2.08 | **cannot arm** | P2 has no SENSE/DETECT/GPIOTE (Table 40) |

T2 and T3 are the tests that matter. T1 only establishes that the harness works
— without it a failure in T2 proves nothing, because it could just be bad
wiring.

## Bench setup

**Set VDD:nRF to 3.3 V in Board Configurator before anything else.**

There is no fixed 3.3 V rail on this board. P6 and the P4 test points carry
VDD:nRF, the programmable 1.8-3.3 V rail, and **the factory default is 1.8 V** —
so an unconfigured DK reads 1.8 V everywhere and there is no 3.3 V to find. The
only fixed supply on the GPIO headers is the 5.0 V on P30/P31/P32 pin 1.

There is no CLI for this: `nrfutil device` exposes board-controller firmware
programming but not the voltage. Open nRF Connect for Desktop, install/open
**Board Configurator**, select the DK, set VDD to 3.3 V, apply. It persists
across power cycles (DK guide §2.9).

**Do not power the breakout from the 5 V pin instead.** Its onboard regulator
would pull SDA/SCL up to 3.3 V against an nRF still running at 1.8 V, which
breaches the VDD + 0.3 V pin limit.

Running the set at 1.8 V would still be valid — none of the three rules under
test is voltage-marginal, and the BME280 die is in spec down to 1.71 V. But it
is not our design point, so a marginal result would be harder to read, and most
breakouts have an LDO on VIN that will not regulate from 1.8 V.

For T1–T3 you need an I²C target. The firmware speaks **BME280/BMP280**,
probing 0x76 and 0x77 and accepting either chip ID. Wire it to header P1:

| Breakout | DK | |
|---|---|---|
| VIN / VCC | VDD:nRF — P6 header (jumper fitted) or a P4 test point, **after** setting it to 3.3 V | not the 5 V on P30/P31/P32 |
| GND | any GND | |
| SCL | P1.11 (T1, T3) / P1.14 (T2) | |
| SDA | P1.10 (T1, T2) / P0.04 (T3) | |

An SHT4x would have been the better target — the SHT45-AD1F is in our BOM
(HARDWARE.md §5), so it would have doubled as driver bring-up, and its 2-byte
CRC gives protocol-level corruption detection. The BME280 has no CRC, so it is
purely a bus target. See "Integrity checking" below.

**Pull-ups.** The overlays do not enable the internal ones, because the board
uses external 4.7 kΩ at 400 kHz and that is the design point under test. Fit
4.7 kΩ to 3.3 V on both lines. Most breakouts carry their own 10 kΩ — that is
a different operating point and a weaker test, so remove them or fit the 4.7 kΩ
in parallel and note what you actually ran.

**Do not press Button 3** during T3 or T4a — it is on P0.04, and a press shorts
the line.

### Integrity checking without a CRC

The BME280 has no checksum, so a corrupt byte is indistinguishable from a real
one at the protocol level. Each pass therefore re-reads the 26-byte factory
calibration block (0x88..0xA1) and compares it against the copy taken at
startup. That block is constant for the life of the part, so any difference is
the bus rather than the sensor — and 26 bytes of known-good data catches more
than a single register would. Mismatches are counted separately from bus
errors, because they mean different things: a NAK is a bus that did not work, a
mismatch is a bus that lied.

Each pass also writes two registers before reading, so a pin that only fails in
one direction still shows up.

## Building and flashing

From `firmware/`, with an nRF Connect SDK environment active:

```bash
west build -p -b nrf54l15dk/nrf54l15/cpuapp pin-assignment
```

```bash
west build -p -b nrf54l15dk/nrf54l15/cpuapp pin-assignment -- -DEXTRA_DTC_OVERLAY_FILE=t2.overlay -DEXTRA_CONF_FILE=t2.conf
```

```bash
west build -p -b nrf54l15dk/nrf54l15/cpuapp pin-assignment -- -DEXTRA_DTC_OVERLAY_FILE=t3.overlay -DEXTRA_CONF_FILE=t3.conf
```

```bash
west build -p -b nrf54l15dk/nrf54l15/cpuapp systemoff-wake
```

```bash
west build -p -b nrf54l15dk/nrf54l15/cpuapp systemoff-wake -- -DEXTRA_DTC_OVERLAY_FILE=t4b.overlay -DEXTRA_CONF_FILE=t4b.conf
```

Then `west flash` and read the console at 115200.

**The console is VCOM1, not VCOM0** — `uart20` is the DK guide's "UART1" on
P1.04/P1.05. On macOS that is the higher-numbered `/dev/cu.usbmodem*` of the
pair. VCOM0 stays silent and looks identical to a dead board.

Flashing without west, from a hex built in the container:

```bash
nrfutil device program --firmware merged.hex --options chip_erase_mode=ERASE_ALL && nrfutil device reset
```

## Reading the results

**T3 is a runtime test.** All five configurations build clean under NCS v3.2.2
— neither dtc nor the pinctrl layer rejects the port crossing, so nothing in
the toolchain knows about §8.8.3. If the rule is real, only the silicon
enforces it.

**T4b's expected result is `-ENOTSUP` from
`gpio_pin_interrupt_configure()`**, not a silent non-wake. A pin that refuses
to arm is a much stronger result than a pin that fails to wake, which is also
what a loose jumper looks like.

**T4a needs the debugger detached.** In Debug Interface mode System OFF is
emulated (datasheet §5.2.1): the CPU keeps running and the device never really
sleeps. The firmware prints a warning if it detects it got past `sys_poweroff()`.

A partial pass in T1–T3 counts as a failure. An intermittent bus is exactly what
a violated timing rule looks like, and it is not something we can design around.

## Results

Run on the DK with a BME280 (chip ID 0x60 at 0x76), VDD:nRF at 3.3 V, the
breakout's own pull-ups, 20 passes per case.

| Case | Pins | Expected | Actual | |
|---|---|---|---|---|
| T1 | SCL P1.11, SDA P1.10, 400 kHz | PASS | **PASS** 20/20 | harness is good |
| T2 | SCL P1.14, SDA P1.10, 400 kHz | FAIL | **PASS** 20/20 | rule not reproducible |
| T2-fast | SCL P1.14, SDA P1.10, 1 MHz | FAIL | **PASS** 20/20 | still not, at the TWIM ceiling |
| T3-control | i2c30, SCL P0.03, SDA P0.04 | PASS | **PASS** 20/20 | sensor + P0.04 wire good |
| T3 | i2c22, SCL P1.11, SDA P0.04 | FAIL | **FAIL** -ENODEV | port rule enforced |
| T4a | wake from P0.04 | wakes | **WOKE** `RESET_LOW_POWER_WAKE` | P0 wakes |
| T4b | wake from P2.08 | cannot arm | **-ENOTSUP** | P2 cannot |

### The port rule holds (§8.8.3)

T3 is the one that would have broken a board. A peripheral-domain TWIM
(`i2c22`) cannot reach a low-power-domain pin (P0.04). The control is what
makes this stand up: same sensor, same P0.04 wire, `i2c30` instead of `i2c22`,
and it passes 20/20. Both lines were verified to carry external pull-ups with
`pin-probe` immediately before the T3 run, so "no device" is not a loose wire.

**Keep SDA and SCL on the same port.** Confirmed by experiment, not just by
reading.

### The clock-pin rule is not reproducible here (Table 77)

A non-clock pin works as TWIM SCL at 400 kHz and at 1 MHz, which is the TWIM
ceiling on this part. There is no faster I²C test available, so via TWIM the
requirement cannot be made to bite at all.

**This does not mean the requirement is void.** Table 77 is a timing-margin
claim — clock pins are "optimized to ensure correct timing between the clock
and data signals". A pass shows the margin was not consumed at this rate, at
room temperature, on 10 cm of jumper wire. Process corners, temperature, and a
real PCB are all outside what was tested.

Worth noting Table 77 also requires a clock pin for SPIM `SCK`, and SPIM00 runs
at 32 MHz where pin-to-pin skew genuinely matters. The requirement is plausibly
dimensioned by the fastest peripheral and applied across the table. That is a
hypothesis these results are consistent with, not something they establish.

**Design call: keep P1.11.** It costs nothing and satisfies a documented
requirement, and a room-temperature bench test that did not fail is not
evidence against one. What the result buys is a known-large margin at our
400 kHz operating point, so deviating later would be a low-risk deliberate
choice rather than a blind one.

### The wake rules hold (Table 40)

T4a produced a genuine System OFF wake from P0.04 — `RESET_LOW_POWER_WAKE` on
the following boot, which only a real wake sets, and the emulated-System-OFF
warning never fired. T4b returned `-ENOTSUP` from
`gpio_pin_interrupt_configure()`: P2 will not even arm a level sense. That is
the stronger of the two possible negative results, since a refusal cannot be
confused with a floating pin.

**PMIC_INT stays on P0.00.**

### Was this worth doing?

Not as much as it looked when proposed. All four claims confirmed what we had
already read and already designed to, so the pinout is unchanged. The prior
probability that Nordic's tables were correct was high, and a test that can only
return "yes, you were right" carries little information.

What it did buy: the pinout is demonstrated rather than assumed; there is now a
working container build, flash and console path plus `pin-probe`, all of which
real bring-up needs and all cheaper to debug against a known answer; two bench
traps are documented; and the clock-pin margin turns out to be large.

The untested risk is entirely in the power chain — boost configuration and the
LDOSW gate for `+3V3_FDC_SW`. Those are our topology decisions rather than
claims established by these DK tests, and they need the production PMIC on the
bench (or the nPM2100 evaluation hardware).

### Bench traps that cost time

- **The P1 header's 00-03 positions are parenthesized on the silkscreen** and
  are not connected without modification (P1.00/P1.01 need SB3-SB6, P1.02/P1.03
  are NFC1/NFC2 and need 0 Ω resistors). P0.00-P0.04 are *not* parenthesized.
  Wiring "03" and "04" on the P1 header instead of the P0 header lands on
  P1.03 (not connected) and P1.04 (`uart20` TXD, the console).
- **The P6 jumper feeds VDD:nRF.** With it out, the SoC is unpowered while the
  debugger stays alive on USB 5 V, and `nrfutil device reset` fails with "debug
  port unavailable" rather than anything mentioning power.
- **Each GPIO header carries its own `VDD:IO` pin** — buffered VDD:nRF, so
  3.3 V once configured, and a more convenient supply for a breakout than P6.
- **`sys_poweroff()` makes the device unprogrammable.** T4a sleeps 5 s then
  enters System OFF, and a device in System OFF does not answer the debugger —
  the next flash simply fails. Press RESET and program inside the 5 s window,
  or `nrfutil device recover`. T4b returns early and never sleeps, so it is
  safe to leave on the board.
- To put the DK back in a sane state, build and flash the stock sample:
  `west build -p always -b nrf54l15dk/nrf54l15/cpuapp $ZEPHYR_BASE/samples/hello_world`.
  It prints on VCOM1.
- Two failures in a row here were bench faults, not results. `pin-probe` exists
  because `-ENODEV` and a loose wire are the same reading; run it before
  banking any negative result.

## What to do with an unexpected result

T2 or T3 passing means the corresponding rule in HARDWARE.md §6 is not what we
read it to be. That does not immediately free the pin — it means the reading is
unreliable and all three need re-checking against the datasheet before the
pinout is frozen. Note it in NEXT-STEPS.md rather than acting on it directly.

## Build status

All five configurations compile under **NCS v3.2.2** and the resolved
devicetree was checked against the intent in each case — `psels` decode to the
pins named in the table above, and the negative controls really do carry
`CONFIG_TEST_EXPECT_*=n`.

**Run on hardware so far:** T1 boots on the DK, `i2c22` initialises, and the
probe correctly reports `-ENODEV` at both addresses with nothing wired. That
exercises the no-device path and shows the harness reports honestly. No test
in the table has produced a real result yet — that needs the BME280 attached.

Notes on choices that the board DTS forced:

- **`i2c22`, not `i2c20`.** UARTE20 and TWIM20 are the same peripheral
  instance, and `uart20` is the Zephyr console on this board.
- **The console is `uart20` on P1.04/P1.05** — the DK guide's "UART1", not the
  P0 UART. P0.00–P0.03 are still claimed by `uart30`, which the board DTS also
  enables, so they stay off limits for a different reason.
- Node labels used by the overlays (`led1` = P1.10, `led3` = P1.14,
  `button3` = P0.04) were read from `nrf54l15dk_common.dtsi`, not assumed.

Editors will flag the Zephyr includes as missing until a build generates
`compile_commands.json`. That is the language server, not the code.

## Reproducing the build without an NCS install

The toolchain image is amd64-only, so this runs under emulation on Apple
silicon — slow but workable for apps this size.

```bash
docker volume create ncs-src && docker run --rm --platform linux/amd64 -v ncs-src:/workdir -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.2.2 . && west update --narrow -o=--depth=1'
```

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v "$PWD:/fw" -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/t1 /fw/pin-assignment'
```

The image's entrypoint is `bash -c`, so the whole command has to be one quoted
string — `docker run … uname -m` runs `uname` with `$0` set to `-m`.
