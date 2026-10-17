"""Capture the native circuit-json-to-gltf assembly in its local WebGL viewer."""
import asyncio, functools, hashlib, json, pathlib, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.async_api import async_playwright

root=pathlib.Path(__file__).resolve().parents[1]
out=root/'artifacts/top-assembly'
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(out)))
threading.Thread(target=server.serve_forever,daemon=True).start()

async def main():
 errors=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
  page=await browser.new_page(viewport={'width':1400,'height':1100})
  page.on('pageerror',lambda error:errors.append(str(error)))
  await page.goto(f'http://127.0.0.1:{server.server_port}/assembly-viewer.html',wait_until='domcontentloaded')
  await page.wait_for_function('window.assemblyReady === true',timeout=60000)
  for view,filename in [('complete','assembly-complete.png'),('connector','assembly-jst-connection.png'),('top','assembly-top.png')]:
   await page.locator(f'[data-view="{view}"]').click()
   await page.mouse.move(1380,1000)
   await page.wait_for_timeout(1200)
   await page.screenshot(path=str(out/filename))
  await browser.close()
 assert not errors,errors
 files=['assembly.circuit.json','artifacts/top-assembly/assembled.glb','artifacts/top-assembly/assembly-complete.png','artifacts/top-assembly/assembly-jst-connection.png','artifacts/top-assembly/assembly-top.png']
 report={'passed':True,'browser_render':'Chromium WebGL using native circuit-json-to-gltf; complete, seated JST and top views captured',
  'browser_errors':errors,'files':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
  'motor_rear_attachment_verified':False,'physical_crimp_and_latch_tested':False}
 (out/'assembly-render-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
try:asyncio.run(main())
finally:server.shutdown()
