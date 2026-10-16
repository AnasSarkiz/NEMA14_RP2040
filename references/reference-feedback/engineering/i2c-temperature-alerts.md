# I²C-only temperature monitoring — v1.0.34

Removed R_TEMP_ALERT (10 kΩ, C25744), its 3.3 V branch, all TMP102 ALERT-to-GPIO24 signal traces, the GPIO24 escape via and the TEMP_OK net/labels. TMP102 pin 3 (ALERT) and RP2040 GPIO24 are explicitly unconnected. Assembly decreases from 104 to 103 top-side components.

TMP102 remains at I²C address 0x48 using GPIO26/SDA and GPIO27/SCL. C_TEMP and R_TEMP_SDA/R_TEMP_SCL remain. Application software must poll temperature and implement its own thresholds, hysteresis, sensor-failure handling and alerts. No firmware is included in this PCB package.

The former external thermal AND gate remains absent. The MCU/USB-PD enable path and the DRV8825 internal die-temperature protection are unchanged. Configurable CH224K selection on GPIO4/5/6 is unchanged.

Surviving components keep their placements. Saved routes are remapped by component/pin identity, with manual vias matched by position. The obsolete ALERT routes and resistor supply branch are removed; ground copper is regenerated and audited. The electrical regression rejects any reconnect of ALERT or GPIO24 as well as loss of the I²C supply/interface or PD enable path.

See [current verification results](revision-checks.json). This revision is local, not published, and has not been tested on physical hardware.
