# Soil 1 dual-pad diagnosis — 2026-09-24

Device status over BLE reported firmware 0.2.27, a valid sample, no sample or storage error, and 2750 mV battery input. Its stored calibration remained SENSE1 2655/5658 fF and SENSE2 2618/5571 fF (dry/wet).

With the board in soil, the raw readings were SENSE1 3550 fF and SENSE2 2095 fF. The firmware's independent two-point conversions therefore produced about 29.8% and 0% respectively. The 0% is the explicit lower clamp because 2095 fF is below SENSE2's 2618 fF dry point; it is not a BLE parser or channel-order issue.

The user removed the board from soil while a connected Measure-now test sampled repeatedly. The out-of-soil readings settled near SENSE1 2220 fF and SENSE2 2076 fF. During reinsertion, SENSE2 changed sharply (8793, 4319, 2184, 2085, 2359, 3153 fF), proving the FDC channel is electrically responsive. The connection dropped before a settled in-soil reading could be captured. Those transients do not establish a stable soil sensitivity or a reliable wet endpoint for SENSE2. No calibration setting was written.

A 0.2.28 production image was built with the misleading BTHome count objects removed. Both moisture fields remain. Host tests, partition validation, DFU package validation, and signed-image key comparison passed. The image is at `output/firmware-0.2.28/`. It has **not** been uploaded: the sensor stopped advertising after reinsertion, and repeated BLE scans missed the subsequent expected windows. Resume with the radio/battery portion accessible, read a fresh settled in-soil sample, then decide whether per-channel calibration is justified. Do not turn the small initial 19 fF SENSE2 soil-minus-air difference into a claimed moisture percentage without a response test.
