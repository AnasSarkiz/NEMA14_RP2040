import { Children, cloneElement, type ReactElement } from "react";
import type { ChipProps } from "@tscircuit/props";
import { TYPE_C_31_M_12 as JlcUsbC } from "./TYPE_C_31_M_12";

// Preserve the established schematic pin numbering; all physical geometry and
// CAD data come unchanged from the exact C165948 EasyEDA supplier import.
// Shell positions, rather than vendor EH numbering, determine this mapping.
const supplierToLegacyPin: Record<number, number> = {
  1: 2, 2: 4, 3: 3, 4: 1, 5: 7, 6: 8, 7: 9, 8: 10,
  9: 11, 10: 12, 11: 13, 12: 14, 13: 5, 14: 16, 15: 15, 16: 6,
};
const imported = JlcUsbC({name: "USB"}).props;
function supplierFootprint(offset: number) {
  const footprint = imported.footprint as ReactElement<{children: ReactElement[]}>;
  return cloneElement(footprint, {}, Children.map(footprint.props.children, child => {
    const pad = child as ReactElement<{portHints?: string[]}>;
    if (!pad.props.portHints) return pad;
    return cloneElement(pad, {portHints: pad.props.portHints.map(hint => {
      const pin = supplierToLegacyPin[Number(hint.replace("pin", ""))];
      if (!pin) throw new Error(`Unmapped C165948 pin: ${hint}`);
      return `pin${pin + offset}`;
    })});
  }));
}
const motorPinLabels = {
  pin1: ["EH1", "SHELL1"],
  pin2: ["EH2", "SHELL2"],
  pin3: ["EH3", "SHELL3"],
  pin4: ["EH4", "SHELL4"],
  pin5: ["A1B12", "GND1"],
  pin6: ["A4B9", "VBUS1"],
  pin7: ["B8", "SBU2"],
  pin8: ["A5", "CC1"],
  pin9: ["B7", "DM2"],
  pin10: ["A6", "DP1"],
  pin11: ["A7", "DM1"],
  pin12: ["B6", "DP2"],
  pin13: ["A8", "SBU1"],
  pin14: ["B5", "CC2"],
  pin15: ["B4A9", "VBUS2"],
  pin16: ["B1A12", "GND2"],
} as const;

const controllerPinLabels = {
  pin13: ["EH1", "SHELL1"],
  pin14: ["EH2", "SHELL2"],
  pin15: ["pin13_alt1", "SHELL3"],
  pin16: ["pin14_alt1", "SHELL4"],
  pin17: ["A1B12", "GND1"],
  pin18: ["A4B9", "VBUS1"],
  pin19: ["B8", "SBU2"],
  pin20: ["A5", "CC1"],
  pin21: ["B7", "DM2"],
  pin22: ["A6", "DP1"],
  pin23: ["A7", "DM1"],
  pin24: ["B6", "DP2"],
  pin25: ["A8", "SBU1"],
  pin26: ["B5", "CC2"],
  pin27: ["B4A9", "VBUS2"],
  pin28: ["B1A12", "GND2"]
} as const;

export const MotorUsbC = (props: ChipProps<typeof motorPinLabels>) => (
  <connector {...imported} standard="usb_c" pinLabels={motorPinLabels}
    footprint={supplierFootprint(0)} {...props}/>
);
export const ControllerUsbC = (props: ChipProps<typeof controllerPinLabels>) => (
  <connector {...imported} standard="usb_c" pinLabels={controllerPinLabels}
    footprint={supplierFootprint(12)} {...props}/>
);
