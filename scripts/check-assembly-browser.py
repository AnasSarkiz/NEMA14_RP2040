"""Open the real exported assembly GLB in Chromium/WebGL; save all review views."""
from pathlib import Path
import functools,hashlib,json,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/assembly-scene'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((OUT/'build-review.json').read_text());assert sha(OUT/'installed-assembly.glb')==report['installed_glb_sha256']
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(OUT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
errors=[];console_errors=[];http_errors=[];screens=[]
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1280,'height':960},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda e:console_errors.append(e.text)if e.type=='error'else None)
  page.on('response',lambda r:http_errors.append({'status':r.status,'url':r.url})if r.status>=400 and not r.url.endswith('favicon.ico')else None)
  page.goto(f'http://127.0.0.1:{server.server_port}/viewer.html')
  page.wait_for_function('window.assemblyReview?.loaded === true',timeout=120000)
  data=page.evaluate('({loaded:assemblyReview.loaded,meshes:assemblyReview.meshes,vertices:assemblyReview.vertices,bounds:assemblyReview.bounds,webgl:assemblyReview.webgl})')
  expected=report['expected_export_glTF_bounds_mm']
  assert all(abs(a-b)<.08 for a,b in zip(data['bounds'],expected)),(data['bounds'],expected)
  assert data['meshes']>8 and data['vertices']>10000
  for view in ['isometric','top','side','underside','controller']:
   page.evaluate('(v)=>assemblyReview.setView(v)',view)
   page.wait_for_timeout(800)
   target=OUT/(view+'.png');page.screenshot(path=str(target),timeout=60000);screens.append({'view':view,'path':str(target.relative_to(ROOT)),'sha256':sha(target)})
  browser.close()
 assert not errors and not console_errors and not http_errors,{'pageerrors':errors,'console_errors':console_errors,'http_errors':http_errors}
 review={'source_board_sha256':report['source_board_sha256'],'assembly_entry_sha256':report['assembly_entry_sha256'],'installed_glb_sha256':sha(OUT/'installed-assembly.glb'),'viewer_js_sha256':sha(OUT/'viewer.js'),'viewer_html_sha256':sha(OUT/'viewer.html'),'renderer':'Chromium WebGL/SwiftShader; actual exported GLB and bundled Three.js viewer','loaded':data,'expected_export_gltf_bounds_mm':expected,'screenshots':screens,'page_errors':errors,'console_errors':console_errors,'http_errors':http_errors,'hardware_fit_verified':False}
 (OUT/'browser-review.json').write_text(json.dumps(review,indent=2)+'\n')
 print('WebGL assembly loaded; dimensions verified; five camera views saved; browser errors 0')
finally:
 server.shutdown();server.server_close()
