# Saved copper

`artifacts/board.circuit.json` is delivery copper. `npm run build` renders/checks it without rerouting. The new RP2040 board is routed independently; no CH32 traces or routing sessions are reused.

The tscircuit local autorouter was attempted first, but timed out after 120 seconds without a completed result. `autorouter-attempt.json` and `tscircuit-routing.log` record that outcome. Future completed local runs save diagnostic copper separately as `artifacts/autorouted.circuit.json`. If it cannot produce a clean board, the permitted freerouting 2.0.1 fallback uses the actual rendered pad geometry and net identities. Four screw-head keepouts are retained on both layers. Exposed-pad ground vias are deliberate exceptions; every other via-in-pad is checked.

```sh
npm run source:check
npm run autoroute
python3 scripts/freeroute.py
XDG_CONFIG_HOME=/workspace/.config XDG_CACHE_HOME=/workspace/.cache \
java -Duser.home=/workspace/.freerouting -jar /workspace/freerouting-2.0.1.jar \
 --gui.enabled=false --api_server.enabled=false --router.stop_pass_no=25 \
 -de artifacts/freerouting-input.dsn -do artifacts/board.ses -mp 20 -mt 2
python3 scripts/import-session.py
npm run build
npm run export
npm run shorts
```

Keep the saved DSN, identity map, SES and final Circuit JSON together. A new routing run may choose different paths. Check reports apply only to the saved geometry. DRC and copper-short checks do not establish USB signal integrity, switch-mode power performance, rear fit, firmware completion or fabrication readiness.
