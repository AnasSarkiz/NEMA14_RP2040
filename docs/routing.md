# Saved v1.8.2 routing

The authoritative routed geometry is `artifacts/board.circuit.json`, identical to `index.circuit.json`, SHA-256 `567b45bd3737600dee1f833c4ee0692e6d50375be05031324674f744f09bd12e`. Earlier DSN, SES, repair logs and trial reports are construction history. The current board uses four copper layers, a 35 × 35 × 1.6 mm outline, exact (±13, ±13) Ø3.2 mm NPTH mounts, same-edge outward USB sockets and the SMT JST-SH motor header. All 81 fitted components and seven bare test pads are on top.

Ground is filled on all four layers. Inner1 also contains named local signal and supply escapes allowed by the geometric checker; it is not an uninterrupted ground-only layer. Motor and bulk power nets are excluded from that escape policy. `artifacts/trace-width-review.json` records actual segment widths, current budgets and estimated temperature rises. These use at least 35 µm outer copper, 17.5 µm inner copper and 20 µm via plating as fabrication requirements, not measured manufactured values.

## USB qualification gap

The saved layout has these total copper centerline lengths by layer. These are whole branched net trees, **not point-to-point pair lengths or measured skew**.

| Net | Top mm | Inner1 mm | Inner2 mm | Bottom mm |
| --- | ---: | ---: | ---: | ---: |
| USB_DP | 12.665 | 0 | 0 | 9.366 |
| USB_DM | 8.129 | 0 | 5.296 | 7.228 |
| MCU_DP | 3.804 | 3.413 | 8.400 | 8.708 |
| MCU_DM | 2.104 | 0 | 0 | 8.407 |

D+ and D− therefore do not use the same set of routing layers. Current receipts establish net/pad correspondence, connectivity and clearances. They do not establish a coupled differential route, suitable impedance, pair skew, return continuity at layer transitions, or working USB enumeration. The remaining engineering review must examine actual connector-to-resistor-to-MCU paths against a specified stackup and nearby reference copper. A layer-area check or allowed-net list cannot substitute for that review. Any corrective routing must preserve approved USB positions and repeat all geometry/CAM checks.

## CAM distinction and limits

The native raw export's manufacturing audit is FAIL for BOM identity, exposed-pad paste, stencil and silkscreen findings. The separately prepared `artifacts/jlcpcb-review` order package passes its independent corrected-CAM audit, with copper, mask, outline and drill members copied byte-for-byte from the raw export. Use the corrected package for supplier review. No raw-export PASS is claimed.

Only the three declared grounded exposed-pad thermal locations may overlap lands; these require supplier approval of filling, capping and planarization. Eight USB shell joints need secondary soldering. Software checks and approximate copper-current screening do not establish USB signal integrity, buck stability, A4988 sense/return behavior, regenerative-energy handling, EMC, hardware operation, supplier assembly acceptance or rear-motor fit.
