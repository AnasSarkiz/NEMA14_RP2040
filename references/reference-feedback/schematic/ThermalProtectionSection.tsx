import { revisionPlacement } from "../mechanical/revision-placement";
import { TMP102AIDRLR } from "../imports/TMP102AIDRLR";
import { logicTrace, schematicSheets } from "./config";

// Signal width requested by the sensor circuit. The validated route plan
// includes fine-pitch escapes and local supply/ground connections.
const thermalTrace = logicTrace;

const section = {
  schSheetName: schematicSheets.thermalProtection,
  schSectionName: "thermal_protection",
} as const;

/** Sensor is beside the larger DRV8825 package, beside its grounded thermal area.
 * GPIO26/27: I2C1 SDA/SCL. RP2040 software evaluates temperature thresholds.
 * ALERT is intentionally unconnected; the sensor does not gate driver enable.
 */
export const ThermalProtectionComponents = () => (
  <>
    <TMP102AIDRLR noConnect={["ALERT"]} name="U_TEMP" schWidth={1.6} schHeight={1.2} schPinStyle={{pin4: {marginLeft: 0.5}}}
      schPinArrangement={{
        leftSide: { pins: [1, 6], direction: "top-to-bottom" },
        rightSide: { pins: [3], direction: "top-to-bottom" },
        topSide: { pins: [5], direction: "left-to-right" },
        bottomSide: { pins: [2, 4], direction: "left-to-right" },
      }} {...section} {...revisionPlacement("U_TEMP", {x:-5.625,y:-8.25})} />
    <capacitor name="C_TEMP" capacitance="100nF" footprint="0402" maxDecouplingTraceLength={4}
      supplierPartNumbers={{ jlcpcb: ["C1525"] }}
      schOrientation="vertical" {...section} {...revisionPlacement("C_TEMP", {x:-5.625,y:-8.25})} />
    <resistor name="R_TEMP_SDA" resistance="4.7k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: ["C25900"] }}
      schOrientation="pos_bottom" {...section} {...revisionPlacement("R_TEMP_SDA", {x:-5.625,y:-8.25})} />
    <resistor name="R_TEMP_SCL" resistance="4.7k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: ["C25900"] }}
      schOrientation="pos_bottom" {...section} {...revisionPlacement("R_TEMP_SCL", {x:-5.625,y:-8.25})} />
    <resistor name="R_MCU_ENABLE_PD" resistance="100k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: ["C25741"] }}
      schOrientation="vertical" {...section} {...revisionPlacement("R_MCU_ENABLE_PD", {x:-5.625,y:-8.25})} />
  </>
);

export const ThermalProtectionTraces = () => (
  <>
    <trace name="TEMP_SDA" from=".MCU > .U1 > .GPIO26_ADC0" to=".U_TEMP > .SDA" schDisplayLabel="TEMP_SDA" {...thermalTrace} />
    <trace name="TEMP_SCL" from=".MCU > .U1 > .GPIO27_ADC1" to=".U_TEMP > .SCL" schDisplayLabel="TEMP_SCL" {...thermalTrace} />
    <trace name="TEMP_GND" from=".U_TEMP > .GND" to=".DRIVER > .EP" {...thermalTrace} thickness="0.3mm" />
    <trace name="TEMP_ADDR_0X48" from=".U_TEMP > .ADD0" to=".U_TEMP > .GND" {...thermalTrace}
      pcbPath={[".U_TEMP > .GND"]} />
    <trace name="TEMP_POWER" from=".U_TEMP > .V_POS" to=".MCU > .L_AVDD > .pin1" schDisplayLabel="V3V3" {...thermalTrace} />
    <trace name="TEMP_DECOUPLE" schDisplayLabel="V3V3" from=".C_TEMP > .pin1" to=".U_TEMP > .V_POS" {...thermalTrace} />
    <trace name="SDA_PULLUP" schDisplayLabel="TEMP_SDA" from=".R_TEMP_SDA > .pin1" to=".U_TEMP > .SDA" {...thermalTrace} />
    <trace name="SCL_PULLUP" schDisplayLabel="TEMP_SCL" from=".R_TEMP_SCL > .pin1" to=".U_TEMP > .SCL" {...thermalTrace} />
    <trace name="MCU_ENABLE_PULLDOWN" from=".R_MCU_ENABLE_PD > .pin1" to=".Q_PD_ENABLE > .source" schDisplayLabel="MCU_ENABLE" {...thermalTrace} />
    {["R_TEMP_SDA", "R_TEMP_SCL"].map(name => (
      <trace key={name} name={`${name}_3V3`} schDisplayLabel="V3V3" from={`.${name} > .pin2`} to=".U_TEMP > .V_POS" {...thermalTrace} />
    ))}
    <trace name="C_TEMP_GND" from=".C_TEMP > .pin2" to="net.GND" {...thermalTrace} />
    <trace name="R_MCU_ENABLE_PD_GND" from=".R_MCU_ENABLE_PD > .pin2" to=".R_SLEEP_PD > .pin2" {...thermalTrace} />
  </>
);
