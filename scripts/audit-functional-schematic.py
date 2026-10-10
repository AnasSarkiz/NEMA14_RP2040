from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
r=Path(sys.argv[1])if len(sys.argv)>1 else Path(__file__).resolve().parents[1];findings=[];pages=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1600,'height':1200})
 for svg in sorted((r/'artifacts').glob('schematic-a4-page-*.svg')):
  page.set_content(svg.read_text());data=page.evaluate('''()=>{const svg=document.querySelector('svg'); const ts=[...svg.querySelectorAll('text')].filter(t=>t.textContent.trim()).map(t=>{const z=t.getBoundingClientRect();return {text:t.textContent.trim(),x:z.x,y:z.y,w:z.width,h:z.height}});const hits=[];for(let i=0;i<ts.length;i++)for(let j=i+1;j<ts.length;j++){const a=ts[i],b=ts[j],w=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x),h=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);if(w>.35&&h>.35)hits.push({a:a.text,b:b.text,w,h})}return {hits,textCount:ts.length}}''')
  findings.extend(dict(page=svg.name,**x)for x in data['hits']);pages.append({'file':svg.name,'text_count':data['textCount'],'sha256':hashlib.sha256(svg.read_bytes()).hexdigest()})
 b.close()
report={'schema':'functional-schematic-text-audit-v1','source_sha256':hashlib.sha256((r/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'pages':pages,'text_overlap_findings':findings,'passed':not findings,'method':'Actual Chromium SVG text bounding boxes; intersections exceeding 0.35 CSS pixel on both axes are findings.'};(r/'artifacts/validation/functional-schematic-text-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(r.name,len(findings),'text overlaps');print(json.dumps(findings[:30],indent=2))

raise SystemExit(0 if not findings else 1)
