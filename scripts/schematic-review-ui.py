"""Read-only browser UI for native tscircuit A4 drawings and CLI analysis findings."""
import argparse,json,pathlib,re,xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOTS={'RP2040':pathlib.Path(__file__).resolve().parents[1]}
for name,path in [('CH32','/workspace/NEMA17_Controller'),('RP2040','/workspace/NEMA14_RP2040')]:
 if pathlib.Path(path).exists():ROOTS[name]=pathlib.Path(path)
HTML='''<!doctype html><meta charset="utf-8"><title>NEMA14 schematic analysis</title><style>body{margin:0;font:16px system-ui;background:#eef2f7;color:#172438}header{padding:14px 24px;background:#17354f;color:white}main{display:grid;grid-template-columns:300px 1fr;gap:16px;padding:18px}aside{background:white;padding:16px;border-radius:8px}select,button{font:inherit;padding:8px;margin:4px}#drawing{background:white;border-radius:8px;width:100%;height:80vh;border:0}.pass{color:#167245}.issue{color:#ae4132}li{margin:12px 0}small{color:#516276}</style><header><h2>tscircuit schematic analysis</h2>Native A4 drawings · CLI placement analysis · saved PCB checks</header><main><aside><label>Board <select id="project"><option>CH32</option><option>RP2040</option></select></label><br><label>A4 sheet <select id="sheet"></select></label><h3 id="summary"></h3><p id="drc"></p><small>Results come from tsci check schematic-placement and the saved DRC report. Named nets connect across pages.</small><ul id="findings"></ul></aside><iframe id="drawing" title="Native A4 schematic"></iframe></main><script>let data;async function load(){const project=document.querySelector('#project').value;data=await(await fetch('/analysis?project='+project)).json();document.querySelector('#sheet').innerHTML=data.sheets.map((s,i)=>`<option value="${i+1}">${i+1}: ${s.display_name}</option>`).join('');document.querySelector('#summary').textContent=data.issues.length+' schematic placement findings';document.querySelector('#summary').className=data.issues.length?'issue':'pass';document.querySelector('#drc').textContent=data.errors+' DRC errors, '+data.warnings+' DRC warnings';document.querySelector('#findings').innerHTML=data.issues.map(s=>'<li>'+s.type+': '+s.message+'</li>').join('');draw()}function draw(){document.querySelector('#drawing').src='/drawing?project='+document.querySelector('#project').value+'&sheet='+document.querySelector('#sheet').value}document.querySelector('#project').onchange=load;document.querySelector('#sheet').onchange=draw;load();</script>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  from urllib.parse import urlparse,parse_qs
  url=urlparse(self.path);query=parse_qs(url.query);project=query.get('project',['CH32'])[0]
  if project not in ROOTS:self.send_error(404);return
  root=ROOTS[project]
  if url.path=='/':content=HTML.replace('<option>CH32</option><option>RP2040</option>', ''.join('<option>'+name+'</option>' for name in ROOTS)).encode();mime='text/html'
  elif url.path=='/analysis':
   text=(root/'artifacts/validation/schematic-placement.txt').read_text();elements=ET.fromstring('<analysis>'+text+'</analysis>');issues=[{'type':e.tag,'message':e.get('message',''),'reference':e.get('componentName','')} for group in elements.iter('SchematicPlacementIssues') for e in group]
   board=json.loads((root/'artifacts/board.circuit.json').read_text());drc=json.loads((root/'artifacts/drc-report.json').read_text());content=json.dumps({'sheets':[e for e in board if e['type']=='schematic_sheet'],'issues':issues,'errors':len(drc['errors']),'warnings':len(drc['warnings'])}).encode();mime='application/json'
  elif url.path=='/drawing':
   number=int(query.get('sheet',['1'])[0]);assert 1<=number<=50;content=(root/f'artifacts/schematic-a4-page-{number:02d}.svg').read_bytes();mime='image/svg+xml'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
 def log_message(self,*args):pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=5175);a=p.parse_args();print(f'Schematic analysis UI listening on 127.0.0.1:{a.port}',flush=True);ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
