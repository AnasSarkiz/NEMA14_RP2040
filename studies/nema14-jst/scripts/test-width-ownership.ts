/** Real automatic underwidth is the negative control for the checker correction. */
import {readFileSync} from 'node:fs'
import {checkSourceTracesMatchPcbTraceThickness} from '@tscircuit/checks'
import assert from 'node:assert/strict'
for(const stack of ['current','tagged'])for(const mode of ['authored','automatic']){
 const b=JSON.parse(readFileSync(`artifacts/iteration-4/compatibility/${stack}-${mode}.circuit.json`,'utf8'))
 const st=new Map<string,any>(b.filter((e:any)=>e.type==='source_trace').map((e:any)=>[e.source_trace_id,e]))
 const pt=new Map<string,any>(b.filter((e:any)=>e.type==='pcb_trace').map((e:any)=>[e.pcb_trace_id,e]))
 const input=JSON.parse(readFileSync(`artifacts/iteration-4/compatibility/${stack}-${mode}.routing-input.json`,'utf8')).simpleRouteJson
 if(stack==='tagged'&&mode==='automatic')for(const c of input.connections.filter((c:any)=>c.source_trace_id))assert.deepEqual(c.path,c.pointsToConnect.map((p:any)=>p.pcb_port_id))
 if(stack==='tagged'&&mode==='authored'){assert.equal(input.traces.length,4);for(const t of input.traces){assert.equal(t.connectsTo.length,2);assert.equal(t.isFixed,true);assert.ok(t.source_trace_id)}}
 const warnings=checkSourceTracesMatchPcbTraceThickness(b),bad=stack==='current'&&mode==='automatic'
 assert.equal(warnings.length,bad?2:0,stack+'/'+mode)
 for(const w of warnings){const actual=pt.get(w.pcb_trace_id!);assert.equal(w.source_trace_id,actual.source_trace_id);assert.match(st.get(actual.source_trace_id).name,/^POWER_/)}
 for(const e of pt.values()){const name=st.get(e.source_trace_id)?.name;if(!/^KELVIN_|^POWER_/.test(name))continue;const widths=e.route.filter((r:any)=>r.route_type==='wire').map((r:any)=>r.width);assert.ok(widths.every((w:number)=>Math.abs(w-(name.startsWith('POWER_')&&!bad?.45:.16))<1e-8),name)}
}
console.log('Four physical width/ownership controls passed; two real legacy underwidths remain detected.')
