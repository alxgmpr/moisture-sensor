# Enclosure evaluation — coin cell and holder retained

**Recommendation:** use the assembled bare PCB for Rev A bench prototypes and product visualization. Keep a future enclosure in the design plan, but make it a purpose-built split shell that closes around the PCB. The original Hammond 1551WK is a workable protective box after modification, but does not naturally implement that assembly concept. The best smaller catalog lead is the Hammond 1551LBK; it is not a drop-in replacement.

![Section comparison](section-comparison.svg)

## What was wrong with the previous render

The visualization followed the existing project's internal mounting posts: PCB underside 6.20 mm above the case bottom, board top approximately 7.80 mm. The probe and sensor slots were cut at that height. The original bottom molding reaches approximately 16.90 mm, so both openings were far below the case joint. This was a board-on-posts construction, not the intended board-between-halves construction.

The previous intersection check verified a static assembled position only. It did not establish that the PCB can be inserted through the two perpendicular closed slots. A seam-level opening lets the lower half receive the PCB and the upper half capture it, avoiding that insertion problem.

Simply raising the board to the 1551WK joint is insufficient. Its lid is shallow and the holder rises about 5.6 mm above the PCB. A seam-mounted board with components facing the shallow lid would lose the needed headroom. One would need a deeper cover, an inverted board facing into the deep half, or a custom split shell, together with new supports and a revised seal.

## Actual size budget

The CR2032 holder **and installed cell stay**. No PCB or BOM edits were made.

Measured from the current Blender/CAD meshes (`height-audit.json`):

| Feature | Envelope |
|---|---:|
| PCB outline, including side sensor tab and probe | 42 × 155 mm |
| Main electronics region, excluding side tab/probe | 34 × 74 mm |
| Nominal PCB thickness | 1.6 mm |
| Holder top above PCB underside | 7.18 mm |
| Holder height above component-side board surface | 5.60 mm |
| Radio module top above PCB underside | 3.18 mm |

A custom shell's first-pass thickness budget is approximately 7.2 mm assembly + 3.0 mm total wall thickness + 1.5–3.0 mm combined internal clearance/support allowance = **11.7–13.2 mm**. A **12–14 mm external thickness target** is therefore plausible, subject to actual holder/cell geometry, fasteners, board retention and RF clearance. This is an engineering estimate, not a fit-certified case. The holder CAD is the project's existing visualization substitute; measure the chosen physical holder before releasing the shell.

## Catalog alternatives checked

| Option | Published size | Assessment for this PCB |
|---|---|---|
| [Hammond 1551WKBK](https://www.hammfg.com/files/parts/pdf/1551WKBK.pdf), current | 80 × 40 × 22 mm; 17.3 mm interior height | Enough height on existing posts; original gasketed box geometry. Poor match for a seam-clamped board without redesign. |
| [Hammond 1551LBK](https://www.hammfg.com/part/1551LBK) | 80 × 40 × 15 mm; maximum PCB 74.5 × 34.5 mm | Most relevant slimmer stock candidate: 7 mm / 32% thinner with the same nominal footprint. Board outline and posts still need a new CAD fit check. |
| [Takachi PS-85](https://takachi-enclosure.com/products/PS) | 85 × 48 × 15 mm; listed internal region 60.1 × 38.7 × 6 mm | Reject for unchanged PCB: listed usable internal length is below the 74 mm electronics section. It would require substantial board/case redesign. |
| Custom split shell | Initial target roughly 80 × 40 × 12–14 mm, with local adjustment for the antenna and retention | Best way to implement the intended seam capture, probe exit and separate side sensor opening together. Prototype first; dimensions are a starting budget. |

The [1551L manufacturer drawing](https://www.hammfg.com/files/parts/pdf/1551LTBU.pdf), revision 31 August 2023, shows 11.0 mm internal height, **3.0 mm PCB posts and 8.0 mm clearance above those posts** in section A–A. Using the current 7.18 mm assembled height leaves approximately **0.82 mm nominal headroom**. This is a plausible height fit, although physical holder dimensions and molding tolerances still need checking. The drawing specifies two PCB mounting holes on a **40 × 28.5 mm** offset pattern, unlike the current four-hole 55 × 25 mm pattern. Its shallow lid also does not naturally support component-side-up seam capture. Treat it as a promising lower-profile shell to adapt with new retention and passages, not something ready to assemble unchanged. The section drawing was visually checked in `1551L-section.png`; the 3.8 mm dimension in section B–B is not the PCB-post height.

The 1551LBK's IP54 catalog rating is for the unmodified enclosure; the probe and sensor openings need their own sealing design. The existing 1551WK gasket also cannot maintain its original sealing path through a seam interrupted by the PCB. If sealing is later required, use local compliant seals at the probe and tab passages rather than assuming the stock gasket handles them.

## Direction for a later case

- Put the split at the PCB passage plane, using locating ledges and positive compression stops. Capture appropriate bare board edges or mounting-hole regions, not components or fragile sensor/probe necks.
- Allocate most depth to the holder side and use a shallow protective half on the opposite side. Retain access for cell replacement.
- Keep the SHT45 sensing aperture exposed to air and maintain a load path from the probe into the case without stressing the thin shoulder or sensor tab.
- Keep conductive fasteners and coatings out of the module antenna region. The existing project already identifies enclosure RF validation as unresolved.

For Rev A, deferring the enclosure is sensible for bench characterization, firmware/radio testing and assembly checks. It does not make an unprotected board a finished wet-soil/outdoor product. The probe protection/coating and electronics moisture protection still require an intentional approach for field trials.

## Product film

`moisture-sensor-turntable.blend` contains the populated PCB, original holder model, installed CR2032 model, and DNP U1 module. The enclosure is omitted. The film uses a warm-white seamless studio surface, soft shadows, broad reflections and an eight-second continuous 360-degree rotation at 24 fps. The project remains editable and true-scale. There is no music, branding or invented circuitry.
