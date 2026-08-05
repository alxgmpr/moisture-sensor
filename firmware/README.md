# Firmware — DK fire-tests

Bench tests that run on an **nRF54L15 DK (PCA10156)**, not on our board. They
exist to settle the pin assignment in [HARDWARE.md](../HARDWARE.md) §6 before
the board is fabricated, because those three claims are datasheet readings and
each one moves pins if it is wrong.

Nothing else in the bring-up list can be tested on the DK. The DK's nPM1300 is
owned by the nRF5340 board controller and is not on the nRF54L15's bus — see
[NEXT-STEPS.md](../NEXT-STEPS.md) under "What the DK's nPM1300 is not".

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

**Set VDD:nRF to 3.3 V in Board Configurator before anything else.** The DK
default is 1.8 V. Our rail is 3.3 V and the bus timing under test is sensitive
to it.

For T1–T3 you need an I²C target. Use an **SHT4x breakout** — the SHT45-AD1F is
already in our BOM (HARDWARE.md §5), so this doubles as bring-up of a driver we
need. Wire it to header P1:

| Breakout | DK |
|---|---|
| VDD | VDD (P4 test point or header P6, 3.3 V) |
| GND | GND |
| SCL | P1.11 (T1, T3) / P1.14 (T2) |
| SDA | P1.10 (T1, T2) / P0.04 (T3) |

**Pull-ups.** The overlays do not enable the internal ones, because the board
uses external 4.7 kΩ at 400 kHz and that is the design point under test. Fit
4.7 kΩ to 3.3 V on both lines. Most breakouts carry their own 10 kΩ — that is
a different operating point and a weaker test, so remove them or fit the 4.7 kΩ
in parallel and note what you actually ran.

**Do not press Button 3** during T3 or T4a — it is on P0.04, and a press shorts
the line.

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

Nothing here has been run on hardware. Compiling proves the overlays resolve,
not that any claim in the table is true.

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
