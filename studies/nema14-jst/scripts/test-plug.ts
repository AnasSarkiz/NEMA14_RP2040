import { readFileSync } from 'node:fs'
import assert from 'node:assert/strict'
import { getSideEntryPlug } from '../src/side-entry-plug'
const b=JSON.parse(readFileSync('tests/fixtures/known-screw-intrusions.circuit.json','utf8'))
const p=getSideEntryPlug(b)
const near=(a:number,z:number)=>assert.ok(Math.abs(a-z)<1e-6,`${a} != ${z}`)
near(p.housing.max[0]-p.housing.min[0],5)
near(p.housing.max[1]-p.housing.min[1],5)
near(p.housing.max[2]-p.housing.min[2],2.8)
near(p.catalog_mated_height_mm,2.95)
near(p.exposed_housing_length_mm,.9625033)
near(p.withdrawal_sweep.max[0]-p.seated_envelope.max[0],5)
assert.equal(p.actual_cable_handling_verified,false)
const s=b.find((e:any)=>e.type==='source_component'&&e.name==='J_MOTOR').source_component_id
const cad=(q:any[])=>q.find((e:any)=>e.type==='cad_component'&&e.source_component_id===s)
const pcb=(q:any[])=>q.find((e:any)=>e.type==='pcb_component'&&e.source_component_id===s)
const moved=structuredClone(b);cad(moved).position.y+=1;pcb(moved).center.y+=1
near(getSideEntryPlug(moved).housing.min[1]-p.housing.min[1],1)
const above=structuredClone(b);cad(above).rotation.z=0;pcb(above).insertion_direction='from_above'
assert.throws(()=>getSideEntryPlug(above),/right-side mating axis/)
const raised=structuredClone(b);cad(raised).position.z+=1
assert.throws(()=>getSideEntryPlug(raised),/header datum/)
console.log('NEMA14 JST plug dimensions, side-axis transform, withdrawal, translation, wrong-entry and datum guards passed.')
