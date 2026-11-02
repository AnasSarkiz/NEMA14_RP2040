"""Route the saved V2 source, save every audit, and keep release blocked."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--passes',type=int,default=2)
parser.add_argument('--jar',type=Path,default=Path('/workspace/freerouting-2.0.1.jar'))
args=parser.parse_args()
if not 1<=args.passes<=100:parser.error('--passes must be between 1 and 100')
expected='d7fd0f63f52e6d74b0fad6715f87ca9f0ffd7109d66b2a584638000270592ecf'
if hashlib.sha256(args.jar.read_bytes()).hexdigest()!=expected:
    raise ValueError('Freerouting JAR does not match the pinned 2.0.1 release')
out=ROOT/'artifacts/v2/routing';out.mkdir(parents=True,exist_ok=True)
python=sys.executable
env=dict(os.environ)
env['PATH']=str(ROOT/'node_modules/.bin')+os.pathsep+env['PATH']
commands=[]
def run(command,log=None):
    print('Running: '+' '.join(map(str,command)),flush=True)
    if log:
        with log.open('w') as stream:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    else:result=subprocess.run(command,cwd=ROOT,env=env)
    commands.append({'command':list(map(str,command)),'exit_code':result.returncode})
    return result.returncode
for command in [
    [python,'scripts/check-v2.py'],
    [python,'scripts/verify-v2-placement.py'],
    [python,'scripts/freeroute-v2.py','export','--source','artifacts/v2/source.circuit.json'],
]:
    if run(command):raise SystemExit('Source/placement/export check failed before routing')
java=['java','-Djava.awt.headless=true','-Duser.home=/tmp/nema14-v2-java','-Xmx4g','-jar',str(args.jar),
      '-de','artifacts/v2/routing/wago.dsn','-do','artifacts/v2/routing/wago.ses',
      '-mp',str(args.passes),'-mt','2','-oit','50','-da','--gui.enabled=false',
      '--router.start_pass_no=1','--router.stop_pass_no='+str(args.passes)]
if run(java,out/'freerouting.log'):raise SystemExit('Freerouting failed; see its log')
if run([python,'scripts/freeroute-v2.py','import','--source','artifacts/v2/source.circuit.json']):
    raise SystemExit('Freerouting session could not be imported')
candidate='artifacts/v2/routing/freerouted.circuit.json'
render=run(['bun','scripts/render-v2-routing.ts',candidate])
physical=run([python,'scripts/audit-v2-routing.py','--source',candidate,'--output','artifacts/v2/routing/physical-routing-audit.json'])
native=run(['bun','scripts/check-v2-routing.ts',candidate])
physical_report=json.loads((out/'physical-routing-audit.json').read_text())
native_report=json.loads((out/'native-drc.json').read_text())
open_count=len(physical_report['disconnected_nets'])
viewer=run([python,'scripts/make-v2-portable-viewer.py','--source',candidate,
            '--output','artifacts/v2/routing/NEMA14-V2-routing-viewer.html',
            '--native-drc','artifacts/v2/routing/native-drc.json',
            '--notice',f'Routing draft · {open_count} nets open · Engineering checks incomplete · Not for ordering'])
report={'stage':'initial routing candidate','fabrication_ready':False,
        'candidate_sha256':hashlib.sha256((ROOT/candidate).read_bytes()).hexdigest(),
        'placement_source_sha256':physical_report['placement_source_sha256'],
        'routed_trace_sections':physical_report['traces'],'through_vias':physical_report['vias'],
        'physical_net_groups':physical_report['nets_checked'],
        'disconnected_net_groups':len(physical_report['disconnected_nets']),
        'independent_shorts':len(physical_report['shorts']),
        'native_drc_errors':len(native_report['errors']),
        'passes':args.passes,'render_exit_code':render,'viewer_exit_code':viewer,
        'physical_audit_exit_code':physical,'native_drc_exit_code':native,'commands':commands,
        'remaining':['Review/fix every open and clearance issue','USB pair/reference, Kelvin sensing and power-loop review','Ground fill/stitching and CAM/drill qualification']}
(out/'routing-status.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(bool(render or viewer or physical or native))
