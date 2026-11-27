# NEMA14 JST — REVIEW ONLY, DO NOT FABRICATE

This isolated coupon is not the controller. No manufacturing process is approved.

Select only EP_TV1, EP_TV2, EP_TV3 and EP_TV4 in SELECTIVE-FILL.csv, drill tool T10, nominal CAD hole0.30mm, proposed land0.75mm. Coupon origin is EP centre(0,0); do not use mapped controller coordinates with coupon Gerbers. A future controller package must regenerate its own XY/tool manifest. Never select every0.30mm via by diameter.

Proposed process for these four only: mechanical through drilling and barrel plating, nonconductive epoxy fill, cure, planarize, copper cap, ENIG. Top EP solderable; bottom via pads mask-covered. Fill/cap/flatness are not encoded in pcb_via or Excellon. Do not remove the plated drilling operation merely because a finished via is capped. Do not treat an open, tented or soldermask-plugged hole as equivalent.

Requested review targets, NOT approved specifications: surface copper cap≥5µm; local cap depression/protrusion≤25µm relative to surrounding EP copper. Confirm actual hole/tool/finished-size tolerances, minimum barrel/cap copper, registration, annular rings, voiding/fill integrity, inner-layer insulation and exact process availability/cost. Generic127/50µm recess/protrusion statements are not this QFN's acceptance limits.

Proposed stencil: four1.25mm squares, centres(±0.725,±0.725)mm,0.12mm foil;62.99% nominal aperture coverage. This is a labelled CAM adapter, not native JSX paste or approved assembly data. Actual solder contact, void distribution, paste/reflow and EP X-ray criteria need agreement for A4988SETTR-T.

The intended future four-layer stack is a screening reference, not an order selection. Obtain technical confirmation of the exact stack/process and assembly tier. Before any release, inspect production copper on all four layers, mask on both sides, paste, plated drill and the XY fill-selection drawing together. No supplier has been contacted.
