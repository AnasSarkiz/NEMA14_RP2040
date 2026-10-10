import React from "react"
import { assembly } from "tscircuit"
import models from "./assets/assembly/models.json"

/** Complete reviewed motor/carrier/harness scene; PCB design entry is index.circuit.tsx.
 * Imported assembly CAD is the documented fallback for the exact NEMA14 motor.
 * No representative NEMA17 motor, six-pin harness or rear screw mounting is used.
 */
export default function Nema14Assembly() {
  return (
    <assembly.device name="NEMA14_INSTALLED_ASSEMBLY">
      <assembly.subassembly name="CONTROLLER" displayName="Controller: top fitted assembly"
        cadModel={{ glbUrl: models.CONTROLLER }} />
      <assembly.subassembly name="MOTOR" displayName="STEPperONLINE 14HM11-0404S: exact manufacturer CAD"
        cadModel={{ glbUrl: models.MOTOR }} />
      <assembly.part name="CARRIER" displayName="Front-M3 carrier: independent host mounting"
        cadModel={{ glbUrl: models.CARRIER }} />
      <assembly.subassembly name="MOTOR_HARNESS" displayName="HAR-001/002: four wires, PHR-4, contacts, splices and service loops"
        cadModel={{ glbUrl: models.MOTOR_HARNESS }} />
      <assembly.subassembly name="INSULATION_AND_RESTRAINT" displayName="Nomex barrier, PEEK supports/clamp and liner"
        cadModel={{ glbUrl: models.INSULATION_AND_RESTRAINT }} />
      <assembly.subassembly name="FASTENERS" displayName="Front M3, PCB M2.5 and restraint fasteners"
        cadModel={{ glbUrl: models.FASTENERS }} />
      <assembly.subassembly name="PD_CABLE" displayName="Tensility 10-06137: 15 V PD cable and reserved bend"
        cadModel={{ glbUrl: models.PD_CABLE }} />
      <assembly.subassembly name="DATA_CABLE" displayName="Tensility 10-06139: computer USB cable and reserved bend"
        cadModel={{ glbUrl: models.DATA_CABLE }} />
    </assembly.device>
  )
}

/** Physical assembly metadata; it does not create winding connections. */
export const motorHarness = [
  { pin: 1, color: "black", winding: "A+", driver: "OUT1A" },
  { pin: 2, color: "green", winding: "A−", driver: "OUT1B" },
  { pin: 3, color: "red", winding: "B+", driver: "OUT2A" },
  { pin: 4, color: "blue", winding: "B−", driver: "OUT2B" },
] as const
