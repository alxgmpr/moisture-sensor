# BL54L15 carrier firmware port

The repository applications currently target the nRF54L15 DK; this migration
does not silently change those bench targets into a production carrier build.
The following are required when adding the carrier board definition. Hardware
has not been built or measured, so these settings are not a qualified release.

## GPIO and programming

No product GPIO assignments changed: SCL=P1.11 (module35), SDA=P1.10 (28),
PMIC_INT=P0.00 (17), SWO=P2.07 (4). Dedicated SWDIO/SWDCLK/nRESET are module5/6/7.
J4 and its reset connection to nPM2100 PG/RESET are unchanged. The module ships
without application firmware; program through J4. P1.00/P1.01 are reserved
for XL1/XL2; never enable them as digital outputs while X1 is fitted. Unused
module pins are NC in the schematic; disconnect unused input buffers in sleep.

## Crystal configuration

X1 remains CM8V-T1A, 32.768 kHz, **CL=7 pF**, ±20 ppm. Its terminals connect
only to module25 XL1 and module24 XL2. There are no discrete load capacitors.
Use internal load banks and the device-specific FICR calibration through the
SDK oscillator driver before LFXO startup.

**Corrected from the old hardware notes:** CL is the crystal's total load across
its terminals. The current Nordic devicetree guidance says
`load-capacitance-femtofarad` selects the internal capacitor, not CL directly.
For equal legs, use `CL ≈ (CINT + Cadditional_per_leg)/2`, where additional
loading includes host/module traces and pin loading not already represented by
the trimmed bank. Do not count the same calibrated pin loading twice. Thus 7 pF
CL needs approximately 14 pF per leg before subtracting those parasitics.

An initial engineering estimate of 2 pF additional loading per leg gives
**CINT≈12 pF**; 1–3 pF would imply 13–11 pF. Start from a supported setting near
12,000 fF and tune on the assembled board. This is an explicit parasitic
assumption, not a measured or vendor-certified trim. Neither 7,000 fF copied
from CL nor the Ezurio DVK's 15,500 fF should be inherited without calculation.
Verify the selected SDK's binding/driver and generated secure-image devicetree;
then measure frequency, cold/low-voltage startup, drive margin and temperature
behavior using a buffered clock output or appropriate low-loading technique.
Do not probe crystal pins with an ordinary oscilloscope probe.

Example carrier starting point (not applied to DK applications):

```dts
&lfxo {
    load-capacitors = "internal";
    load-capacitance-femtofarad = <12000>; /* Initial estimate; trim on carrier. */
    status = "okay";
};

&hfxo {
    load-capacitors = "internal";
    load-capacitance-femtofarad = <15000>; /* BL54L15 DVK module starting value. */
    status = "okay";
};
```

The module contains its own 32 MHz crystal, with the load banks inside the SoC.
The 15,000 fF HFXO starting value follows the upstream Ezurio BL54L15 DVK board
configuration for this module; it is not the old bare-board X2 CL=8 pF value.
Verify HFXO startup and frequency with the intended SDK and module revision.
Enable the SoC's main DC/DC regulator using that SDK's regulator binding; the
inductor and rail support are in the module, so no host DCC wiring is needed.

Select LFXO as LFCLK and retain the System OFF/GRTC timed-wake design. Wait for
clock startup, configure/retain the required low-frequency/GRTC domain, arm the
wake deadline, and test repeated timed System OFF cycles at voltage and
temperature limits. A DK wake test alone does not verify the new carrier layout.

## nPM2100 and radio

Keep 3.3 V VOUT and the existing FDC load-switch/I²C sequencing. Extend the
existing force-HP measurement window to cover **every radio TX/RX window** and
its settling time. LP/ULP has about 70 mVpp typical ripple; Ezurio permits at most
10 mV supply ripple/noise for undisturbed radio operation. HP is a mitigation,
not a guaranteed 10 mV specification. Measure at module26 with a short ground
spring over relevant bandwidth, including startup, transitions and depleted-
cell bursts. Revisit filtering if it fails; account for the module input
capacitance in nPM2100's effective VOUT-capacitance limit. Recalculate the battery
budget from measured module and converter current. Never switch off VOUT while
relying on SoC System OFF/GRTC wake.

## Sources (accessed 2026-09-04)

- [Ezurio module datasheet](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series), Clocks, Circuit Checklist, Pin-Out and operating conditions.
- [Nordic LFXO internal capacitor model](https://docs.nordicsemi.com/r/bundle/ngl_001/page/gl/ngl_001/lfxo_internal_capacitor.html) and [LFXO devicetree](https://docs.nordicsemi.com/r/bundle/ngl_001/page/gl/ngl_001/lfxo_devicetree.html).
- [Zephyr nRF54L LFXO binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/clock/nordic,nrf54l-lfxo.html) and [factory-trim implementation](https://github.com/zephyrproject-rtos/zephyr/blob/main/soc/nordic/nrf54l/soc.c).
- [Ezurio BL54L15 DVK clock/regulator configuration](https://github.com/zephyrproject-rtos/zephyr/blob/main/boards/ezurio/bl54l15_dvk/nrf54l_10_15_cpuapp_common.dtsi). This is a module reference, not a carrier pin assignment.
- Local Nordic nPM2100 Datasheet v1.0, boost operating modes and external component limits.
