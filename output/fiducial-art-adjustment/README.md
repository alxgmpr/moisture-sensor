# Fiducials moved clear of the user-positioned sprout

- FID1: (88, 99.5) → (88.5, 100.5) mm.
- FID2: (83, 103) → (77.5, 102.5) mm.
- FID3 and FID4 unchanged. Existing fiducial pad/mask geometry and assembly exclusions retained.

Moved through KiCad IPC, refilled zones, and saved the maintained board.
Artwork, grouping, all other footprints, tracks, arcs, and vias are unchanged.
The minimum distance from each new center to the sprout ink is 1.725 mm
(FID1) and 2.608 mm (FID2), clearing the 1 mm mask-opening radius.

Native DRC: 45 → 40 violations, resolving five silk-over-copper violations,
with no new violation identities and zero unconnected items. All three
fiducial/tooling regression tests pass. The remaining 40 issues predate this
artwork conflict. Visually reviewed `after-detail.png` and `after.svg`.

Previously exported fabrication packages were not regenerated.
