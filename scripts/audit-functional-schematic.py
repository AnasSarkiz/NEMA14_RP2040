"""Check rendered text collisions and foreign labels/text inside symbol bodies."""
from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
r=Path(sys.argv[1])if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
findings=[];body_findings=[];pages=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1600,'height':1200})
 for svg in sorted((r/'artifacts').glob('schematic-a4-page-*.svg')):
  page.set_content(svg.read_text());data=page.evaluate('''()=>{
   const svg=document.querySelector('svg'),box=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}},owner=e=>e.closest('[data-schematic-component-id]')?.getAttribute('data-schematic-component-id');
   const ts=[...svg.querySelectorAll('text')].filter(t=>t.textContent.trim()).map(t=>({text:t.textContent.trim(),owner:owner(t),...box(t)}));
   const bodies=[...svg.querySelectorAll('.sch-component-body')].map(e=>({component:owner(e),...box(e)}));
   const overlap=(a,b)=>({w:Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x),h:Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)}),significant=o=>o.w>.35&&o.h>.35;
   const hits=[],bodyHits=[];
   for(let i=0;i<ts.length;i++)for(let j=i+1;j<ts.length;j++){const o=overlap(ts[i],ts[j]);if(significant(o))hits.push({a:ts[i].text,b:ts[j].text,...o})}
   for(const t of ts)for(const body of bodies){if(t.owner===body.component)continue;const o=overlap(t,body);if(significant(o))bodyHits.push({text:t.text,foreign_body:body.component,...o})}
   return{hits,bodyHits,textCount:ts.length,bodyCount:bodies.length}
  }''')
  findings.extend(dict(page=svg.name,**x)for x in data['hits']);body_findings.extend(dict(page=svg.name,**x)for x in data['bodyHits']);pages.append({'file':svg.name,'text_count':data['textCount'],'symbol_bodies_checked':data['bodyCount'],'sha256':hashlib.sha256(svg.read_bytes()).hexdigest()})
 b.close()
report={'schema':'functional-schematic-text-audit-v2','source_sha256':hashlib.sha256((r/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'pages':pages,'text_overlap_findings':findings,'foreign_symbol_body_findings':body_findings,'passed':not(findings or body_findings),'method':'Actual Chromium SVG bounding boxes; intersections exceeding 0.35 CSS pixel on both axes are findings. Text is allowed within its own symbol body, never a foreign symbol body. Net labels have no component owner and are checked against every body.'}
(r/'artifacts/validation/functional-schematic-text-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(r.name,len(findings),'text overlaps;',len(body_findings),'foreign symbol-body overlaps');print(json.dumps((findings+body_findings)[:30],indent=2))
raise SystemExit(0 if report['passed']else 1)
