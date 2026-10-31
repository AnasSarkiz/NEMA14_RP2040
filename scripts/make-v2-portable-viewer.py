"""Make a single-file, read-only tscircuit preview; never exports manufacturing files."""
import base64, hashlib, json, re
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'artifacts/v2/source.circuit.json'
circuit=json.loads(source.read_text())
assets={}
for element in circuit:
    if element['type']!='cad_component':continue
    obj=element.get('model_obj_url')
    if obj:
        if obj.startswith('https://raw.githubusercontent.com/AnasSarkiz/NEMA14_RP2040/'):
            path=ROOT/('imports/'+unquote(urlparse(obj).path).split('/imports/',1)[1])
        else:
            path=Path(obj)
            if not path.is_absolute():path=ROOT/path
        path=path.resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Missing local CAD: '+str(path))
        asset_key=str(path.relative_to(ROOT))
        assets[asset_key]=base64.b64encode(path.read_bytes()).decode()
        element['model_obj_url']='embedded:'+asset_key
        # Display uses the exact OBJ; STEP exchange files are unnecessary here.
        element.pop('model_step_url',None)

bundle=ROOT/'node_modules/@tscircuit/runframe/dist/standalone-preview.min.js'
version=json.loads((bundle.parent.parent/'package.json').read_text())['version']
sha=hashlib.sha256(source.read_bytes()).hexdigest()
def script_json(value):return json.dumps(value,separators=(',',':')).replace('<','\\u003c')
# Replace only remote font transport expressions in the pinned viewer bundle.
# These expressions are inside a worker-serialized function, so embed literals.
fonts=ROOT/'references/viewer/fonts'
def data_url(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
font_json={
    'codepoint-index/plane0/0-ff.json':data_url(fonts/'latin-index.json','application/json'),
    'font-meta/latin.json':data_url(fonts/'latin-meta.json','application/json'),
}
font_files={f'latin/sans-serif.normal.{w}.woff':data_url(fonts/f'latin-sans-{w}.woff','font/woff') for w in [400,700]}
raw_js=bundle.read_text()
fetch_expression='fetch(Q+"/"+W)'
font_expression='Q+"/font-files/"+q.id+"/"+ge+"."+ye+"."+le+".woff"'
assert raw_js.count(fetch_expression)==1 and raw_js.count(font_expression)==1,'Viewer font transport changed; review packaging'
raw_js=raw_js.replace(fetch_expression,'fetch(('+script_json(font_json)+')[W]||Q+"/"+W)')
raw_js=raw_js.replace(font_expression,'(('+script_json(font_files)+')[q.id+"/"+ge+"."+ye+"."+le+".woff"]||'+font_expression+')')
js=re.sub(r'</script',lambda m:'<\\/script',raw_js,flags=re.I)
manifold=ROOT/'references/viewer/manifold-3.2.1'
loader=re.sub(r'</script',lambda m:'<\\/script',(manifold/'manifold.js').read_text(),flags=re.I)
wasm=base64.b64encode((manifold/'manifold.wasm').read_bytes()).decode()
preload=loader+"\nconst embeddedManifoldWasm="+json.dumps(wasm)+";\nwindow.ManifoldModule=()=>Module({wasmBinary:Uint8Array.from(atob(embeddedManifoldWasm),c=>c.charCodeAt(0))});\n"
html='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEMA14 RP2040 V2 — placement preview</title>
<style>html,body{margin:0;height:100%;font:14px system-ui;background:#f8fafc;color:#172b35}#draft{height:42px;box-sizing:border-box;padding:11px 16px;background:#fff2cb;border-bottom:1px solid #b99c50}#root{height:calc(100% - 42px);width:100%}.loading{padding:32px}</style>
</head><body><div id="draft"><strong>V2 · 34.5 × 34.5 mm</strong> — Placement draft · Unrouted · Not for ordering</div>
<div id="root"><div class="loading">Loading tscircuit viewer…</div></div>
<script>
const embeddedAssets=ASSETS;
const assetUrls=Object.fromEntries(Object.entries(embeddedAssets).map(([key,data])=>[key,URL.createObjectURL(new Blob([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],{type:'text/plain'}))]));
window.CIRCUIT_JSON=CIRCUIT;
for(const item of window.CIRCUIT_JSON){if(item.type==='cad_component'&&item.model_obj_url?.startsWith('embedded:'))item.model_obj_url=assetUrls[item.model_obj_url.slice(9)];}
window.CIRCUIT_JSON_PREVIEW_PROPS={defaultActiveTab:'pcb',showRightHeaderContent:true,readOnly:true,showFileMenu:false,showImportAndFormatButtons:false,allowSelectingVersion:false,availableTabs:['pcb','schematic','cad']};
window.addEventListener('error',e=>{console.error('Viewer error:',e.message)});
</script><script type="module">BUNDLE</script></body></html>'''
html=html.replace('ASSETS;',script_json(assets)+';',1).replace('CIRCUIT;',script_json(circuit)+';',1).replace('BUNDLE</script>',preload+js+'</script>',1)
html=html.replace('<title>',f'<!-- Source SHA256: {sha}; runframe {version}; models embedded, no manufacturing export. -->\n<title>',1)
output=ROOT/'artifacts/v2/NEMA14-V2-viewer.html'
output.write_text(html)
print(json.dumps({'path':str(output),'bytes':output.stat().st_size,'source_sha256':sha,'runframe_version':version,'embedded_obj_models':len(assets)}))
