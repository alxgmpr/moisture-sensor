/*
 * Line-state probe — tells apart the three things a dead I2C bus can mean.
 *
 * Written because T3-control failed with -ENODEV, which is equally consistent
 * with a loose jumper, a pin held by something else on the DK, and the port
 * rule actually being enforced. Reading each line under three different
 * internal-pull settings separates them without touching the wiring:
 *
 *   pull-down reads 1, pull-up reads 1   external pull-up present — wire is good
 *   pull-down reads 0, pull-up reads 1   floating — nothing on the other end
 *   pull-up   reads 0                    driven low by something else
 *
 * The nRF internal pulls are around 13 kOhm, so a 10 kOhm external pull-up
 * beats an internal pull-down but not by much. Treat the pull-down column as
 * indicative; the pull-up column reading 0 is the decisive one.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/printk.h>

struct probe_pin {
	const struct device *port;
	gpio_pin_t pin;
	const char *name;
	const char *note;
};

#define P0 DEVICE_DT_GET(DT_NODELABEL(gpio0))
#define P1 DEVICE_DT_GET(DT_NODELABEL(gpio1))

static int read_with(const struct probe_pin *p, gpio_flags_t pull)
{
	int err;

	err = gpio_pin_configure(p->port, p->pin, GPIO_INPUT | pull);
	if (err) {
		return err;
	}

	/* Let the pull settle against whatever capacitance is on the line. */
	k_msleep(2);

	return gpio_pin_get_raw(p->port, p->pin);
}

int main(void)
{
	const struct probe_pin pins[] = {
		{ P0, 3, "P0.03", "UART0 CTS, driven by debugger during HWFC detect" },
		{ P0, 4, "P0.04", "Button 3, no external pull-up per DK guide" },
		{ P1, 11, "P1.11", "clean, T1/T3 SCL" },
		{ P1, 10, "P1.10", "LED 1 gate, T1/T2 SDA" },
	};

	printk("\n=== line-state probe ===\n");
	printk("%-6s %6s %6s %6s   %s\n", "pin", "nopull", "pulldn", "pullup", "reading");

	for (size_t i = 0; i < ARRAY_SIZE(pins); i++) {
		const struct probe_pin *p = &pins[i];
		int nopull, pulldn, pullup;
		const char *verdict;

		if (!device_is_ready(p->port)) {
			printk("%-6s port not ready\n", p->name);
			continue;
		}

		nopull = read_with(p, 0);
		pulldn = read_with(p, GPIO_PULL_DOWN);
		pullup = read_with(p, GPIO_PULL_UP);

		if (nopull < 0 || pulldn < 0 || pullup < 0) {
			printk("%-6s read error\n", p->name);
			continue;
		}

		if (pullup == 0) {
			verdict = "DRIVEN LOW by something else";
		} else if (pulldn == 1) {
			verdict = "external pull-up present — wire good";
		} else {
			verdict = "floating — nothing on the other end";
		}

		printk("%-6s %6d %6d %6d   %s\n", p->name, nopull, pulldn, pullup, verdict);

		/* Leave the pin high-impedance rather than holding a pull on
		 * a line the next test will use. */
		gpio_pin_configure(p->port, p->pin, GPIO_DISCONNECTED);
	}

	printk("\nnotes:\n");
	for (size_t i = 0; i < ARRAY_SIZE(pins); i++) {
		printk("  %-6s %s\n", pins[i].name, pins[i].note);
	}

	return 0;
}
