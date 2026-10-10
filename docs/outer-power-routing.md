# Current outer-power routing

Final saved board SHA256 `b28a7426d8bedbb10ae2eef10f6111f28326407e30352b2011bd0beab7ab33bd`. Main motor and15V routes use top/bottom only, minimum0.45mm with individually proved native pin escapes/resistor leaves; sense0.30mm.

- A_PLUS: 0.45mm main minimum; 1 branched through vias.
- A_MINUS: 0.45mm main minimum; 1 branched through vias.
- B_PLUS: 0.45mm main minimum; 1 branched through vias.
- B_MINUS: 0.45mm main minimum; 1 branched through vias.
- PD_VBUS: 0.45mm main minimum; 10 branched through vias.
- SENSE1: 0.3mm main minimum; 0 branched through vias.
- SENSE2: 0.3mm main minimum; 0 branched through vias.

Phase vias are present. All-branch counts are not series transition counts. Actual CAM series transitions are in service-outer-power-cam.json. New ground/supply planes invalidate old return-resistance calculations; bench ground-bounce/current-sharing review remains required. BUCK_SW RMS thermal budget0.48A derives from pulse/average and ripple screens; transient≈0.921A is checked separately.
