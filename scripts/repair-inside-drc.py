"""Remove the concrete obsolete/attempted traces reported by native DRC.
No checker filtering; every affected net must be rerouted and all checks rerun.
"""
import json,hashlib
import verify_supplier_connectivity as g
j=g.j;errors=json.loads((g.ROOT/'artifacts/drc-report.json').read_text())['errors'];traces={e['pcb_trace_id']:e for e in j if e['type']=='pcb_trace'};removed={};protected=('inside_phase_escape_','inside_power_escape_','inside_ref_escape','inside_signal_escape_','inside_mcu_escape_','inside_sense_escape_','inside_logic_escape_')
for e in errors:
 if e['type']not in ['pcb_trace_error','pcb_via_trace_clearance_error']:continue
 tid=e.get('pcb_trace_id')
 if tid and tid.startswith(protected):
  candidates=[t for t in traces if t!=tid and not t.startswith(protected)and t in e.get('pcb_trace_error_id',e.get('pcb_via_trace_clearance_error_id',''))];assert len(candidates)==1,(e,candidates);tid=candidates[0]
 assert tid in traces,('Missing actionable trace',e)
 removed[tid]={'net':g.nets.get(g.key(traces[tid])),'error':e}
assert removed,'No actionable trace repairs in current report'
keys={g.key(traces[k])for k in removed};out=[e for e in j if not(e['type']=='pcb_trace'and e['pcb_trace_id']in removed or e['type']=='pcb_via'and e.get('pcb_trace_id')in removed or e['type']=='pcb_copper_pour'and g.nets.get(g.key(e))=='GND')];g.path.write_text(json.dumps(out,indent=2)+'\n');report={'source_before_sha256':hashlib.sha256(json.dumps(j).encode()).hexdigest(),'removed_concrete_error_traces':removed,'affected_nets_requiring_repair':sorted(g.nets[k]for k in keys),'status':'REROUTE_REBUILD_CONNECTIVITY_AND_CAM_REQUIRED'};(g.ROOT/'artifacts/validation/service-actionable-drc-repair.json').write_text(json.dumps(report,indent=2)+'\n');print(','.join(report['affected_nets_requiring_repair']))
