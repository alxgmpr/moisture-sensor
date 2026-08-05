# BTHome Firmware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Firmware on the nRF54L15 DK that advertises five simulated soil-sensor values as BTHome v2 beacons on an hourly wake/advertise/System-OFF cycle, appearing in Home Assistant as one device with five entities.

**Architecture:** A linear `main()` that runs once per cold boot — check escape button, read GRTC, generate values, encode, advertise, sleep — plus one pure module (`bthome.c`) holding all wire-format logic so it can be tested on the host without a board. Waking from System OFF is a cold boot, so there is no state machine and no persistent storage; GRTC SYSCOUNTER is the only thing that survives, and it is the time base.

**Tech Stack:** nRF Connect SDK v3.2.2, Zephyr 4.2, C11. Built in the `ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2` container. Host unit tests compile with the Mac's own `cc` — the encoder has no Zephyr dependency, so its tests need no container and no emulation.

Design: [docs/superpowers/specs/2026-08-04-bthome-firmware-design.md](../specs/2026-08-04-bthome-firmware-design.md)

## Global Constraints

- Target board is `nrf54l15dk/nrf54l15/cpuapp`. NCS v3.2.2.
- **Console is VCOM1**, `/dev/cu.usbmodem0010577745793`, 115200 8N1. VCOM0 is silent and looks identical to a dead board.
- DK serial number for `nrfutil` is `1057774579`.
- **VDD:nRF must be 3.3 V** (set in Board Configurator; the DK default of 1.8 V is not our operating point).
- **The P6 jumper must be fitted** or the SoC is unpowered and `nrfutil` fails with "debug port unavailable" without mentioning power.
- `bthome.c` and `bthome.h` must not include any Zephyr header. That is what makes them host-testable.
- **Measurement order in the packet is load-bearing.** Both `0x14` moisture entries must be emitted SENSE1-then-SENSE2 on every advertisement; Home Assistant binds `moisture_2` positionally.
- **Every error path must reach `sys_poweroff()`** — except a failure to arm the GRTC wake, which must `sys_reboot()` instead, because System OFF with no wake source never returns.
- GRTC is clocked from LFXO (board default). Do not switch it to LFRC; Table 21 of the datasheet makes LFRC System-ON only.

**Build command** (used by several tasks):

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

**Flash command** (used by several tasks):

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

---

### Task 1: BTHome v2 encoder, with host unit tests

**Files:**
- Create: `firmware/bthome-sensor/src/bthome.h`
- Create: `firmware/bthome-sensor/src/bthome.c`
- Test: `firmware/bthome-sensor/tests/bthome/test_bthome.c`
- Test: `firmware/bthome-sensor/tests/bthome/run.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: `struct bthome_values` (fields `battery_pct` `uint8_t`, `temperature_cc` `int16_t`, `humidity_cpct` `uint16_t`, `moisture1_cpct` `uint16_t`, `moisture2_cpct` `uint16_t`); `#define BTHOME_ADV_DATA_LEN 17`; `int bthome_encode(const struct bthome_values *v, uint8_t *buf, size_t buf_len)` returning `BTHOME_ADV_DATA_LEN` or `-1`.

- [ ] **Step 1: Write the failing test**

Create `firmware/bthome-sensor/tests/bthome/test_bthome.c`:

```c
/*
 * Host tests for the BTHome encoder. Plain C and plain asserts: the module
 * under test has no Zephyr dependency by design, so the test should not
 * invent one. Compiles and runs in well under a second with the system cc.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../../src/bthome.h"

static int failures;

static void expect_bytes(const char *name, const uint8_t *got,
			 const uint8_t *want, size_t len)
{
	if (memcmp(got, want, len) == 0) {
		printf("PASS %s\n", name);
		return;
	}

	failures++;
	printf("FAIL %s\n  want:", name);
	for (size_t i = 0; i < len; i++) {
		printf(" %02X", want[i]);
	}
	printf("\n  got: ");
	for (size_t i = 0; i < len; i++) {
		printf(" %02X", got[i]);
	}
	printf("\n");
}

static void expect_int(const char *name, int got, int want)
{
	if (got == want) {
		printf("PASS %s\n", name);
		return;
	}
	failures++;
	printf("FAIL %s: want %d, got %d\n", name, want, got);
}

/* battery 87 %, 23.45 C, 41.20 %RH, SENSE1 62.50 %, SENSE2 58.75 % */
static const struct bthome_values nominal = {
	.battery_pct = 87,
	.temperature_cc = 2345,
	.humidity_cpct = 4120,
	.moisture1_cpct = 6250,
	.moisture2_cpct = 5875,
};

static void test_golden_vector(void)
{
	static const uint8_t want[BTHOME_ADV_DATA_LEN] = {
		0xD2, 0xFC,             /* service UUID 0xFCD2, little endian */
		0x40,                   /* BTHome v2, unencrypted */
		0x01, 0x57,             /* battery 87 */
		0x02, 0x29, 0x09,       /* temperature 2345 */
		0x03, 0x18, 0x10,       /* humidity 4120 */
		0x14, 0x6A, 0x18,       /* moisture 6250   (SENSE1) */
		0x14, 0xF3, 0x16,       /* moisture 5875   (SENSE2) */
	};
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	expect_int("golden returns full length",
		   bthome_encode(&nominal, buf, sizeof(buf)), BTHOME_ADV_DATA_LEN);
	expect_bytes("golden vector", buf, want, sizeof(want));
}

static void test_negative_temperature(void)
{
	struct bthome_values v = nominal;
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	v.temperature_cc = -500;   /* -5.00 C -> 0xFE0C -> 0C FE little endian */
	bthome_encode(&v, buf, sizeof(buf));

	expect_int("negative temp low byte", buf[6], 0x0C);
	expect_int("negative temp high byte", buf[7], 0xFE);
}

static void test_moisture_order(void)
{
	struct bthome_values v = nominal;
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	/* SENSE1 must land at offset 12-13 and SENSE2 at 15-16. Home Assistant
	 * assigns moisture_2 by position, so a swap here silently binds the
	 * wrong electrode to the wrong entity with no error anywhere. */
	v.moisture1_cpct = 0x1111;
	v.moisture2_cpct = 0x2222;
	bthome_encode(&v, buf, sizeof(buf));

	expect_int("sense1 low byte", buf[12], 0x11);
	expect_int("sense1 high byte", buf[13], 0x11);
	expect_int("sense2 low byte", buf[15], 0x22);
	expect_int("sense2 high byte", buf[16], 0x22);
}

static void test_buffer_too_small(void)
{
	uint8_t buf[BTHOME_ADV_DATA_LEN - 1];

	expect_int("short buffer rejected",
		   bthome_encode(&nominal, buf, sizeof(buf)), -1);
}

static void test_null_arguments(void)
{
	uint8_t buf[BTHOME_ADV_DATA_LEN];

	expect_int("null values rejected", bthome_encode(NULL, buf, sizeof(buf)), -1);
	expect_int("null buffer rejected", bthome_encode(&nominal, NULL, 99), -1);
}

int main(void)
{
	test_golden_vector();
	test_negative_temperature();
	test_moisture_order();
	test_buffer_too_small();
	test_null_arguments();

	printf("\n%s\n", failures ? "TESTS FAILED" : "all tests passed");
	return failures ? 1 : 0;
}
```

Create `firmware/bthome-sensor/tests/bthome/run.sh`:

```sh
#!/bin/sh
# Host test runner. No container and no Zephyr: bthome.c is pure C.
set -e

here=$(dirname "$0")
out=$(mktemp -d)/test_bthome

cc -std=c11 -Wall -Wextra -Werror -o "$out" \
	"$here/test_bthome.c" "$here/../../src/bthome.c"

"$out"
```

Then make it executable:

```bash
chmod +x firmware/bthome-sensor/tests/bthome/run.sh
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `./firmware/bthome-sensor/tests/bthome/run.sh`

Expected: FAIL — the compiler errors with `fatal error: '../../src/bthome.h' file not found`, because the module does not exist yet.

- [ ] **Step 3: Write the header**

Create `firmware/bthome-sensor/src/bthome.h`:

```c
/*
 * BTHome v2 service-data encoder.
 *
 * Pure C — no Zephyr, no hardware. Everything that can be got wrong about the
 * wire format lives in this module so it can be tested on the host.
 */
#ifndef BTHOME_H_
#define BTHOME_H_

#include <stddef.h>
#include <stdint.h>

/*
 * Every field is mandatory, and there is deliberately no way to express an
 * absent measurement. BTHome binds the second moisture value positionally, so
 * omitting one field would silently rebind SENSE2's reading to Home
 * Assistant's `moisture` entity with no error raised anywhere.
 */
struct bthome_values {
	uint8_t  battery_pct;     /* 0..100 */
	int16_t  temperature_cc;  /* hundredths of a degree C */
	uint16_t humidity_cpct;   /* hundredths of a percent */
	uint16_t moisture1_cpct;  /* hundredths of a percent, SENSE1 */
	uint16_t moisture2_cpct;  /* hundredths of a percent, SENSE2 */
};

/* UUID (2) + device info (1) + five measurements (14). */
#define BTHOME_ADV_DATA_LEN 17

/*
 * Writes the complete BTHome service-data payload — 0xFCD2 little endian, the
 * device-info byte, then the measurements — into buf. The caller wraps this in
 * an AD element of type BT_DATA_SVC_DATA16; the length and type bytes are the
 * Bluetooth stack's job, not ours.
 *
 * Returns BTHOME_ADV_DATA_LEN, or -1 if any argument is NULL or buf_len is too
 * small.
 */
int bthome_encode(const struct bthome_values *v, uint8_t *buf, size_t buf_len);

#endif /* BTHOME_H_ */
```

- [ ] **Step 4: Write the implementation**

Create `firmware/bthome-sensor/src/bthome.c`:

```c
#include "bthome.h"

/* Service UUID 0xFCD2, transmitted little endian. */
#define BTHOME_UUID_LO 0xD2
#define BTHOME_UUID_HI 0xFC

/* Bits 5-7 hold the BTHome version (2); bit 0 clear means unencrypted. This
 * single byte is the whole encryption seam — it becomes 0x41 when encryption
 * is turned on. */
#define BTHOME_DEVICE_INFO 0x40

#define OBJ_BATTERY     0x01   /* uint8,  factor 1    */
#define OBJ_TEMPERATURE 0x02   /* sint16, factor 0.01 */
#define OBJ_HUMIDITY    0x03   /* uint16, factor 0.01 */
#define OBJ_MOISTURE    0x14   /* uint16, factor 0.01 */

static size_t put_u8(uint8_t *buf, size_t i, uint8_t obj, uint8_t val)
{
	buf[i++] = obj;
	buf[i++] = val;
	return i;
}

static size_t put_u16(uint8_t *buf, size_t i, uint8_t obj, uint16_t val)
{
	buf[i++] = obj;
	buf[i++] = (uint8_t)(val & 0xFFU);
	buf[i++] = (uint8_t)(val >> 8);
	return i;
}

int bthome_encode(const struct bthome_values *v, uint8_t *buf, size_t buf_len)
{
	size_t i = 0;

	if (v == NULL || buf == NULL || buf_len < BTHOME_ADV_DATA_LEN) {
		return -1;
	}

	buf[i++] = BTHOME_UUID_LO;
	buf[i++] = BTHOME_UUID_HI;
	buf[i++] = BTHOME_DEVICE_INFO;

	/* Ascending object id, and SENSE1 before SENSE2. The moisture ordering
	 * is load-bearing: Home Assistant assigns the `_2` postfix by position,
	 * and the BTHome spec requires the same order in every advertisement. */
	i = put_u8(buf, i, OBJ_BATTERY, v->battery_pct);
	i = put_u16(buf, i, OBJ_TEMPERATURE, (uint16_t)v->temperature_cc);
	i = put_u16(buf, i, OBJ_HUMIDITY, v->humidity_cpct);
	i = put_u16(buf, i, OBJ_MOISTURE, v->moisture1_cpct);
	i = put_u16(buf, i, OBJ_MOISTURE, v->moisture2_cpct);

	return (int)i;
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `./firmware/bthome-sensor/tests/bthome/run.sh`

Expected: every line `PASS`, then `all tests passed`, exit status 0.

- [ ] **Step 6: Commit**

```bash
git add firmware/bthome-sensor/src/bthome.h firmware/bthome-sensor/src/bthome.c firmware/bthome-sensor/tests/
git commit -m "BTHome v2 encoder, with the wire format pinned by host tests

Pure C with no Zephyr dependency, so the tests compile with the system cc and
run in under a second. The golden vector pins every byte; separate tests cover
negative temperature as two's-complement sint16 and the SENSE1-before-SENSE2
ordering that Home Assistant binds positionally."
```

---

### Task 2: App skeleton that advertises a fixed packet

Gets the build, flash and advertise path working end to end with hardcoded values, so later tasks change one thing at a time.

**Files:**
- Create: `firmware/bthome-sensor/CMakeLists.txt`
- Create: `firmware/bthome-sensor/Kconfig`
- Create: `firmware/bthome-sensor/prj.conf`
- Create: `firmware/bthome-sensor/dev.conf`
- Create: `firmware/bthome-sensor/src/main.c`

**Interfaces:**
- Consumes: `bthome_encode()`, `struct bthome_values`, `BTHOME_ADV_DATA_LEN` from Task 1.
- Produces: a buildable Zephyr application; `CONFIG_SENSOR_CYCLE_SECONDS`, `CONFIG_SENSOR_ADV_WINDOW_MS`, `CONFIG_SENSOR_DEVICE_NAME`.

No devicetree overlay is needed. The app uses only board-default aliases (`sw0`) and adds no pins.

- [ ] **Step 1: Create the build files**

`firmware/bthome-sensor/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(bthome_sensor)

target_sources(app PRIVATE src/main.c src/bthome.c)
```

`firmware/bthome-sensor/Kconfig`:

```
config SENSOR_CYCLE_SECONDS
	int "Seconds between wake cycles"
	default 3600
	help
	  Hourly by default, matching the 8760 wakes/yr in HARDWARE.md §7. The
	  committed default is the product value; dev.conf overrides it.

config SENSOR_ADV_WINDOW_MS
	int "Milliseconds to advertise per wake"
	default 2000

config SENSOR_DEVICE_NAME
	string "BLE local name"
	default "Plant-1"
	help
	  Seven characters maximum. The advertisement has nine spare bytes and
	  the name element costs two on top of its text.

source "Kconfig.zephyr"
```

`firmware/bthome-sensor/prj.conf`:

```
CONFIG_BT=y
CONFIG_BT_BROADCASTER=y
CONFIG_BT_PERIPHERAL=n
CONFIG_BT_OBSERVER=n
CONFIG_BT_DEVICE_NAME="Plant-1"

CONFIG_GPIO=y
CONFIG_HWINFO=y
CONFIG_POWEROFF=y
CONFIG_REBOOT=y
```

`firmware/bthome-sensor/dev.conf`:

```
# Thirty-second cycle so a full wake/advertise/sleep can be watched without
# waiting an hour. The product default in Kconfig stays at 3600.
CONFIG_SENSOR_CYCLE_SECONDS=30
```

- [ ] **Step 2: Write main.c with fixed values**

Create `firmware/bthome-sensor/src/main.c`:

```c
/*
 * BTHome soil sensor — nRF54L15 DK, simulated data.
 *
 * One cold boot is one cycle: wake, generate, advertise, System OFF. Waking
 * from System OFF resets the device, so there is no loop and no state to
 * carry between cycles.
 */

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/sys/printk.h>

#include "bthome.h"

static void advertise(const uint8_t *svc_data)
{
	const struct bt_data ad[] = {
		BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
		BT_DATA(BT_DATA_SVC_DATA16, svc_data, BTHOME_ADV_DATA_LEN),
		BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_SENSOR_DEVICE_NAME,
			sizeof(CONFIG_SENSOR_DEVICE_NAME) - 1),
	};
	int err;

	err = bt_enable(NULL);
	if (err) {
		printk("bt_enable failed (%d)\n", err);
		return;
	}

	/* Non-connectable, non-scannable: there is no GATT service worth
	 * connecting to, and staying connectable would hold the radio up
	 * waiting for connections we do not want. */
	err = bt_le_adv_start(BT_LE_ADV_PARAM(BT_LE_ADV_OPT_NONE,
					      BT_GAP_ADV_FAST_INT_MIN_2,
					      BT_GAP_ADV_FAST_INT_MAX_2, NULL),
			      ad, ARRAY_SIZE(ad), NULL, 0);
	if (err) {
		printk("adv_start failed (%d)\n", err);
		return;
	}

	printk("advertising %d ms\n", CONFIG_SENSOR_ADV_WINDOW_MS);
	k_msleep(CONFIG_SENSOR_ADV_WINDOW_MS);

	bt_le_adv_stop();
}

int main(void)
{
	/* Fixed values for now; Task 4 replaces this with the simulation. */
	const struct bthome_values v = {
		.battery_pct = 87,
		.temperature_cc = 2345,
		.humidity_cpct = 4120,
		.moisture1_cpct = 6250,
		.moisture2_cpct = 5875,
	};
	uint8_t svc[BTHOME_ADV_DATA_LEN];

	printk("\n=== bthome-sensor ===\n");

	if (bthome_encode(&v, svc, sizeof(svc)) != BTHOME_ADV_DATA_LEN) {
		printk("encode failed\n");
		return 0;
	}

	printk("payload:");
	for (size_t i = 0; i < sizeof(svc); i++) {
		printk(" %02X", svc[i]);
	}
	printk("\n");

	advertise(svc);

	printk("cycle complete\n");
	return 0;
}
```

- [ ] **Step 3: Build**

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

Expected: exit 0 and `.build-bthome.hex` written.

- [ ] **Step 4: Flash and read the console**

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

Read `/dev/cu.usbmodem0010577745793` at 115200. Expected output:

```
=== bthome-sensor ===
payload: D2 FC 40 01 57 02 29 09 03 18 10 14 6A 18 14 F3 16
advertising 2000 ms
cycle complete
```

The payload bytes must match Task 1's golden vector exactly. If they do not, the encoder is being called differently than the test calls it.

- [ ] **Step 5: Confirm the advertisement is on air**

Open nRF Connect on a phone (or any BLE scanner) and find `Plant-1`. Confirm the service data under UUID `0xFCD2` matches the payload printed above, from the `40` byte onward.

This is the step that proves the AD wrapping is right — the encoder tests cannot see whether the stack put the UUID and length bytes on correctly.

- [ ] **Step 6: Commit**

```bash
git add firmware/bthome-sensor/
git commit -m "App skeleton: advertise a fixed BTHome packet

Gets build, flash and advertise working with hardcoded values so later tasks
change one thing at a time. No devicetree overlay needed — the app uses only
board-default aliases and adds no pins.

Non-connectable advertising: there is no GATT service worth connecting to."
```

---

### Task 3: Stable BLE identity derived from the chip

Without this, Home Assistant registers a new device on every wake and accumulates 24 dead sensors a day.

**Files:**
- Modify: `firmware/bthome-sensor/src/main.c`

**Interfaces:**
- Consumes: `advertise()` from Task 2.
- Produces: `static int set_stable_identity(void)`, returning 0 on success or a negative error. Called before `bt_enable()`.

- [ ] **Step 1: Add the identity function**

Add these includes to the top of `main.c`, after the existing ones:

```c
#include <string.h>

#include <zephyr/drivers/hwinfo.h>
```

Add this function above `advertise()`:

```c
/*
 * The BLE identity must be identical on every cold boot. Zephyr generates one
 * when none is configured — the LBS sample logs "No ID address" and does
 * exactly that — and a fresh address each hour would make Home Assistant
 * register a new device every hour.
 *
 * Deriving it from the chip's own ID keeps it stable with no settings
 * subsystem, no NVS, and no flash wear.
 */
static int set_stable_identity(void)
{
	bt_addr_le_t addr = { .type = BT_ADDR_LE_RANDOM };
	uint8_t hwid[16];
	ssize_t n;
	int err;

	n = hwinfo_get_device_id(hwid, sizeof(hwid));
	if (n < 6) {
		printk("hwinfo_get_device_id returned %d\n", (int)n);
		return -1;
	}

	/* Fold every byte of the device id into six so none of it is ignored. */
	memset(addr.a.val, 0, sizeof(addr.a.val));
	for (ssize_t i = 0; i < n; i++) {
		addr.a.val[i % 6] ^= hwid[i];
	}

	/* A static random address must have its two most significant bits set. */
	addr.a.val[5] |= 0xC0;

	err = bt_id_create(&addr, NULL);
	if (err < 0) {
		printk("bt_id_create failed (%d)\n", err);
		return err;
	}

	printk("identity: %02X:%02X:%02X:%02X:%02X:%02X\n",
	       addr.a.val[5], addr.a.val[4], addr.a.val[3],
	       addr.a.val[2], addr.a.val[1], addr.a.val[0]);

	return 0;
}
```

- [ ] **Step 2: Call it before bt_enable**

In `advertise()`, insert this immediately before the `bt_enable(NULL)` call:

```c
	if (set_stable_identity() < 0) {
		printk("continuing with the stack's own identity\n");
	}
```

`bt_id_create()` sets the default identity when called before `bt_enable()`. If it returns `-EALREADY` or the address printed does not match what the scanner shows, move this call to immediately *after* `bt_enable()` succeeds and re-run Step 4.

- [ ] **Step 3: Build and flash**

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

- [ ] **Step 4: Verify the address is stable across resets**

Read the console, note the `identity:` line. Then reset three times:

```bash
nrfutil device reset --serial-number 1057774579
```

Expected: the same six bytes every time, and no `No ID address` warning. A changing address here is the whole bug this task exists to prevent, so do not proceed until it is byte-identical.

Confirm the scanner shows that same address for `Plant-1`.

- [ ] **Step 5: Commit**

```bash
git add firmware/bthome-sensor/src/main.c
git commit -m "Derive a stable BLE identity from the chip id

Zephyr generates an identity when none is configured. Since every wake is a
cold boot, that would give Home Assistant a new device every hour and 24 dead
sensors a day. Folding the hwinfo device id into six bytes keeps the address
fixed with no settings subsystem and no flash wear."
```

---

### Task 4: GRTC time base and the simulated drying curve

**Files:**
- Modify: `firmware/bthome-sensor/src/main.c`

**Interfaces:**
- Consumes: `struct bthome_values` from Task 1.
- Produces: `static uint64_t elapsed_ms(void)`; `static struct bthome_values sim_values(uint64_t t_ms)`.

- [ ] **Step 1: Add the time base and simulation**

Add to the includes in `main.c`:

```c
#include <zephyr/drivers/timer/nrf_grtc_timer.h>
```

Add these constants and functions above `main()`:

```c
/* One wet-to-dry sweep, then it repeats, so the curve is visible in a session. */
#define SIM_DRY_PERIOD_MS   (6ULL * 60 * 60 * 1000)
#define SIM_MOIST_WET_CPCT  8000U   /* 80.00 % */
#define SIM_MOIST_DRY_CPCT  2500U   /* 25.00 % */

/* SENSE2 reads four points below SENSE1 so that a positional mix-up between
 * the two entities is obvious in Home Assistant rather than invisible. */
#define SIM_SENSE2_OFFSET   400U

/*
 * GRTC SYSCOUNTER survives System OFF — the datasheet is explicit that
 * SYSCOUNTERL/H are restored on wakeup even though the rest of GRTC resets.
 * That makes it the one clock that measures total elapsed time across cold
 * boots, which is why the simulation can be a pure function of it and needs no
 * stored state.
 *
 * The counter runs at sys_clock_hw_cycles_per_sec(), not a fixed 1 MHz, so
 * convert rather than assume.
 */
static uint64_t elapsed_ms(void)
{
	uint64_t ticks = z_nrf_grtc_timer_read();

	return (ticks * 1000ULL) / (uint64_t)sys_clock_hw_cycles_per_sec();
}

/* Triangle wave in [-amplitude, +amplitude], integer only. */
static int32_t triangle(uint64_t t_ms, uint32_t period_ms, int32_t amplitude)
{
	uint32_t phase = (uint32_t)(t_ms % period_ms);
	uint32_t half = period_ms / 2U;
	uint32_t up = (phase < half) ? phase : (period_ms - phase);

	return ((int32_t)up * 2 * amplitude) / (int32_t)half - amplitude;
}

static struct bthome_values sim_values(uint64_t t_ms)
{
	uint64_t phase = t_ms % SIM_DRY_PERIOD_MS;
	uint32_t span = SIM_MOIST_WET_CPCT - SIM_MOIST_DRY_CPCT;
	uint16_t m1 = (uint16_t)(SIM_MOIST_WET_CPCT -
				 (uint64_t)span * phase / SIM_DRY_PERIOD_MS);
	uint64_t drained = t_ms / (30ULL * 60 * 1000);   /* 1 % per 30 min */

	struct bthome_values v = {
		.battery_pct = (drained >= 99) ? 1U : (uint8_t)(100U - drained),
		.temperature_cc =
			(int16_t)(2100 + triangle(t_ms, 20U * 60 * 1000, 150)),
		.humidity_cpct =
			(uint16_t)(4500 + triangle(t_ms, 37U * 60 * 1000, 800)),
		.moisture1_cpct = m1,
		.moisture2_cpct = (m1 > SIM_SENSE2_OFFSET)
					  ? (uint16_t)(m1 - SIM_SENSE2_OFFSET)
					  : 0U,
	};

	return v;
}
```

- [ ] **Step 2: Use them in main**

Replace the fixed `const struct bthome_values v = {...};` block in `main()` with:

```c
	uint64_t now_ms = elapsed_ms();
	const struct bthome_values v = sim_values(now_ms);
```

And add this line immediately after the `=== bthome-sensor ===` banner:

```c
	printk("elapsed %llu ms\n", now_ms);
```

Move the `now_ms`/`v` declarations above that `printk` so they are in scope.

Also add a readable dump after the payload print:

```c
	printk("battery %u%%  temp %d.%02d C  hum %u.%02u%%  m1 %u.%02u%%  m2 %u.%02u%%\n",
	       v.battery_pct, v.temperature_cc / 100, (v.temperature_cc % 100 + 100) % 100,
	       v.humidity_cpct / 100, v.humidity_cpct % 100,
	       v.moisture1_cpct / 100, v.moisture1_cpct % 100,
	       v.moisture2_cpct / 100, v.moisture2_cpct % 100);
```

- [ ] **Step 3: Build and flash**

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

- [ ] **Step 4: Verify the values against known-good numbers**

Immediately after programming, `elapsed_ms` is near zero. Expected first-boot values, within a point or two for the milliseconds that have actually elapsed:

| Field | Expected near t=0 |
|---|---|
| battery | `100%` |
| temp | `19.50 C` |
| humidity | `37.00%` |
| m1 | `80.00%` |
| m2 | `76.00%` |

Then reset twice more, a few seconds apart. **`elapsed` must keep increasing across resets, not restart at zero.** That is the proof SYSCOUNTER survived, and everything in the design rests on it. If it restarts at zero, stop — the simulation and the whole no-stored-state approach need rethinking.

- [ ] **Step 5: Commit**

```bash
git add firmware/bthome-sensor/src/main.c
git commit -m "Simulated drying curve driven by GRTC SYSCOUNTER

SYSCOUNTER is restored on wakeup from System OFF even though the rest of GRTC
resets, so it measures total elapsed time across cold boots. That lets the
simulation be a pure function of the clock with no stored state and no flash
wear from writing 8760 times a year.

SENSE2 is offset four points below SENSE1 so a positional mix-up between the
two Home Assistant entities is visible rather than silent."
```

---

### Task 5: The sleep cycle and the escape hatch

**Files:**
- Modify: `firmware/bthome-sensor/src/main.c`

**Interfaces:**
- Consumes: everything from Tasks 2–4.
- Produces: `static bool escape_held(void)`; `static void sleep_until_next_cycle(void)` which never returns.

- [ ] **Step 1: Add the escape hatch**

Add to the includes:

```c
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/sys/reboot.h>
```

Add above `main()`:

```c
static const struct gpio_dt_spec escape_btn = GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);

/*
 * Held at boot, this keeps the device awake and therefore programmable. A
 * device in System OFF does not answer the debugger, so without an escape a
 * one-hour cycle leaves a very small window to flash in.
 *
 * DK only. Our board needs no equivalent: with a debugger attached the device
 * is in Debug Interface mode and System OFF is emulated, so it stays reachable.
 */
static bool escape_held(void)
{
	if (!gpio_is_ready_dt(&escape_btn)) {
		return false;
	}

	if (gpio_pin_configure_dt(&escape_btn, GPIO_INPUT) < 0) {
		return false;
	}

	/* The devicetree spec carries GPIO_ACTIVE_LOW, so 1 means pressed. */
	return gpio_pin_get_dt(&escape_btn) == 1;
}
```

- [ ] **Step 2: Add the sleep**

Add above `main()`:

```c
static void sleep_until_next_cycle(void)
{
	int err = z_nrf_grtc_wakeup_prepare((uint64_t)CONFIG_SENSOR_CYCLE_SECONDS *
					    USEC_PER_SEC);

	if (err < 0) {
		/*
		 * This is the one failure that must not fall through to sleep.
		 * System OFF with no wake source never returns, so a device
		 * that sleeps here is gone until someone presses reset.
		 */
		printk("GRTC wake prepare failed (%d) — resetting instead\n", err);
		sys_reboot(SYS_REBOOT_COLD);
	}

	printk("sleeping %d s\n", CONFIG_SENSOR_CYCLE_SECONDS);
	k_msleep(50);   /* sys_poweroff() does not wait for the console */

	sys_poweroff();
}
```

- [ ] **Step 3: Restructure main around them**

Replace the body of `main()` so it reads:

```c
int main(void)
{
	uint64_t now_ms;
	struct bthome_values v;
	uint8_t svc[BTHOME_ADV_DATA_LEN];

	printk("\n=== bthome-sensor ===\n");

	if (escape_held()) {
		printk("Button 0 held — staying awake so the board can be flashed.\n");
		while (1) {
			k_sleep(K_FOREVER);
		}
	}

	now_ms = elapsed_ms();
	v = sim_values(now_ms);

	printk("elapsed %llu ms\n", now_ms);

	if (bthome_encode(&v, svc, sizeof(svc)) != BTHOME_ADV_DATA_LEN) {
		/* Never advertise a partial packet: a missing field rebinds
		 * SENSE2 to the wrong Home Assistant entity silently. Skipping
		 * the advertisement lets HA mark the entity stale, which is
		 * honest about what happened. */
		printk("encode failed — skipping this advertisement\n");
	} else {
		printk("payload:");
		for (size_t i = 0; i < sizeof(svc); i++) {
			printk(" %02X", svc[i]);
		}
		printk("\n");

		printk("battery %u%%  temp %d.%02d C  hum %u.%02u%%  m1 %u.%02u%%  m2 %u.%02u%%\n",
		       v.battery_pct, v.temperature_cc / 100,
		       (v.temperature_cc % 100 + 100) % 100,
		       v.humidity_cpct / 100, v.humidity_cpct % 100,
		       v.moisture1_cpct / 100, v.moisture1_cpct % 100,
		       v.moisture2_cpct / 100, v.moisture2_cpct % 100);

		advertise(svc);
	}

	sleep_until_next_cycle();

	return 0;   /* unreachable */
}
```

- [ ] **Step 4: Build with the dev overlay and flash**

The 30-second cycle makes this observable. Note the added `-DEXTRA_CONF_FILE=dev.conf`:

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor -- -DEXTRA_CONF_FILE=dev.conf && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

- [ ] **Step 5: Verify the cycle repeats on its own**

Watch the console for three minutes. Expected: a complete cycle roughly every 30 seconds, with `elapsed` climbing monotonically across them and `m1` decreasing slowly.

```
=== bthome-sensor ===
elapsed 31420 ms
payload: D2 FC 40 ...
battery 100%  temp 19.55 C  hum 37.02%  m1 79.98%  m2 75.98%
advertising 2000 ms
sleeping 30 s
```

Each cycle must begin with the banner — that is a cold boot, and it is how you tell real System OFF from an emulated one.

- [ ] **Step 6: Verify the escape hatch**

Hold Button 0 and press RESET. Expected:

```
=== bthome-sensor ===
Button 0 held — staying awake so the board can be flashed.
```

with no sleep afterwards. Confirm a flash succeeds while it sits in that state.

- [ ] **Step 7: Commit**

```bash
git add firmware/bthome-sensor/src/main.c
git commit -m "The real cycle: GRTC wake, System OFF, and an escape hatch

Every path reaches sys_poweroff() — at 1.5 uA, firmware that errors and loops
does not lose a reading, it flattens the cell. The one exception points the
other way: if arming the GRTC wake fails we reset instead of sleeping, because
System OFF with no wake source never returns.

Encode failure skips the advertisement rather than sending a partial packet,
since a missing field silently rebinds SENSE2 to the wrong entity.

Button 0 held at boot keeps the board programmable. DK only — our board gets
the same effect free from Debug Interface mode emulating System OFF."
```

---

### Task 6: Watchdog

The design marks this optional. Skip it and move to Task 7 if you would rather not carry it.

**Files:**
- Modify: `firmware/bthome-sensor/src/main.c`
- Modify: `firmware/bthome-sensor/prj.conf`

**Interfaces:**
- Consumes: `sleep_until_next_cycle()` from Task 5.
- Produces: `static void watchdog_start(void)`.

- [ ] **Step 1: Enable the driver**

Append to `firmware/bthome-sensor/prj.conf`:

```
CONFIG_WATCHDOG=y
```

- [ ] **Step 2: Add the watchdog**

Add to the includes in `main.c`:

```c
#include <zephyr/drivers/watchdog.h>
```

Add above `main()`:

```c
/*
 * Covers a hang while the radio is up. Halted in System OFF so it does not
 * fire during the sleep — the GRTC alarm owns that timing.
 *
 * The timeout is several times the advertising window; anything longer than
 * that awake means something is stuck.
 */
static void watchdog_start(void)
{
	const struct device *wdt = DEVICE_DT_GET(DT_NODELABEL(wdt31));
	struct wdt_timeout_cfg cfg = {
		.window.min = 0,
		.window.max = CONFIG_SENSOR_ADV_WINDOW_MS * 4,
		.callback = NULL,
		.flags = WDT_FLAG_RESET_SOC,
	};
	int err;

	if (!device_is_ready(wdt)) {
		printk("watchdog not ready — continuing without it\n");
		return;
	}

	if (wdt_install_timeout(wdt, &cfg) < 0) {
		printk("wdt_install_timeout failed — continuing without it\n");
		return;
	}

	err = wdt_setup(wdt, WDT_OPT_PAUSE_HALTED_BY_DBG);
	if (err < 0) {
		printk("wdt_setup failed (%d) — continuing without it\n", err);
	}
}
```

If `wdt31` is not the correct node label for this board, find it with:

```bash
docker run --rm --platform linux/amd64 -v ncs-build:/builds ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'grep -n "wdt[0-9]*:" /builds/bthome/bthome-sensor/zephyr/zephyr.dts'
```

- [ ] **Step 3: Call it, after the escape check**

In `main()`, immediately after the `escape_held()` block, add:

```c
	watchdog_start();
```

It goes after the escape check deliberately: the awake-forever state must not be reset every few seconds.

- [ ] **Step 4: Build, flash, and verify normal operation is unaffected**

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor -- -DEXTRA_CONF_FILE=dev.conf && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

```bash
cd /Users/alex/moisture-sensor-carrier/firmware && nrfutil device program --firmware .build-bthome.hex --options chip_erase_mode=ERASE_ALL --serial-number 1057774579 && nrfutil device reset --serial-number 1057774579
```

Expected: cycles continue every 30 seconds exactly as in Task 5, with no unexpected resets. A reset loop here means the timeout is shorter than a real cycle takes.

- [ ] **Step 5: Commit**

```bash
git add firmware/bthome-sensor/src/main.c firmware/bthome-sensor/prj.conf
git commit -m "Watchdog covering a hang while the radio is up

Installed after the escape check so holding Button 0 is not interrupted by
resets. Timeout is four times the advertising window; longer than that awake
means something is stuck."
```

---

### Task 7: Home Assistant verification and README

**Files:**
- Create: `firmware/bthome-sensor/README.md`
- Modify: `NEXT-STEPS.md`

**Interfaces:**
- Consumes: the working firmware from Tasks 2–6.
- Produces: documentation only.

- [ ] **Step 1: Build and flash the product-default build**

Note there is **no** `dev.conf` here — this is the hourly build, to confirm the committed default works:

```bash
docker run --rm --platform linux/amd64 -v ncs-src:/workdir -v ncs-build:/builds -v /Users/alex/moisture-sensor-carrier/firmware:/fw -w /workdir ghcr.io/nrfconnect/sdk-nrf-toolchain:v3.2.2 'source /opt/toolchain-env.sh; export ZEPHYR_BASE=/workdir/zephyr; west build -p always -b nrf54l15dk/nrf54l15/cpuapp -d /builds/bthome /fw/bthome-sensor && cp /builds/bthome/merged.hex /fw/.build-bthome.hex'
```

Confirm the console says `sleeping 3600 s`.

- [ ] **Step 2: Reflash the dev build for the HA check**

Waiting an hour per reading makes verification painful. Rebuild with `dev.conf` (the command in Task 5, Step 4) and flash.

- [ ] **Step 3: Verify in Home Assistant**

Home Assistant should discover the device automatically over its Bluetooth integration — BTHome needs no configuration beyond accepting the discovery.

Confirm all of:

- One device appears, named `Plant-1`.
- It has **five** entities: battery, temperature, humidity, moisture, moisture_2.
- `moisture` reads roughly four points **higher** than `moisture_2`. If `moisture_2` is the higher of the two, the ordering has been inverted somewhere and Task 1's ordering test needs re-reading.
- Values match the console print for the same cycle.
- Over ten minutes or so, both moisture entities trend downwards.
- **Only one device** exists after several cycles. A second device appearing means the identity is not stable and Task 3 did not hold.

- [ ] **Step 4: Write the README**

Create `firmware/bthome-sensor/README.md` covering: what the app does; the wake/advertise/sleep cycle; how to build with and without `dev.conf`; how to flash; that the console is VCOM1; the Button 0 escape hatch; how to run the host tests (`./tests/bthome/run.sh`); the packet layout table from the design; and the note that measurement order is load-bearing.

Link to the design at `docs/superpowers/specs/2026-08-04-bthome-firmware-design.md` rather than restating its reasoning.

- [ ] **Step 5: Update NEXT-STEPS.md**

In the DK section, record that BTHome firmware with simulated data is working and visible in Home Assistant, and note what remains: real sensor drivers (needs our board), encryption (needs the counter persisted), and the nPM1300 fuel gauge for real battery reporting (needs the EK, and the open question in HARDWARE.md §5 about its availability for nRF54L15).

- [ ] **Step 6: Commit and push**

```bash
git add firmware/bthome-sensor/README.md NEXT-STEPS.md
git commit -m "BTHome firmware verified end to end in Home Assistant

Five entities under one device, moisture reading above moisture_2 as designed,
one device across many cycles confirming the identity is stable.

Records what is left: real drivers need our board, encryption needs a
persisted counter, and real battery reporting needs the EK."
git push
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| Linear cycle, no state machine | 2, 5 |
| Pure BTHome encoder, host-tested | 1 |
| Packet layout, 17-byte service data | 1 |
| Ordering invariant, SENSE1 then SENSE2 | 1 (test), 7 (HA check) |
| Packet ID omitted | 1 (no packet-id field exists) |
| Stable FICR-derived identity | 3 |
| Non-connectable, 100 ms, 2 s window | 2 |
| GRTC SYSCOUNTER time base | 4 |
| Drying curve, pure function of clock | 4 |
| Button 0 escape hatch | 5 |
| Every path reaches `sys_poweroff()` | 5 |
| GRTC-arm failure resets instead | 5 |
| No partial packets | 5 |
| Watchdog, optional | 6 |
| Kconfig defaults | 2 |
| `dev.conf` 30 s override | 2, 5 |
| End-to-end HA verification | 7 |

**Deviation from the spec:** no `boards/nrf54l15dk_nrf54l15_cpuapp.overlay` is created. The spec's file listing included one, but the app uses only board-default aliases (`sw0`) and adds no pins, so an overlay would be an empty file. Noted in Task 2.

**Type consistency:** `struct bthome_values` field names and types are identical in Tasks 1, 2, 4 and 5. `bthome_encode()` is called with the same signature everywhere and its return compared against `BTHOME_ADV_DATA_LEN` in both the tests and `main()`. `elapsed_ms()` returns `uint64_t` and `sim_values()` takes `uint64_t` throughout.
