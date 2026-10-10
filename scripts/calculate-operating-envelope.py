from pathlib import Path
import json,math,hashlib
for root in [Path(__file__).resolve().parents[1]]:
 name='CH32X035' if json.loads((root/'package.json').read_text())['name']=='NEMA14_CH32X035G8U6' else 'RP2040'; load=.550
 rl=10000*470/(10000+470);scale=1+100000/rl;vmax=35*(rl*1.01)/(100000*.99+rl*1.01)
 cmin=100e-6*.8*.7;lmax=.024*1.2;imax=.25;winding=.5*lmax*2*imax**2;mechanical=.0001;energy=winding+mechanical
 j=json.loads((root/'artifacts/board.circuit.json').read_text());parts={e['name']:e for e in j if e['type']=='source_component'}
 assert parts['R_REF_H']['resistance']==6200 and parts['R_VM_BLEED']['resistance']==470 and parts['R_SA']['resistance']==.24 and parts['R_SB']['resistance']==.24
 report={'source_sha256':hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'revision':'diagnostics-2026-10-10','status':'proposed prototype qualification envelope; not a qualified product rating','hardwareTestsPerformed':False,'manufacturingRelease':False,'motor':'14HM11-0404S','normalPdBusV':[14.25,15.75],'busOperatingCeilingV':18,'phaseCurrentNominalA':3.3/(1+6200/1000)/(8*.24),'maximumAcceptedMeasuredPhasePeakA':imax,'motorManufacturerPhaseLimitA':.4,'ambientRoomC':[0,40],'maximumLocalPcbAmbientC':45,'maximumMotorCaseC':60,'logicOutputMaximumLoadA':load,'logicOutputMaximumAverageLoadA':.310,'baselineLogicAllowanceA':.100,'dataOnlyLogicTargetA':.075,'dataOnlyUsbAcceptanceA':.100,'dataOnlyEfficiencyScreenAssumed':.70,'dataOnlyInputCurrentScreenA':.075*3.6/(.70*(4.75-.60)),'buzzerWorstResistivePulseA':3.6/9,'buzzerMaximumBurstS':.100,'buzzerMaximumBurstRateHz':1,'buzzerNominalPwmHz':4000,'buzzerPwmDuty':.5,'buzzerRequiresValid15VPd':True,'regulator':'AP63203WU-7','minimumAcceptedLogicRailV':3.,'maximumAcceptedLogicRailV':3.6,'maximumMechanicalEnergyPerStopJ':mechanical,'maximumStopRateHz':1,'busMinimumBulkCapacitanceF':cmin,'bulkMinimumMethod':'100uF x initial tolerance0.8 x endurance capacitance change0.7. This is an endurance-test screening corner, not a lifetime or high-frequency guarantee.','windingInductanceMaximumH':lmax,'windingEnergyJ':winding,'totalStopEnergyJ':energy,'energyBudgetTo18VJ':.5*cmin*(18**2-15.75**2),'idealBusPeakV':math.sqrt(15.75**2+2*energy/cmin),'excludedFromIdealBusPeak':['ESR/ESL','cable inductance','capacitor bias and temperature/aging beyond cited endurance','switching overshoot','continued backdrive','PD-source absorption'],'adcScaleNominal':scale,'adcWorstPassive35VBoundV':vmax,'adcLeakageAllowanceA':1e-6,'adcLeakageVoltageAllowanceV':470*1.01*1e-6,'adcOffLimitV':.3,'adcTimeConstantNominalS':1/(1/100000+1/10000+1/470)*10e-9,'prototypeGates':['phase-current accuracy and mismatch over supply/temperature/microstep','mounted temperatures and thermal soak','USB enumeration/programming and DATA current','15V PD negotiation and loss','startup/reset/brownout/source handover and ADC fast collapse','regeneration bus peak and repetition','buck biased/aged capacitance and loop/load response','harness fit/pull/abrasion and connector insertion','supplier fabrication and pickup acceptance']}
 if 'U_LDO' in parts:
  report['holtek']={'operatingInputMaximumV':30,'absoluteInputMaximumV':33,'absoluteJunctionMaximumC':150,'designJunctionTargetMaximumC':125,'thetaJaScreenCPerW':200,'maximumLogicLoadAssumptionA':load,'iqMaximumA':4e-6,'lossAt15_75VAnd3_0VOutW':(15.75-3)*load+15.75*4e-6,'junctionScreenAtLocal45C':45+200*((15.75-3)*load+15.75*4e-6),'junctionScreenAt18V':45+200*((18-3)*load+18*4e-6),'screenIsMeasurement':False,'regulationGuaranteeOverMountedTemperature':'not established; verify3.0..3.6V over all states, otherwise reject/change regulator'}
 assert parts['U_BUCK']['manufacturer_part_number']=='AP63203WU-7'
 out=root/'artifacts/engineering';out.mkdir(exist_ok=True);p=out/'supported-operating-envelope.json';p.write_text(json.dumps(report,indent=2)+'\n')
 text=f'''# Proposed operating envelope — {name}

This is a general-purpose **prototype qualification envelope**, chosen without assuming a host machine. It is the intended supported envelope after the acceptance tests below pass. Neither design has been built or qualified; these limits are requirements, not measured ratings. CAM success does not approve continuous operation, fabrication or production release. An application must establish its inertia, speed, stored spring/gravity energy and stopping behavior before operation.

| Parameter | Conservative limit | Evidence / qualification |
|---|---|---|
| Motor | STEPperONLINE 14HM11-0404S only; keyed black/green/red/blue harness | Exact motor drawing: 0.40 A/phase, 25 Ω ±10%, 24 mH ±20%. Other NEMA14 motors need separate review. |
| PD motor input | Requested 15 V; normal 14.25–15.75 V | Reject unexpected PD voltage. Confirm negotiation and safe power loss on a prototype. |
| Motor bus during stopping | **≤18 V**, including all switching/ESR/cable peaks | Oscilloscope acceptance requirement; TVS breakdown is higher and cannot enforce this operating limit. |
| Winding current | 6.2 kΩ / 1 kΩ reference, unchanged 0.24 Ω shunts: **{report['phaseCurrentNominalA']:.6f} A nominal**. Accepted actual peak in each phase ≤0.25 A; never exceed manufacturer0.40 A. | Divider/shunt tolerances and reference leakage can raise the formula. A4988 accuracy is specified at VREF2V, not this≈0.458V reference; current must be measured. If actual peak exceeds0.25A, adjust the reference resistor and repeat qualification. Copper arithmetic is not used to compensate shunts. |
| Logic supply load | ≤{int(load*1000)} mA pulse /310mA average on3V3; 100mA PD baseline allowance; DATA-only 3V3 target≤75mA; **no external loads** | Qualification ceilings, not measured consumption. Buzzer only with valid15V PD,4kHz/50%, bursts≤100ms,≤1/s; DATA-only buzzer disabled. Measure USB input≤100mA before enumeration, then within the descriptor/advertised budget. |
| Logic voltage | 3.0–3.6 V in every powered state | Acceptance window, not a guaranteed tolerance attributed to either regulator. Check start/stop and loaded ripple. |
| USB data input | USB2 host5V only;≤100mA drawn from DATA before and after enumeration | No higher host budget assumed. No motor power from DATA. Verify enumeration and ROM/application programming. |
| Temperature | Room0–40°C, noncondensing; local air at regulators/PCB≤45°C; motor case≤60°C | Mounted motor heating may violate local45°C even in a cool room. Thermal-soak test determines duty/cooling. No continuous-duty or torque/speed guarantee yet. |
| Junction design target | ≤125°C | A design target. AP63203 design-section ceiling125°C; each other manufacturer limit remains separate. |
| Returned mechanical energy | **≤0.10mJ per stop**, including rotor/load kinetic energy, gravity and elastic energy; stops≤1Hz | Energy budget below. Sustained or externally forced back-driving is outside this envelope. |
| Back-driving / brake | No continuous regenerative operation; no uncontrolled falling/overhauling load | No brake resistor/controller is fitted and no PD sink capability is assumed. Higher returned energy requires a separately qualified braking/clamping subsystem and revised protection review. |
| Environment | Indoor bench/light machine, protected from conductive debris, liquids and cable impact | Harness barrier/clamp/access and supplier fabrication remain qualification gates. |

## Added diagnostics and power margin

DATA-only3V3 target≤75mA screens≈92.9mA input at3.6V output,4.75V host minus0.60V diode and an assumed70% conversion efficiency. Efficiency/dropout are unproved; the measured DATA-port100mA ceiling applies to every steady state and power transition, including loss of PD while sounding. Firmware must disable the alarm before DATA fallback; if handover measurements exceed the host budget, revise hardware gating/power before release.

Both designs now use AP63203WU-7. CH32's former HT7533-1 was removed: a 0.4 A coil pulse at15.75V would dissipate about4.98W in a3.3V LDO, beyond the retained low-load design. Holtek's official30V operating/33V absolute ratings are historical evidence, not current limits for the buck.

MLT-5020 primary datasheet specifies12Ω±3Ω. A deliberately conservative resistive screen is3.6V/9Ω=0.4A pulse, plus100mA baseline and<6mA LED/pull-ups: below550mA. At50% PWM, average screen≈306mA; this does not replace coil-waveform measurements. The published100mA sounder limit is specified at3.0V/4kHz/50%; acoustic behavior and actual consumption at the accepted rail window remain unqualified. AO3400A's48mΩ maximum at2.5V gives≤7.68mW pulse conduction screen at0.4A.

Bourns4.7µH−20%=3.76µH and AP63203's typical1.1MHz/−6% FSS give a nominal-corner ripple screen≈0.741A at18V/3.6V and peak≈0.921A at550mA load, below published2.0A Isat/1.9A Irms at25°C. Frequency/FSS and hot saturation are not guaranteed corners; startup/fault current limit can exceed Isat. Scope current and qualify temperature, output-bank bias/aging, stability and source handover. All three22µF output capacitors and10µF/50V input are retained, plus22µF local buzzer bypass.

TMP102 reports local PCB temperature. Its reading is not a measured winding, case or A4988 junction temperature; do not treat the MCU alert as an independent hardware cutoff. Correlate sensor, driver, motor and carrier readings before defining a thermal trip. See[diagnostics.md](diagnostics.md) for pins and firmware behavior.

## Regeneration calculation and application check

Use **all** returned energy, not only the attached load: `Emechanical = ½ Jtotal ω² + returned gravitational energy + returned elastic energy`, with total reflected inertia including the rotor. Gear efficiency is conservatively100% when estimating energy returned to the board. Do not count winding dissipation, friction, firmware reaction or PD source absorption as a guaranteed sink.

At0.25A maximum actual phase current and28.8mH maximum documented winding inductance, assume both windings simultaneously contain `½ L (IA² + IB²) = {winding*1000:.3f}mJ`. Adding the0.10mJ mechanical allocation gives **{energy*1000:.3f}mJ per stop**. Panasonic's initial−20% capacitance and endurance-change−30% corner gives **56µF**, rather than relying only on the80µF initial corner. This is an endurance-test screen; it is not a lifetime warranty or a verified effective-capacitance floor at every temperature/frequency.

From15.75V,56µF stores **{report['energyBudgetTo18VJ']*1000:.4f}mJ** before18V. The ideal capacitor-only peak is **{report['idealBusPeakV']:.3f}V**. The remaining voltage margin must absorb ESR/ESL, switching and cable overshoot; the calculation does **not** certify that margin. Scope the actual bus with the PD source connected and disconnected, hottest mounted board, smallest qualified capacitor, worst microstep/decay and simultaneous stop. Reject any operating point exceeding18V. Maximum1Hz repetition is a proposed acceptance ceiling; confirm recovery, capacitor ripple/temperature and protection heating. TVS pulse ratings do not establish repetitive braking capacity.

For illustration, at60rpm, the0.10mJ kinetic-energy allocation permits at most `Jtotal = 2E/ω² ≈5.07×10⁻⁶kg·m²`, including the rotor. That is an energy example, **not** a qualified60rpm speed or guaranteed torque rating. A slower system can still violate the budget through gravity, springs or externally driven motion.

## ADC and power-transition requirements

The revised passive monitor is100kΩ feeding10kΩ∥470Ω toGND, with10nF toGND at the ADC. Nominal scale is **{scale:.5f}**;15V is≈{15/scale*1000:.2f}mV at the ADC. With1% resistor corners,35V gives≤**{vmax:.6f}V**, plus≈0.475mV for a1µA input-leakage screen. This remains below the powered-off+0.3V pin limit without an enable signal, firmware, rail clamp or unqualified switch behavior. Stored capacitor voltage is bounded by the same low divider voltage through instantaneous logic collapse. Nominal RC≈{report['adcTimeConstantNominalS']*1e6:.2f}µs. The35V calculation is pin-protection screening, **not authorization for35V bus operation**. Verify negative ringing and high-frequency coupling physically.

Firmware must configure the pin as a high-impedance analog input with no pull-up/output drive, apply the new scale, use sufficient acquisition time, and calibrate against a DMM. At a3.3V12-bit ADC, bus resolution is≈0.180V/count; use averaging and hysteresis, and do not claim precision overvoltage protection. On reset, keep STEP low, ENABLE_N high and SLEEP low. Arm the motor only after valid PD-good status, a measured14.25–15.75V bus and stable logic; disable on loss of these conditions. Firmware is not the regenerative clamp. Qualified brownout/reset behavior, PG transitions and power-source handover are still required.

## Prototype acceptance and limits that remain unproved

- Measure both phase peaks and balance across normal supply, microsteps and temperature. Acceptance≤0.25A per phase; no motor0.40A exceedance. Record actual sense-return bounce with a differential/Kelvin measurement.
- Measure total 3V3 pulse load against the{int(load*1000)}mA ceiling and average load against310mA. Verify3.0–3.6V regulation, ripple, startup, ROM boot and USB activity at room0/40°C and motor-heated local45°C. Both variants use AP63203; oscillator frequency/FSS typical values do not establish a guaranteed ripple-current corner.
- Perform slow and fast power ramps, abrupt PD/data removal, all cable insertion orders, brownout/reset and source handover. Record ADC/3V3/PG/ENABLE/SLEEP and bus peaks. No unexpected motor drive or powered-off pin-limit violation is accepted.
- Test stopping energy/repetition at the envelope corners, including source disconnection. Verify≤18V peak and no continuous TVS conduction; use qualified external braking for more energetic hosts.
- Validate buck capacitance at operating bias/temperature/age, stability, startup, load steps and inductor peak/heating. Typical supplier curves are screening data, not a guaranteed worst-case capacitor specification.
- Establish continuous-duty time/cooling only after steady-state mounted temperature testing. Check driver/regulator junction estimates against125°C design target and motor/harness/cable material limits.
- Test simultaneous exact USB plug insertion/removal, JST mating and insertion coupon, harness crimp/splice pull strength, strain relief, vibration, abrasion and insulation. Resolve material certificates and supplier fill/cap/slot/stencil/pickup acceptance.

Calculations are executable in`artifacts/engineering/supported-operating-envelope.json`. No hardware measurement or supplier approval has been performed. The installation remains the enlarged front-thread carrier documented in`mechanical-fit.md`; the35×35mm PCB is not the host-machine envelope.
'''
 if 'U_LDO' in parts:
  h=report['holtek'];text+='\n## Holtek screening within this proposed envelope\n\nHT75xx-1Rev2.81 specifies30V maximum operating input,33V absolute input and150°C absolute junction maximum.125°C is our design target. At20mA total load,3.0V conservative output and15.75V input, loss≤%.6fW using4µA maximumIq. With the cited200°C/W screening value and local45°C, estimated junction≈%.2f°C; an18V bus gives≈%.2f°C. This is a calculation, not measured thermal performance or a full-temperature output-voltage guarantee. Measure actual load/rail/temperature before accepting the LDO; a failure of the20mA, voltage or temperature gates requires a regulator redesign, rather than operating beyond the envelope.\n'%(h['lossAt15_75VAnd3_0VOutW'],h['junctionScreenAtLocal45C'],h['junctionScreenAt18V'])
 import re
 text=re.sub(r'(?<=[a-z])(?=\d)', ' ', text)
 text=re.sub(r'(?<=\d)(?=(?:mJ|mV|V|A|mA|Hz|rpm|µF|µs|°C|kΩ|nF)\b)', ' ', text)
 text=text.replace('in`','in `').replace('in3V3','in 3V3').replace('on3V3','on 3V3').replace('this≈','this ≈').replace('is100','is 100').replace('toGND','to GND')
 (root/'docs/supported-operating-envelope.md').write_text(text)
 print(root.name,'documented candidate envelope')
