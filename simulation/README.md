# Reliability simulations

## openEMS

`openems/return_path.m` compares the old D8 return (two through-board transitions and bottom routing) with the revised nearby via and In1 ground finger in a controlled source-return fixture. It uses PEC conductors, εr=4.2 FR4 and an artificial return plate 3 mm above the board. It is **not** the assembled PCB, an IEC ESD generator, a semiconductor avalanche model, or the module antenna.

```sh
docker build -t moisture-openems:bookworm simulation/openems
docker run --rm -v "$PWD:/work" moisture-openems:bookworm \
  octave --no-gui --quiet simulation/openems/return_path.m baseline 0.2 /work/tmp/em-baseline
docker run --rm -v "$PWD:/work" moisture-openems:bookworm \
  octave --no-gui --quiet simulation/openems/return_path.m revised 0.2 /work/tmp/em-revised
```

The completed runs use openEMS 0.0.35 from Debian bookworm, 118,048 cells, 0.0539 ps time steps and stop below −40 dB residual energy. Floating-point mesh duplicates are rounded before smoothing. Initial discarded runs had an unused excitation or insufficient time span; those are not used in the reported comparison.

Results and exact XML inputs: `docs/reliability-2026-09-07/openems/`. In the 200–500 MHz band the revised fixture shows lower apparent inductance, but no independent mesh convergence run was completed. The baseline's negative extracted resistance near the upper frequency limit is a numerical artifact in a passive model. Do not use these curves to specify clamp voltages, ESD survival, radiated emissions, or antenna matching. A decay criterion alone does not validate port extraction.

## Electrostatic probe sweep

`electrostatics/solver.py` solves 2-D finite-volume electrostatics and passes a parallel-plate field/charge check. `probe_sweep.py` sweeps ideal lossless exterior εr=1/5/20/40 and εr=3 coating of 0.2/0.6/1.0 mm around a 20 mm wide, 1.6 mm thick board. It includes a 16 mm electrode and surrounding four-layer equipotential shield, with no backing copper below the electrode. Charge per length is multiplied by the 30 mm electrode length.

```sh
.venv-cq/bin/python -m unittest discover -s simulation/electrostatics
.venv-cq/bin/python simulation/electrostatics/probe_sweep.py
```

This needs NumPy/SciPy. It omits end fringing, the other electrode, lossy/conductive soil, exact shield cutouts and a finite-impedance shield driver. Reducing grid spacing from 0.2 to 0.1 mm changes results by up to 9.5%; moving the grounded outer boundary from 30 to 50 mm changes them by up to 24.6%. These are sensitivity calculations, not a calibrated moisture prediction. The strong boundary dependence is a reason to measure the finished probe.

A separate conservative surface-coupling calculation in the reliability report covers conductive material immediately outside the coating. Do not apply the benign lossless sweep to saline or conductive wet soil.
