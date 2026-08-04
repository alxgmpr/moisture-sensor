/*
 * System OFF wake fire-test — nRF54L15 DK (PCA10156).
 *
 * Tests the Table 40 claim that moved PMIC_INT off P2.00 in HARDWARE.md §6:
 * P0 and P1 can wake the system, P2 cannot — no SENSE/DETECT, no GPIOTE.
 *
 * The device resets on wake, so the result is read from the reset cause on
 * the next boot rather than from anything that survives the sleep.
 *
 * T4a wakes from P0.04 and expects success. T4b asks for the same thing on a
 * P2 pin. The interesting part of T4b is that it should fail at
 * gpio_pin_interrupt_configure() with -ENOTSUP — the port cannot express the
 * request at all. That is a stronger result than grounding a pin and watching
 * nothing happen, which is also consistent with a loose jumper.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/sys/printk.h>

#define SETTLE_SECONDS 5

static const struct gpio_dt_spec wake =
	GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), wake_gpios);

static void report_reset_cause(void)
{
	uint32_t cause = 0;
	int err;

	err = hwinfo_get_reset_cause(&cause);
	if (err) {
		printk("reset cause unavailable (%d)\n", err);
		return;
	}

	printk("reset cause: 0x%08x%s%s%s\n", cause,
	       (cause & RESET_LOW_POWER_WAKE) ? " LOW_POWER_WAKE" : "",
	       (cause & RESET_PIN) ? " PIN" : "",
	       (cause & RESET_POR) ? " POR" : "");

	if (cause & RESET_LOW_POWER_WAKE) {
		printk("\n>>> WOKE FROM SYSTEM OFF <<<\n");
		printk("VERDICT: the configured pin can wake the system.\n\n");
	}

	/* Clear it, or the next boot reports this run's cause as its own. */
	hwinfo_clear_reset_cause();
}

int main(void)
{
	int err;

	printk("\n=== %s ===\n", CONFIG_TEST_LABEL);

	report_reset_cause();

	if (!gpio_is_ready_dt(&wake)) {
		printk("wake pin's GPIO port is not ready\n");
		return 0;
	}

	printk("wake pin: %s pin %d\n", wake.port->name, wake.pin);

	err = gpio_pin_configure_dt(&wake, GPIO_INPUT);
	if (err) {
		printk("gpio_pin_configure_dt: %d\n", err);
		return 0;
	}

	err = gpio_pin_interrupt_configure_dt(&wake, GPIO_INT_LEVEL_ACTIVE);
	if (err) {
		printk("gpio_pin_interrupt_configure_dt: %d%s\n", err,
		       (err == -ENOTSUP) ? "  (-ENOTSUP)" : "");
		printk("\nThis port cannot arm a level-sense wake.\n");
		printk("VERDICT: %s\n",
		       IS_ENABLED(CONFIG_TEST_EXPECT_WAKE)
			       ? "*** UNEXPECTED — a pin we rely on for wake cannot arm ***"
			       : "expected — confirms Table 40 for this port.");
		return 0;
	}

	printk("sense armed.\n");

	if (!IS_ENABLED(CONFIG_TEST_EXPECT_WAKE)) {
		printk("*** UNEXPECTED — this port was not supposed to arm. ***\n");
		printk("Continuing: if it also wakes, Table 40 is wrong.\n");
	}

	printk("\nRelease the wake pin now (leave it inactive).\n");
	printk("Entering System OFF in %d s. Assert the pin to wake.\n",
	       SETTLE_SECONDS);
	printk("If nothing happens, that is the result — press RESET to end the run.\n");

	k_sleep(K_SECONDS(SETTLE_SECONDS));

	printk("powering off.\n");
	/* Let the console drain; sys_poweroff() does not wait for the UART. */
	k_msleep(100);

	sys_poweroff();

	/* Reached only in Debug Interface mode, where System OFF is emulated
	 * (datasheet §5.2.1) — the CPU stays on and execution continues.
	 * Detach the debugger and power-cycle if you land here. */
	printk("\nStill running: System OFF was emulated (debugger attached).\n");
	printk("This run proves nothing. Detach the debugger and repeat.\n");

	while (1) {
		k_sleep(K_FOREVER);
	}

	return 0;
}
