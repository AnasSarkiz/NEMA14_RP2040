# Current exact-part evidence

See [engineering review](engineering-review.md), [operating envelope](supported-operating-envelope.md), `references/manufacturer-review.json` → `independent_revision`, and `artifacts/engineering/service-power-review.json` for current identities, calculations, limitations and primary PDF/curve hashes. The old entries retained in manufacturer-review.json are explicitly historical and superseded where they describe removed components.

Exact active TVS: Littelfuse SMF4L16A/C1973135; exact active USB ESD: ST USBLC6-2SC6/C7519. Both retain native supplier footprints/STEP/OBJ. Supplier stock and pickup/rotation acceptance must be reconfirmed; current availability is not a design guarantee. RP buck input CL32B106KBJNNNE/C138687, output3×CL21A226MAQNNNE/C45783 and Bourns SRN4018-4R7M/C780206 have primary manufacturer evidence; typical bias curves do not prove lifetime minima or assembled loop stability.

Holtek absolute junction maximum150 °C, operating input30 V and absolute input33 V come from Rev2.81.125 °C is a design target, not its rating. JST generic CAD post discrepancy, real cable dimensions/registration, factory motor lead stock and all material/process certificates remain qualification gaps. No primary condition is replaced by a supplier marketing rating.
