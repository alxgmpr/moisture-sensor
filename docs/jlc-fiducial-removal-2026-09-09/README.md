# Remove optional copper fiducials

Removed FID1–FID4 from the PCB and their three schematic symbols plus unused cached symbol definition. Retained TH1–TH3 for Economic assembly. Restored the four GND stitching vias previously removed only for fiducial clearance; the via removed for TH1 remains absent. Refilled zones and regenerated the Economic assembly package.

Validation: no unconnected items or schematic parity issues; DRC remains at two previously accepted keepout errors and 38 warnings. ERC has no errors. Four alignment/package tests pass. BOM and CPL contain 38 fitted components. Current package: `production/jlc-economic-quote/JLC-Gerbers.zip`.
