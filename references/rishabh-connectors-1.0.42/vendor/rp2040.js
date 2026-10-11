import { ABM8_272_T3 } from "../imports/jlc/C20625731";
import { ControllerUsbC } from "../imports/usb-c-20v";
import { RP2040 as JlcRP2040 } from "../imports/jlc/RP2040";
import { W25Q16JVUXIQ as JlcFlash } from "../imports/jlc/W25Q16JVUXIQ";
import { AP2112K_3_3TRG1 as JlcRegulator } from "../imports/jlc/AP2112K_3_3TRG1";
// node_modules/@tscircuit/common/dist/index.js
import { jsx, jsxs } from "react/jsx-runtime";
import { jsx as jsx2, jsxs as jsxs2 } from "react/jsx-runtime";
import React from "react";
import { jsxs as jsxs3 } from "react/jsx-runtime";
import { jsx as jsx3, jsxs as jsxs4 } from "react/jsx-runtime";
import { jsx as jsx4, jsxs as jsxs5 } from "react/jsx-runtime";
import React2 from "react";
import { jsx as jsx5 } from "react/jsx-runtime";
import { jsx as jsx6, jsxs as jsxs6 } from "react/jsx-runtime";
import { jsx as jsx7, jsxs as jsxs7 } from "react/jsx-runtime";
import React3 from "react";
import { jsx as jsx8 } from "react/jsx-runtime";
import { jsx as jsx9, jsxs as jsxs8 } from "react/jsx-runtime";

// node_modules/@tscircuit/math-utils/dist/chunk-U45EKA3R.js
function grid({
  rows,
  cols,
  xSpacing,
  ySpacing,
  width,
  height,
  offsetX = 0,
  offsetY = 0,
  yDirection = "cartesian",
  centered = true
}) {
  const effectiveXSpacing = xSpacing ?? 1;
  const effectiveYSpacing = ySpacing ?? 1;
  const totalWidth = width ?? cols * effectiveXSpacing;
  const totalHeight = height ?? rows * effectiveYSpacing;
  const centeringOffsetX = centered ? -totalWidth / 2 : 0;
  const centeringOffsetY = centered ? -totalHeight / 2 : 0;
  const cellWidth = width ? width / cols : effectiveXSpacing;
  const cellHeight = height ? height / rows : effectiveYSpacing;
  const cells = [];
  for (let row = 0;row < rows; row++) {
    for (let col = 0;col < cols; col++) {
      const index = row * cols + col;
      const centerX = offsetX + centeringOffsetX + col * cellWidth + cellWidth / 2;
      const rawCenterY = offsetY + row * cellHeight + cellHeight / 2;
      const centerY = yDirection === "cartesian" ? offsetY + centeringOffsetY + (rows - 1 - row) * cellHeight + cellHeight / 2 : offsetY + centeringOffsetY + row * cellHeight + cellHeight / 2;
      cells.push({
        index,
        center: { x: centerX, y: centerY },
        topLeft: {
          x: centerX - cellWidth / 2,
          y: centerY + cellHeight / 2
        },
        bottomRight: {
          x: centerX + cellWidth / 2,
          y: centerY - cellHeight / 2
        },
        row,
        col
      });
    }
  }
  return cells;
}

// node_modules/@tscircuit/common/dist/index.js
import { jsx as jsx10, jsxs as jsxs9 } from "react/jsx-runtime";
import { jsx as jsx11, jsxs as jsxs10 } from "react/jsx-runtime";
import { jsx as jsx12 } from "react/jsx-runtime";
import { jsx as jsx13 } from "react/jsx-runtime";
import { jsx as jsx14 } from "react/jsx-runtime";
import { jsx as jsx15 } from "react/jsx-runtime";
import { jsx as jsx16 } from "react/jsx-runtime";
import { jsx as jsx17 } from "react/jsx-runtime";
import { jsx as jsx18 } from "react/jsx-runtime";
import { jsx as jsx19 } from "react/jsx-runtime";
import { jsx as jsx20, jsxs as jsxs11 } from "react/jsx-runtime";
import { jsx as jsx21, jsxs as jsxs12 } from "react/jsx-runtime";
import { jsx as jsx22, jsxs as jsxs13 } from "react/jsx-runtime";
import { jsx as jsx23, jsxs as jsxs14 } from "react/jsx-runtime";
import { jsx as jsx24, jsxs as jsxs15 } from "react/jsx-runtime";
import { jsx as jsx25, jsxs as jsxs16 } from "react/jsx-runtime";
import { jsx as jsx26, jsxs as jsxs17 } from "react/jsx-runtime";
import { jsx as jsx27, jsxs as jsxs18 } from "react/jsx-runtime";
import { jsx as jsx28, jsxs as jsxs19 } from "react/jsx-runtime";
import { jsx as jsx29, jsxs as jsxs20 } from "react/jsx-runtime";
import { jsx as jsx30, jsxs as jsxs21 } from "react/jsx-runtime";
import { jsx as jsx31, jsxs as jsxs22 } from "react/jsx-runtime";
import { jsx as jsx32, jsxs as jsxs23 } from "react/jsx-runtime";
import { jsx as jsx33, jsxs as jsxs24 } from "react/jsx-runtime";
import { jsx as jsx34, jsxs as jsxs25 } from "react/jsx-runtime";
import { jsx as jsx35, jsxs as jsxs26 } from "react/jsx-runtime";
import { jsx as jsx36, jsxs as jsxs27 } from "react/jsx-runtime";
var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __pow = Math.pow;
var __defNormalProp = (obj, key, value) => (key in obj) ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
var __objRest = (source, exclude) => {
  var target = {};
  for (var prop in source)
    if (__hasOwnProp.call(source, prop) && exclude.indexOf(prop) < 0)
      target[prop] = source[prop];
  if (source != null && __getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(source)) {
      if (exclude.indexOf(prop) < 0 && __propIsEnum.call(source, prop))
        target[prop] = source[prop];
    }
  return target;
};
var OutlineBuilder = class {
  constructor(startX, startY) {
    this.points = [];
    this.lastDirection = null;
    this.currentX = startX;
    this.currentY = startY;
    this.points.push({ x: startX, y: startY });
  }
  updateDirection(x, y) {
    if (x > this.currentX)
      this.lastDirection = "right";
    else if (x < this.currentX)
      this.lastDirection = "left";
    else if (y > this.currentY)
      this.lastDirection = "down";
    else if (y < this.currentY)
      this.lastDirection = "up";
  }
  lineTo(x, y) {
    if (x !== this.currentX || y !== this.currentY) {
      this.updateDirection(x, y);
      this.currentX = x;
      this.currentY = y;
      this.points.push({ x, y });
    }
    return this;
  }
  dirToUnit(dir) {
    switch (dir) {
      case "right":
        return { x: 1, y: 0 };
      case "left":
        return { x: -1, y: 0 };
      case "down":
        return { x: 0, y: 1 };
      case "up":
        return { x: 0, y: -1 };
    }
  }
  outgoingFor(last, turn) {
    switch (last) {
      case "right":
        return turn === "cw" ? { unit: { x: 0, y: 1 }, dir: "down" } : { unit: { x: 0, y: -1 }, dir: "up" };
      case "left":
        return turn === "cw" ? { unit: { x: 0, y: -1 }, dir: "up" } : { unit: { x: 0, y: 1 }, dir: "down" };
      case "down":
        return turn === "cw" ? { unit: { x: -1, y: 0 }, dir: "left" } : { unit: { x: 1, y: 0 }, dir: "right" };
      case "up":
        return turn === "cw" ? { unit: { x: 1, y: 0 }, dir: "right" } : { unit: { x: -1, y: 0 }, dir: "left" };
    }
  }
  corner({ radius, turn }) {
    if (this.points.length < 2) {
      throw new Error("Need at least two points to create a corner");
    }
    if (!this.lastDirection) {
      throw new Error("Cannot create a corner without a known incoming direction");
    }
    const ix = this.currentX;
    const iy = this.currentY;
    const prevIndex = this.points.length - 2;
    const prevPoint = this.points[prevIndex];
    this.points.pop();
    const incomingUnit = this.dirToUnit(this.lastDirection);
    const { unit: outgoingUnit, dir: outgoingDir } = this.outgoingFor(this.lastDirection, turn);
    const dxPrev = ix - prevPoint.x;
    const dyPrev = iy - prevPoint.y;
    const distPrev = Math.hypot(dxPrev, dyPrev);
    const r = Math.min(radius, distPrev);
    const startX = ix - incomingUnit.x * r;
    const startY = iy - incomingUnit.y * r;
    const endX = ix + outgoingUnit.x * r;
    const endY = iy + outgoingUnit.y * r;
    const inVec = { x: -incomingUnit.x, y: -incomingUnit.y };
    const outVec = { x: outgoingUnit.x, y: outgoingUnit.y };
    const bisector = { x: inVec.x + outVec.x, y: inVec.y + outVec.y };
    const bisLen = Math.hypot(bisector.x, bisector.y);
    let dot = inVec.x * outVec.x + inVec.y * outVec.y;
    dot = Math.max(-1, Math.min(1, dot));
    const angle = Math.acos(dot);
    if (bisLen < 0.000000001 || Math.abs(Math.sin(angle / 2)) < 0.000000001) {
      this.points.push({ x: ix, y: iy });
      this.currentX = ix;
      this.currentY = iy;
      return this;
    }
    const offset = r / Math.sin(angle / 2);
    const bisUnit = { x: bisector.x / bisLen, y: bisector.y / bisLen };
    const centerX = ix + bisUnit.x * offset;
    const centerY = iy + bisUnit.y * offset;
    const startAngle = Math.atan2(startY - centerY, startX - centerX);
    const endAngle = Math.atan2(endY - centerY, endX - centerX);
    let angleDelta = endAngle - startAngle;
    while (angleDelta <= -Math.PI)
      angleDelta += 2 * Math.PI;
    while (angleDelta > Math.PI)
      angleDelta -= 2 * Math.PI;
    const lastAfterPop = this.points[this.points.length - 1];
    const almostEqual = (a, b) => Math.abs(a - b) < 0.000000001;
    if (!lastAfterPop || !almostEqual(lastAfterPop.x, startX) || !almostEqual(lastAfterPop.y, startY)) {
      this.points.push({ x: startX, y: startY });
    }
    const segments = 8;
    for (let i = 1;i <= segments; i++) {
      const t = i / segments;
      const angle2 = startAngle + angleDelta * t;
      const x = centerX + r * Math.cos(angle2);
      const y = centerY + r * Math.sin(angle2);
      this.points.push({ x, y });
    }
    const last = this.points[this.points.length - 1];
    this.currentX = last.x;
    this.currentY = last.y;
    this.lastDirection = outgoingDir;
    return this;
  }
  arcTo(x, y, { radius, sweep = true, segments = 16 }) {
    const start = { x: this.currentX, y: this.currentY };
    const end = { x, y };
    const mx = (start.x + end.x) / 2;
    const my = (start.y + end.y) / 2;
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist === 0)
      return this;
    const h = Math.sqrt(Math.max(0, radius * radius - __pow(dist / 2, 2)));
    const perpX = -dy / dist;
    const perpY = dx / dist;
    const cx = mx + (sweep ? 1 : -1) * perpX * h;
    const cy = my + (sweep ? 1 : -1) * perpY * h;
    const startAngle = Math.atan2(start.y - cy, start.x - cx);
    const endAngle = Math.atan2(end.y - cy, end.x - cx);
    let sweepAngle = endAngle - startAngle;
    if (sweep && sweepAngle < 0)
      sweepAngle += 2 * Math.PI;
    if (!sweep && sweepAngle > 0)
      sweepAngle -= 2 * Math.PI;
    for (let i = 1;i <= segments; i++) {
      const t = i / segments;
      const angle = startAngle + sweepAngle * t;
      const px = cx + radius * Math.cos(angle);
      const py = cy + radius * Math.sin(angle);
      this.points.push({ x: px, y: py });
    }
    this.currentX = end.x;
    this.currentY = end.y;
    return this;
  }
  toArray() {
    return [...this.points];
  }
};
var outlineBuilder = (x, y) => {
  return new OutlineBuilder(x, y);
};
var processorOutline = outlineBuilder(-9, 11).lineTo(11, 11).corner({ radius: 1, turn: "ccw" }).lineTo(11, -7).corner({ radius: 0.5, turn: "ccw" }).lineTo(10, -7).corner({ radius: 0.5, turn: "cw" }).lineTo(10, -11).lineTo(3.28, -11).lineTo(3.28, -8).arcTo(2.08, -8, { radius: 0.6, sweep: true }).lineTo(2.08, -11).lineTo(-10, -11).lineTo(-10, -7).corner({ radius: 0.5, turn: "cw" }).lineTo(-11, -7).corner({ radius: 0.5, turn: "ccw" }).lineTo(-11, 11).corner({ radius: 1, turn: "ccw" }).toArray();
var functionOutline = outlineBuilder(0, 32.5).lineTo(19, 32.5).corner({ radius: 1, turn: "ccw" }).lineTo(19, -28.5).corner({ radius: 0.5, turn: "ccw" }).lineTo(10, -28.5).corner({ radius: 0.5, turn: "cw" }).lineTo(10, -32.5).lineTo(3.28, -32.5).lineTo(3.28, -29.5).arcTo(2.08, -29.5, { radius: 0.6, sweep: true }).lineTo(2.08, -32.5).lineTo(-10, -32.5).lineTo(-10, -28.5).corner({ radius: 0.5, turn: "cw" }).lineTo(-19, -28.5).corner({ radius: 0.5, turn: "ccw" }).lineTo(-19, 32.5).corner({ radius: 1, turn: "ccw" }).toArray();
var pacmanPolygonOutline = new OutlineBuilder(-0.2, -0.2).lineTo(-0.2, 2.5).arcTo(-2.5, 0, { radius: 2.5, sweep: true }).arcTo(0, -2.5, { radius: 2.5, sweep: true }).arcTo(2.5, -0.2, { radius: 2.5, sweep: true }).lineTo(-0.2, -0.2).toArray();
var horizontalEdgeViaGridCells = grid({
  rows: 2,
  cols: 17,
  xSpacing: 5,
  ySpacing: 45,
  offsetX: 50,
  offsetY: 32.5,
  yDirection: "up-is-negative"
});
var verticalEdgeViaGridCells = grid({
  rows: 8,
  cols: 2,
  xSpacing: 80,
  ySpacing: 5,
  offsetX: 50,
  offsetY: 32.5,
  yDirection: "up-is-negative"
});
var pinLabels = {
  pin1: ["IOVDD6"],
  pin2: ["GPIO0"],
  pin3: ["GPIO1"],
  pin4: ["GPIO2"],
  pin5: ["GPIO3"],
  pin6: ["GPIO4"],
  pin7: ["GPIO5"],
  pin8: ["GPIO6"],
  pin9: ["GPIO7"],
  pin10: ["IOVDD5"],
  pin11: ["GPIO8"],
  pin12: ["GPIO9"],
  pin13: ["GPIO10"],
  pin14: ["GPIO11"],
  pin15: ["GPIO12"],
  pin16: ["GPIO13"],
  pin17: ["GPIO14"],
  pin18: ["GPIO15"],
  pin19: ["TESTEN"],
  pin20: ["XIN"],
  pin21: ["XOUT"],
  pin22: ["IOVDD4"],
  pin23: ["DVDD2"],
  pin24: ["SWCLK"],
  pin25: ["SWD"],
  pin26: ["RUN"],
  pin27: ["GPIO16"],
  pin28: ["GPIO17"],
  pin29: ["GPIO18"],
  pin30: ["GPIO19"],
  pin31: ["GPIO20"],
  pin32: ["GPIO21"],
  pin33: ["IOVDD3"],
  pin34: ["GPIO22"],
  pin35: ["GPIO23"],
  pin36: ["GPIO24"],
  pin37: ["GPIO25"],
  pin38: ["GPIO26_ADC0"],
  pin39: ["GPIO27_ADC1"],
  pin40: ["GPIO28_ADC2"],
  pin41: ["GPIO29_ADC3"],
  pin42: ["IOVDD2"],
  pin43: ["ADC_AVDD"],
  pin44: ["VREG_IN"],
  pin45: ["VREG_VOUT"],
  pin46: ["USB_DM"],
  pin47: ["USB_DP"],
  pin48: ["USB_VDD"],
  pin49: ["IOVDD1"],
  pin50: ["DVDD1"],
  pin51: ["QSPI_SD3"],
  pin52: ["QSPI_SCLK"],
  pin53: ["QSPI_SD0"],
  pin54: ["QSPI_SD2"],
  pin55: ["QSPI_SD1"],
  pin56: ["QSPI_SS"],
  pin57: ["GND", "thermalpad"]
};
var RP2040 = (props) => {
  return /* @__PURE__ */ jsx12("chip", __spreadValues({
    pinLabels,
    supplierPartNumbers: {
      jlcpcb: ["C2040"]
    },
    manufacturerPartNumber: "RP2040",
    footprint: JlcRP2040({name: props.name}).props.footprint,
    cadModel: {
      objUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C2040.obj?uuid=76b360a9d4c54384a4e47d7e5af156df",
      stepUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C2040.step?uuid=76b360a9d4c54384a4e47d7e5af156df",
      pcbRotationOffset: 0,
      modelOriginPosition: { x: 0, y: 0, z: -0.02 }
    }
  }, props));
};
var pinLabels3 = {
  pin1: ["CS"],
  pin2: ["pin2"],
  pin3: ["pin3"],
  pin4: ["GND"],
  pin5: ["pin5"],
  pin6: ["CLK"],
  pin7: ["pin7"],
  pin8: ["VCC"],
  pin9: ["EP"]
};
var W25Q16JVUXIQ = (props) => {
  return /* @__PURE__ */ jsx14("chip", __spreadValues({
    pinLabels: pinLabels3,
    supplierPartNumbers: {
      jlcpcb: ["C2843335"]
    },
    manufacturerPartNumber: "W25Q16JVUXIQ",
    footprint: JlcFlash({name: props.name}).props.footprint,
    cadModel: {
      objUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C2843335.obj?uuid=2b35e1c3dcc44b77887d4f445b51370a",
      stepUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C2843335.step?uuid=2b35e1c3dcc44b77887d4f445b51370a",
      pcbRotationOffset: 0,
      modelOriginPosition: { x: 0, y: 0, z: 0 }
    }
  }, props));
};
var pinLabels4 = {
  pin1: ["VIN"],
  pin2: ["GND"],
  pin3: ["EN"],
  pin4: ["NC"],
  pin5: ["VOUT"]
};
var AP2112K_3_3TRG1 = (props) => {
  return /* @__PURE__ */ jsx15("chip", __spreadValues({
    pinLabels: pinLabels4,
    supplierPartNumbers: {
      jlcpcb: ["C23380830"]
    },
    manufacturerPartNumber: "AP2112K_3_3TRG1",
    footprint: JlcRegulator({name: props.name}).props.footprint,
    cadModel: {
      objUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C23380830.obj?uuid=8c971aea3af54c53b74baeb1f489d393",
      stepUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C23380830.step?uuid=8c971aea3af54c53b74baeb1f489d393",
      // Native model has three leads on -Y; the footprint has them on +X.
      pcbRotationOffset: 90,
      modelOriginPosition: { x: 0, y: 0, z: -0.7 }
    }
  }, props));
};
// Use the imported EasyEDA symbol while retaining the routed board's footprint.
var X322512MSB4SI = (props) => jsx16(ABM8_272_T3, {
  ...props,
  footprint: "crystal",
  internallyConnectedPins: [["pin2", "pin4"]],
  showPinAliases: false,
});
var pinLabels5 = {
  pin1: ["pin1"],
  pin2: ["pin2"],
  pin3: ["pin3"],
  pin4: ["pin4"]
};
var SKRPACE010 = (props) => {
  return /* @__PURE__ */ jsx17("pushbutton", __spreadValues({
    pinLabels: pinLabels5,
    supplierPartNumbers: {
      jlcpcb: ["C139797"]
    },
    manufacturerPartNumber: "SKRPACE010",
    footprint: "smdpushbutton",
    internallyConnectedPins: [
      ["pin1", "pin2"],
      ["pin3", "pin4"]
    ],
    cadModel: {
      objUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C139797.obj?uuid=00d848a7e8384bbd9286566957e8bb9c",
      stepUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C139797.step?uuid=00d848a7e8384bbd9286566957e8bb9c",
      pcbRotationOffset: 0,
      modelOriginPosition: { x: 0, y: 0, z: -0.01 }
    }
  }, props));
};
var pinLabels6 = {
  pin1: ["cathode", "neg"],
  pin2: ["anode", "pos"]
};
var B5819W_SL = (props) => {
  const _a = props, { name = "D1" } = _a, restProps = __objRest(_a, ["name"]);
  return /* @__PURE__ */ jsx18("diode", __spreadValues({
    name,
    pinLabels: pinLabels6,
    variant: "schottky",
    supplierPartNumbers: {
      jlcpcb: ["C8598"]
    },
    manufacturerPartNumber: "B5819W_SL",
    footprint: "sod123w_p3.4mm_pw0.95mm",
    cadModel: {
      objUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C8598.obj?uuid=e9d505c99b6c436aaf827a29c5ba4f84",
      stepUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C8598.step?uuid=e9d505c99b6c436aaf827a29c5ba4f84",
      pcbRotationOffset: 0,
      modelOriginPosition: { x: 0, y: 0.000012699999999199463, z: -0.6 }
    }
  }, restProps));
};
var XL_1608SURC_06 = (props) => {
  const _a = props, { name = "LED1" } = _a, restProps = __objRest(_a, ["name"]);
  return /* @__PURE__ */ jsx19("led", __spreadValues({
    name,
    supplierPartNumbers: {
      jlcpcb: ["C965799"]
    },
    manufacturerPartNumber: "XL_1608SURC_06",
    pinLabels: { pin1: ["cathode", "neg"], pin2: ["anode", "pos"] },
    footprint: "led_p1.498mm_pw0.8mm_ph0.8mm",
    cadModel: {
      objUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C965799.obj?uuid=d0740cb8891c49a88b6949cb978926f3",
      stepUrl: "https://modelcdn.tscircuit.com/easyeda_models/assets/C965799.step?uuid=d0740cb8891c49a88b6949cb978926f3",
      pcbRotationOffset: 0,
      modelOriginPosition: {
        x: -0.000012700000070253736,
        y: 0.00005079999993995443,
        z: -0.01
      }
    }
  }, restProps));
};
var denseTraceProps = { thickness: "0.1mm" };
var gndLabel = { displayName: "GND", schDisplayLabel: "GND" };
var vbusLabel = { displayName: "VBUS", schDisplayLabel: "VBUS" };
var vsysLabel = { displayName: "VSYS", schDisplayLabel: "VSYS" };
var v3v3Label = { displayName: "V3V3", schDisplayLabel: "V3V3" };
var v1v1Label = { displayName: "V1V1", schDisplayLabel: "V1V1" };
var adcRefLabel = {
  displayName: "ADC_REF",
  schDisplayLabel: "ADC_REF"
};
var schSections = {
  rp2040: (name) => `${name}__rp2040`,
  usb: (name) => `${name}__usb`,
  power: (name) => `${name}__power`,
  flash: (name) => `${name}__flash`,
  clock: (name) => `${name}__clock`,
  controls: (name) => `${name}__controls`,
  display: (name) => `${name}__display`,
  status: (name) => `${name}__status`,
  debug: (name) => `${name}__debug`
};
var Microcontroller_RP2040 = (_a) => {
  var _b = _a, {
    name = "Microcontroller_RP2040",
    connections
  } = _b, props = __objRest(_b, [
    "name",
    "connections"
  ]);
  var programmingSchSheetName = props.schSheetName === "controller" ? "controller_programming" : undefined;
  var resistor0402Footprint = () => /* @__PURE__ */ jsxs11("footprint", { children: [
    /* @__PURE__ */ jsx20("smtpad", {
      portHints: ["pin1"],
      pcbX: "-0.432816mm",
      pcbY: "0mm",
      width: "0.565658mm",
      height: "0.540004mm",
      shape: "rect"
    }),
    /* @__PURE__ */ jsx20("smtpad", {
      portHints: ["pin2"],
      pcbX: "0.432816mm",
      pcbY: "0mm",
      width: "0.565658mm",
      height: "0.540004mm",
      shape: "rect"
    })
  ] });
  var capacitor0402Footprint = () => /* @__PURE__ */ jsxs11("footprint", { children: [
    /* @__PURE__ */ jsx20("smtpad", {
      portHints: ["pin1"],
      pcbX: "-0.420116mm",
      pcbY: "0mm",
      width: "0.499999mm",
      height: "0.540004mm",
      shape: "rect"
    }),
    /* @__PURE__ */ jsx20("smtpad", {
      portHints: ["pin2"],
      pcbX: "0.420116mm",
      pcbY: "0mm",
      width: "0.499999mm",
      height: "0.540004mm",
      shape: "rect"
    })
  ] });
  return /* @__PURE__ */ jsxs11("group", __spreadProps(__spreadValues({ name }, props), { children: [
    /* @__PURE__ */ jsx20("schematicsection", {
      name: schSections.rp2040(name),
      displayName: "RP2040 & Power"
    }),
    programmingSchSheetName ? null : /* @__PURE__ */ jsx20("schematicsection", {
      name: schSections.usb(name),
      displayName: "Programming USB-C & QSPI"
    }),
    /* @__PURE__ */ jsx20("schematicsection", { name: schSections.clock(name), displayName: "Clock" }),
    /* @__PURE__ */ jsx20(X322512MSB4SI, {
      name: "Y1",
      schSectionName: schSections.clock(name),
      pcbX: -1.2,
      pcbY: -6,
      pcbRotation: 270,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_XIN",
      capacitance: "15pF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1548"] },
      manufacturerPartNumber: "0402CG150J500NT",
      schSectionName: schSections.clock(name),
      schOrientation: "vertical",
      pcbX: -2,
      pcbY: -9.8,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_XOUT",
      capacitance: "15pF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1548"] },
      manufacturerPartNumber: "0402CG150J500NT",
      schSectionName: schSections.clock(name),
      schOrientation: "vertical",
      pcbX: 0,
      pcbY: -9.8,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_XOUT",
      resistance: "1k",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C11702"] },
      schSectionName: schSections.clock(name),
      pcbX: 1.8,
      pcbY: -5.8,
    }),
    /* @__PURE__ */ jsx20("schematicsection", {
      name: schSections.status(name),
      displayName: "Controls, Status & SWD"
    }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "Y1_G1", from: ".Y1 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "Y1_G2", from: ".Y1 > .pin4", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", { name: "USB_DN_JOIN", schDisplayLabel: "USB_D-", from: ".J_USB > .A7", to: ".J_USB > .B7" }),
    /* @__PURE__ */ jsx20("trace", { name: "USB_DN_CONN", schDisplayLabel: "USB_D-", from: ".J_USB > .B7", to: ".R_USB1 > .pin1" }),
    /* @__PURE__ */ jsx20("trace", { name: "USB_DP_JOIN", schDisplayLabel: "USB_D+", from: ".J_USB > .A6", to: ".J_USB > .B6" }),
    /* @__PURE__ */ jsx20("trace", { name: "USB_DP_CONN", schDisplayLabel: "USB_D+", from: ".J_USB > .B6", to: ".R_USB2 > .pin1" }),
    /* @__PURE__ */ jsx20(B5819W_SL, {
      name: "D_VBUS",
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_supply",
      pcbX: -3.375,
      pcbY: 16.75,
      pcbRotation: 180,
      schRotation: 270
    }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "VBUS_D", from: "net.VBUS", to: ".D_VBUS > .anode" }, vbusLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "D_VSYS",
      from: ".D_VBUS > .cathode",
      to: "net.VSYS"
    }, vsysLabel)),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_3V3_EN",
      resistance: "100k",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25741"] },
      manufacturerPartNumber: "0402WGF1003TCE",
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_supply",
      pcbX: -5.375,
      pcbY: 13.75,
      pcbRotation: 90,
      schRotation: 270
    }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "EN_VSYS",
      from: ".R_3V3_EN > .pin1",
      to: "net.VSYS"
    }, vsysLabel)),
    /* @__PURE__ */ jsx20("trace", { name: "EN_R", from: ".R_3V3_EN > .pin2", to: ".U3 > .EN" }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_IOVDD1",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: -4.4,
      pcbY: -5,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_IOVDD2",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: -3,
      pcbY: 6,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_IOVDD3",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbRotation: 0,
      pcbX: -8.125,
      pcbY: -1.25,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_IOVDD4",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: -4.4,
      pcbY: -6,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_IOVDD5",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbRotation: -90,
      pcbX: -6.875,
      pcbY: -5,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_IOVDD6",
      pcbRotation: 90,
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: -5.375,
      pcbY: 3.75,
    }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "IO5_3V3",
      from: ".C_IOVDD5 > .pin1",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "IO5_G", from: ".C_IOVDD5 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "IO6_3V3",
      from: ".C_IOVDD6 > .pin1",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "IO6_G", from: ".C_IOVDD6 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "IO3_3V3",
      from: ".C_IOVDD3 > .pin1",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "IO3_G", from: ".C_IOVDD3 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "IO4_3V3",
      from: ".C_IOVDD4 > .pin1",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "IO4_G", from: ".C_IOVDD4 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_RUN",
      schRotation: 90.0,
      resistance: "10k",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25744"] },
      manufacturerPartNumber: "0402WGF1002TCE",
      schSectionName: schSections.controls(name),
      pcbX: 6.125,
      pcbY: -6.25,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_FLASH",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      maxDecouplingTraceLength: 1.3,
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_bypass",
      schOrientation: "vertical",
      pcbX: -0.4,
      pcbY: 7.9,
      pcbRotation: -90,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_USB_VDD",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      maxDecouplingTraceLength: 1.5,
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_bypass",
      schOrientation: "vertical",
      pcbX: 0.4,
      pcbY: 5.7,
      pcbRotation: 90,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_ADC",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      manufacturerPartNumber: "CL05B104KO5NNNC",
      schSectionName: schSections.power(name),
      schOrientation: "vertical",
      pcbX: 8,
      pcbY: -4.4,
    }),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "RUN_R",
      from: ".R_RUN > .pin1",
      to: ".U1 > .RUN"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "RUN_3V3", from: ".R_RUN > .pin2", to: "net.V3V3" }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "TEST_G", from: ".U1 > .TESTEN", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "FLSH_3V3",
      from: ".C_FLASH > .pin1",
      to: ".U2 > .VCC"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "FLSH_G", from: ".C_FLASH > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "IO1_3V3",
      from: ".C_IOVDD1 > .pin1",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "IO1_G", from: ".C_IOVDD1 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "IO2_3V3",
      from: ".C_IOVDD2 > .pin1",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "IO2_G", from: ".C_IOVDD2 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "UVDD_3V3",
      from: ".C_USB_VDD > .pin1",
      to: ".U1 > .USB_VDD"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "UVDD_G", from: ".C_USB_VDD > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "ADC_REF",
      from: ".C_ADC > .pin1",
      to: "net.ADC_VREF"
    }, adcRefLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "ADC_G", from: ".C_ADC > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20(ControllerUsbC, {
      name: "J_USB",
      // Keep shell labels above/below the built-in USB graphic and data-pair labels separate.
      schPinArrangement: {topSide:{pins:[18],direction:"left-to-right"},rightSide:{pins:[27,20,26,22,24,23,21,25,19,28],direction:"top-to-bottom"},bottomSide:{pins:[17],direction:"left-to-right"},leftSide:{pins:[13,15,16,14],direction:"top-to-bottom"}},
      schWidth: 3, schHeight: 3.95,
      schPinStyle: {...Object.fromEntries([20,26,22,24,23,21,25,19,28].map(pin=>[`pin${pin}`,{marginTop:0.2}])),pin15:{marginTop:0.1},pin16:{marginTop:2.6},pin14:{marginTop:0.1}},
      noConnect: ["B8", "A8"],
      schSheetName: programmingSchSheetName,
      schSectionName: schSections.usb(name),
      pcbX: 3.125,
      pcbY: 22.45,
      pcbRotation: 180,

    }),
    /* @__PURE__ */ jsx20(RP2040, {
      name: "U1",
      noConnect: ["GPIO24"],
      schWidth: 2.8,
      pinAttributes: {
        IOVDD1: { requiresPower: true },
        GND: { requiresGround: true }
      },
      connections,
      showPinAliases: true,
      schSectionName: schSections.rp2040(name),
      pcbX: 0,
      pcbY: 0.5,
      schPinArrangement: {
        leftSide: {
          pins: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
          direction: "top-to-bottom"
        },
        rightSide: {
          pins: [57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30],
          direction: "top-to-bottom"
        }
      },
      schPinStyle: {
        pin2: { marginTop: 1.05 },
        pin20: { marginTop: 0.4 },
        pin22: { marginTop: 0.4 },
        pin27: { marginTop: 0.4 },
        pin56: { marginTop: 0.3 },
        pin50: { marginTop: 0.4 },
        pin48: { marginTop: 0.35 },
        pin45: { marginTop: 0.35 },
        pin43: { marginTop: 0.35 },
        pin41: { marginTop: 0.35 },
        pin37: { marginTop: 0.35 }
      }
    }),
    /* @__PURE__ */ jsx20(W25Q16JVUXIQ, {
      name: "U2",
      pinAttributes: {
        VCC: { requiresPower: true },
        GND: { requiresGround: true }
      },
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_flash",
      pcbX: -3,
      pcbY: 8.25,
      pcbRotation: -90,
      schPinArrangement: {
        leftSide: {
          pins: [1, 6, 5, 2, 3, 7],
          direction: "top-to-bottom"
        },
        topSide: {
          pins: [8],
          direction: "left-to-right"
        },
        bottomSide: {
          pins: [4, 9],
          direction: "left-to-right"
        }
      },
      schPinStyle: {
        pin1: { marginBottom: 0.18 },
        pin6: { marginTop: 0.25, marginBottom: 0.18 },
        pin5: { marginTop: 0.25, marginBottom: 0.18 },
        pin2: { marginBottom: 0.18 },
        pin3: { marginBottom: 0.18 },
        pin9: { marginLeft: 0.6 }
      }
    }),
    /* @__PURE__ */ jsx20(AP2112K_3_3TRG1, {
      name: "U3",
      schHeight: 1.4,
      pinAttributes: {
        VIN: { requiresPower: true },
        GND: { requiresGround: true }
      },
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_supply",
      pcbX: -7.875,
      pcbY: 14.25,
      pcbRotation: 180,
      schPinArrangement: {
        leftSide: {
          pins: [1, 3],
          direction: "top-to-bottom"
        },
        rightSide: {
          pins: [5, 4],
          direction: "top-to-bottom"
        },
        bottomSide: {
          pins: [2],
          direction: "left-to-right"
        }
      },
      schPinStyle: {
        pin3: { marginTop: 0.8 },
        pin4: { marginTop: 0.8 },
        pin2: { marginLeft: 0 }
      }
    }),

    /* @__PURE__ */ jsx20(SKRPACE010, {
      name: "SW_BOOT",
      pcbRotation: 0,
      schSectionName: schSections.controls(name),
      pcbX: 7.375,
      pcbY: 16.5,
    }),
    /* @__PURE__ */ jsx20(SKRPACE010, {
      name: "SW_RUN",
      schSectionName: schSections.controls(name),
      pcbX: 4.125,
      pcbY: -8.75,
      pcbRotation: 0,
    }),
    /* @__PURE__ */ jsx20(XL_1608SURC_06, {
      name: "D_PWR",
      schRotation: -90.0,
      color: "green",
      schSectionName: schSections.status(name),
      pcbX: -8.875,
      pcbY: 17.25,
      pcbRotation: 0,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_BOOT",
      schRotation: 90.0,
      resistance: "10k",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25744"] },
      manufacturerPartNumber: "0402WGF1002TCE",
      schSectionName: schSections.controls(name),
      pcbX: -2.875,
      pcbY: 19.75,
      pcbRotation: 90,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_PWR_LED",
      schRotation: -90.0,
      resistance: "330",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25104"] },
      manufacturerPartNumber: "0402WGF3300TCE",
      schSectionName: schSections.status(name),
      pcbX: -10.375,
      pcbY: 18.75,
      pcbRotation: 90,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_CC1",
      schRotation: -90.0,
      resistance: "5.1k",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25905"] },
      manufacturerPartNumber: "0402WGF5101TCE",
      schSheetName: programmingSchSheetName,
      schSectionName: schSections.usb(name),
      pcbX: 0.625,
      pcbY: 16.75,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_CC2",
      schRotation: -90.0,
      resistance: "5.1k",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25905"] },
      manufacturerPartNumber: "0402WGF5101TCE",
      schSheetName: programmingSchSheetName,
      schSectionName: schSections.usb(name),
      pcbX: 0.625,
      pcbY: 18.05,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_USB1",
      resistance: "27",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25100"] },
      schSheetName: programmingSchSheetName,
      schSectionName: schSections.usb(name),
      pcbX: 4.3,
      pcbY: 5.4,
      pcbRotation: 180,
    }),
    /* @__PURE__ */ jsx20("resistor", {
      name: "R_USB2",
      resistance: "27",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C25100"] },
      schSheetName: programmingSchSheetName,
      schSectionName: schSections.usb(name),
      pcbX: 4.3,
      pcbY: 6.7,
      pcbRotation: 180,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_VBUS",
      capacitance: "10uF",
      footprint: "0603",
      supplierPartNumbers: { jlcpcb: ["C19702"] },
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_supply",
      schOrientation: "vertical",
      pcbX: -8.875,
      pcbY: 11.05,
      pcbRotation: 90,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_3V3",
      pcbRotation: 0,
      capacitance: "10uF",
      footprint: "0603",
      supplierPartNumbers: { jlcpcb: ["C19702"] },
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_bypass",
      schOrientation: "vertical",
      pcbX: -4.875,
      pcbY: 10.75,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_CORE",
      capacitance: "1uF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C52923"] },
      maxDecouplingTraceLength: 1.5,
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: 1.6,
      pcbY: 5.9,
      pcbRotation: 90,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_USB",
      capacitance: "1uF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C52923"] },
      maxDecouplingTraceLength: 1.5,
      schSheetName: programmingSchSheetName,
      schSectionName: "MCU__programming_bypass",
      schOrientation: "vertical",
      pcbX: 2.8,
      pcbY: 5.7,
      pcbRotation: 90,
    }),



    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_DVDD1",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      maxDecouplingTraceLength: 1.5,
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: -0.8,
      pcbY: 5.7,
      pcbRotation: 90,
    }),
    /* @__PURE__ */ jsx20("capacitor", {
      name: "C_DVDD2",
      capacitance: "100nF",
      footprint: "0402",
      supplierPartNumbers: { jlcpcb: ["C1525"] },
      schSectionName: schSections.rp2040(name),
      schOrientation: "vertical",
      pcbX: 2.8,
      pcbY: -4.5,
    }),
    /* @__PURE__ */ jsx20("inductor", {
      name: "L_AVDD",
      schRotation: -90.0,
      inductance: "600ohm@100MHz",
      footprint: /* @__PURE__ */ jsxs11("footprint", { children: [
        /* @__PURE__ */ jsx20("smtpad", {
          portHints: ["pin1"],
          pcbX: "-0.699897mm",
          pcbY: "0mm",
          width: "0.7999984mm",
          height: "0.8640064mm",
          shape: "rect"
        }),
        /* @__PURE__ */ jsx20("smtpad", {
          portHints: ["pin2"],
          pcbX: "0.699897mm",
          pcbY: "0mm",
          width: "0.7999984mm",
          height: "0.8640064mm",
          shape: "rect"
        })
      ] }),
      schSectionName: schSections.power(name),
      pcbX: 1.375,
      pcbY: 7.5,
      supplierPartNumbers: { jlcpcb: ["C19330"] },
      manufacturerPartNumber: "BLM18AG601SN1D",
      pcbRotation: 0,
    }),
    /* @__PURE__ */ jsx20("testpoint", {
      name: "TP_SWCLK",
      footprintVariant: "pad",
      padShape: "circle",
      padDiameter: "1.1mm",
      schSectionName: schSections.debug(name),
      pcbX: 1.625,
      pcbY: -14.25,
    }),
    /* @__PURE__ */ jsx20("testpoint", {
      name: "TP_GND",
      footprintVariant: "pad",
      padShape: "circle",
      padDiameter: "1.1mm",
      schSectionName: schSections.debug(name),
      pcbX: -0.875,
      pcbY: -14.25,
    }),
    /* @__PURE__ */ jsx20("testpoint", {
      name: "TP_SWDIO",
      footprintVariant: "pad",
      padShape: "circle",
      padDiameter: "1.1mm",
      schSectionName: schSections.debug(name),
      pcbX: 4.125,
      pcbY: -13.25,
    }),
    /* @__PURE__ */ jsx20("testpoint", {
      name: "TP_3V3",
      footprintVariant: "pad",
      padShape: "circle",
      padDiameter: "1.1mm",
      schSectionName: schSections.debug(name),
      pcbX: 5.125,
      pcbY: -11.75,
    }),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "QSPI_SS",
      from: ".U1 > .QSPI_SS",
      to: ".U2 > .CS",
      schDisplayLabel: "QSPI_SS"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "QSPI_SD0",
      from: ".U1 > .QSPI_SD0",
      to: ".U2 > .pin5",
      schDisplayLabel: "QSPI_SD0"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "QSPI_SD1",
      from: ".U1 > .QSPI_SD1",
      to: ".U2 > .pin2",
      schDisplayLabel: "QSPI_SD1"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "QSPI_SD2",
      from: ".U1 > .QSPI_SD2",
      to: ".U2 > .pin3",
      schDisplayLabel: "QSPI_SD2"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "QSPI_SD3",
      from: ".U1 > .QSPI_SD3",
      to: ".U2 > .pin7",
      schDisplayLabel: "QSPI_SD3"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "QSPI_SCLK",
      from: ".U1 > .QSPI_SCLK",
      to: ".U2 > .CLK",
      schDisplayLabel: "QSPI_SCLK"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "IOVDD1_P",
      from: ".U1 > .IOVDD1",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "IOVDD2_P",
      from: ".U1 > .IOVDD2",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "IOVDD3_P",
      from: ".U1 > .IOVDD3",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "IOVDD4_P",
      from: ".U1 > .IOVDD4",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "IOVDD5_P",
      from: ".U1 > .IOVDD5",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "IOVDD6_P",
      from: ".U1 > .IOVDD6",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), { name: "DVDD1_CAP", from: ".C_DVDD1 > .pin1", to: ".U1 > .DVDD1" })),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), { name: "DVDD1_P", from: ".U1 > .DVDD1", to: "net.V1V1" }), v1v1Label)),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), { name: "VREG_CORE", from: ".U1 > .VREG_VOUT", to: ".C_CORE > .pin1" })),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), { name: "VREG_VOUT_P", from: ".U1 > .VREG_VOUT", to: "net.V1V1" }), v1v1Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), { name: "DVDD2_P", from: ".U1 > .DVDD2", to: "net.V1V1" }), v1v1Label)),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), { name: "DVDD2_CAP", from: ".U1 > .DVDD2", to: ".C_DVDD2 > .pin1" })),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "VREG_IN_P",
      from: ".U1 > .VREG_IN",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_VDD_P",
      from: ".U1 > .USB_VDD",
      to: "net.V3V3"
    }), v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "GND_G", from: ".U1 > .GND", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USBV_IO1",
      from: ".U1 > .USB_VDD",
      to: ".U1 > .IOVDD1"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "VBUS_A", from: ".J_USB > .A4B9", to: "net.VBUS" }, vbusLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "VBUS_B", from: ".J_USB > .B4A9", to: "net.VBUS" }, vbusLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_DN",
      from: ".R_USB1 > .pin2",
      to: ".U1 > .USB_DM"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_DP",
      from: ".R_USB2 > .pin2",
      to: ".U1 > .USB_DP"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "CC1",
      from: ".J_USB > .A5",
      to: ".R_CC1 > .pin1"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadProps(__spreadValues({}, denseTraceProps), {
      name: "CC2",
      from: ".J_USB > .B5",
      to: ".R_CC2 > .pin1"
    })),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_G",
      from: ".J_USB > .A1B12",
      to: "net.GND"
    }), gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_G_B",
      from: ".J_USB > .B1A12",
      to: "net.GND"
    }), gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_EH1",
      from: ".J_USB > .EH1",
      to: "net.GND"
    }), gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_EH1_ALT",
      from: ".J_USB > .pin13_alt1",
      to: "net.GND"
    }), gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_EH2",
      from: ".J_USB > .EH2",
      to: "net.GND"
    }), gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues(__spreadProps(__spreadValues({}, denseTraceProps), {
      name: "USB_EH2_ALT",
      from: ".J_USB > .pin14_alt1",
      to: "net.GND"
    }), gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CC1_G", from: ".R_CC1 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CC2_G", from: ".R_CC2 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "VBUS_C", from: "net.VBUS", to: ".C_VBUS > .pin1" }, vbusLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "VBUS_G", from: ".C_VBUS > .pin2", to: ".U3 > .GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "VSYS_IN", from: "net.VSYS", to: ".U3 > .VIN" }, vsysLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "REG_3V3", from: ".U3 > .VOUT", to: "net.V3V3" }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "REG_G", from: ".U3 > .GND", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "C3V3_P", from: ".C_3V3 > .pin1", to: "net.V3V3" }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "C3V3_G", from: ".C_3V3 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CORE_G", from: ".C_CORE > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CUSB_P", from: ".C_USB > .pin1", to: ".U1 > .VREG_IN" }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CUSB_G", from: ".C_USB > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "AVDD_IN", from: ".L_AVDD > .pin1", to: "net.V3V3" }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "AVDD",
      from: ".L_AVDD > .pin2",
      to: "net.ADC_VREF"
    }, adcRefLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "ADC_AVDD",
      from: ".U1 > .ADC_AVDD",
      to: "net.ADC_VREF"
    }, adcRefLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "FLSH_GND", from: ".U2 > .GND", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "FLSH_VCC", from: ".U2 > .VCC", to: "net.V3V3" }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", { name: "FLSH_EP_GND_JOIN", from: ".U2 > .EP", to: ".U2 > .GND" }),
    /* @__PURE__ */ jsx20("trace", { name: "XIN", from: ".Y1 > .pin1", to: ".U1 > .XIN", maxViaCount: 0, pcbPathRelativeTo: ".Y1 > .pin1", pcbPath: [{ x: -1.95, y: -0.85 }, { x: -1.95, y: 0.6 }] }),
    /* @__PURE__ */ jsx20("trace", { name: "XOUT_R", from: ".Y1 > .pin3", to: ".R_XOUT > .pin1", maxViaCount: 0, pcbStraightLine: true }),
    /* @__PURE__ */ jsx20("trace", { name: "XOUT", from: ".R_XOUT > .pin2", to: ".U1 > .XOUT", maxViaCount: 0, pcbPathRelativeTo: ".R_XOUT > .pin2", pcbPath: [{"x": -0.14, "y": 0.65}, {"x": -0.54, "y": 0.65}, {"x": -0.59, "y": 0.7}, {"x": -0.69, "y": 0.7}, {"x": -0.84, "y": 0.85}, {"x": -0.84, "y": 0.9}, {"x": -0.89, "y": 0.95}, {"x": -0.89, "y": 1.25}, {"x": -1.64, "y": 2.0}, {"x": -1.64, "y": 2.1}, {"x": -1.89, "y": 2.35}, {"x": -1.89, "y": 2.75}] }),
    /* @__PURE__ */ jsx20("trace", { name: "CXIN", from: ".C_XIN > .pin1", to: ".Y1 > .pin1", maxViaCount: 0, pcbPathRelativeTo: ".C_XIN > .pin1", pcbPath: [{ x: -1, y: 0 }, { x: -1, y: 4.4 }] }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CXIN_G", from: ".C_XIN > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", { name: "CXOUT", from: ".C_XOUT > .pin1", to: ".Y1 > .pin3", maxViaCount: 0, pcbStraightLine: true }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "CXOUT_G", from: ".C_XOUT > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "DVDD1_CAP_G", from: ".C_DVDD1 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "DVDD2_CAP_G", from: ".C_DVDD2 > .pin2", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", { name: "BOOT_SW", from: ".SW_BOOT > .pin1", to: ".U1 > .QSPI_SS" }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "BOOT_G", from: ".SW_BOOT > .pin3", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", { name: "BOOT_R", from: ".R_BOOT > .pin1", to: ".U1 > .QSPI_SS" }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "BOOT_3V3",
      from: ".R_BOOT > .pin2",
      to: "net.V3V3"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", { name: "RUN_SW", from: ".SW_RUN > .pin1", to: ".U1 > .RUN" }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "RUN_G", from: ".SW_RUN > .pin4", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({
      name: "PLED_3V3",
      from: "net.V3V3",
      to: ".R_PWR_LED > .pin1"
    }, v3v3Label)),
    /* @__PURE__ */ jsx20("trace", { name: "PLED_D", from: ".R_PWR_LED > .pin2", to: ".D_PWR > .anode" }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "PLED_G", from: ".D_PWR > .cathode", to: ".U3 > .GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", { name: "SWCLK", from: ".U1 > .SWCLK", to: ".TP_SWCLK > .pin1" }),
    /* @__PURE__ */ jsx20("trace", { name: "SWD", from: ".U1 > .SWD", to: ".TP_SWDIO > .pin1" }),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "TP_G", from: ".TP_GND > .pin1", to: "net.GND" }, gndLabel)),
    /* @__PURE__ */ jsx20("trace", __spreadValues({ name: "TP3V3_T", from: ".TP_3V3 > .pin1", to: "net.V3V3" }, v3v3Label)),
    /* @__PURE__ */ jsx20("silkscreentext", { text: "BOOT", fontSize: "0.8mm", pcbX: 12, pcbY: 14 }),
    /* @__PURE__ */ jsx20("silkscreentext", { text: "RUN", fontSize: "0.8mm", pcbX: 2, pcbY: -10.5 }),
    /* @__PURE__ */ jsx20("silkscreentext", { text: "PWR", fontSize: "0.8mm", pcbX: -5.5, pcbY: 15 }),
    /* @__PURE__ */ jsx20("silkscreentext", { text: "USB-C", fontSize: "0.9mm", pcbX: 0, pcbY: 25 })
  ] }));
};
export {
  Microcontroller_RP2040
};
