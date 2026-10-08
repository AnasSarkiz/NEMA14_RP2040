# Native JLCPCB imports and schematic presentation

Current source has **67 fitted references**, each resolved from an exact JLCPCB CID using tsci import --jlcpcb --download --use-exact-footprint. The catalog maps references to MPNs and preserves original TSX and native OBJ/STEP hashes. The resolver rejects footprint/CAD overrides. J_MOTOR, J_DEBUG, J_BOOT and mounting holes are bare PCB features with no fitted model.

Native original footprint JSX remains unchanged. Active adapters add React compatibility, public model URLs and documented CAD anchor alignment; native mesh/model vertices are retained. Import provenance proves which supplier model was used, **not manufacturer dimensional fidelity**. Latest import/presentation/assembly reports must be rebuilt for final copper.

| Reference | Exact selected identity | Relevant review |
| --- | --- | --- |
| J_PD, J_DATA | C165948 TYPE-C-31-M-12 |16 physical contacts incl four shields; both openings at the same +Y edge, outward-facing; centers X±5.3 mm, 10.6 mm pitch; compact cable overmolds ≤10 mm wide require simultaneous physical fit check |
| C_BULK | C178585 Panasonic EEEFPV101XAP |100 µF±20%, 35 V; verified ripple/ESR primary data |
| R_REF_H | C23018 0603WAF3901T5E |3.9 kΩ, 1% |
| R_REF_L, R_PD | C441922 ERJPA3F1001V |1 kΩ, 1%, 0.25 W |
| R_SA, R_SB | C2930216 FRL0805FR240TS |0.24 Ω, 1%, 125 mW; hot/pulse qualification pending |
| U_VM_ISO | C131992 SN74CBTLV1G125DCKR |Exact 5-pinSC70 footprint; primary Ioff/pinmap verified |
| Q_DATA | C94514 MMBT3904-7-F |Exact SOT23 import; primary electrical evidence pending |
| R_VM_EN, R_VM_BLEED | C25804 0603WAF1002T5E |10 kΩ OE pull-up/output bleed |
| C_VM_ISO | C1525 CL05B104KO5NNNC |100 nF±10%, 16 V, 0402 switch bypass |

The 3.9 kΩ/1 kΩ reference divider sets 0.3508 A nominal peak; low-VREF accuracy is unqualified. C_BULK's manufacturer body height is 7.7±0.3 mm, but its fresh native STEP measures approximately 5.82 mm. Mechanical review preserves that model and separately checks the manufacturer maximum envelope; **USER_REVIEW remains explicit**.

Numbered landscape A4 sheets include chip-purpose notes and every physical pin. New notes describe VM isolation and active-low host sensing. Final report-presentation results must cover all 67 references and latest source/copper; historical 61-part reports do not validate this revision. See [BOM review](bom.md), [manufacturer evidence](component-evidence.md) and [mechanical fit](mechanical-fit.md).
