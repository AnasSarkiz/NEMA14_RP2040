#!/usr/bin/env python3
"""Export native copper/drills and apply qualified stencil, silk and assembly policies.

The upstream CLI export is retained for diagnosis. The default downloadable
archive is the reviewed output, with a frozen Circuit JSON hash and byte-identical
native copper/mask/outline/drills. Supplier approval remains separate.
"""
import hashlib,importlib.util,json,os,pathlib,shutil,subprocess,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
PYTHON='/workspace/.routing-venv/bin/python'

def main():
    board=ROOT/'artifacts/board.circuit.json';frozen=board.read_bytes();stage=ROOT/'artifacts/engineering-fixes';stage.mkdir(exist_ok=True)
    upstream=stage/'upstream-native-gerbers.zip';primary=ROOT/'artifacts/nema14-gerbers.zip'
    env=dict(os.environ);env['PATH']=str(ROOT/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config'
    subprocess.run(['tsci','export',str(board),'-f','gerbers','-o',str(upstream)],cwd=ROOT,env=env,check=True)
    shutil.copy2(upstream,primary)
    subprocess.run([PYTHON,'scripts/prepare-jlcpcb-review.py'],cwd=ROOT,env=env,check=True)
    out=ROOT/'artifacts/jlcpcb-review';cam=out/'cam'
    with zipfile.ZipFile(primary,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(cam.iterdir()):
            if p.suffix in {'.gbr','.drl','.csv'}:z.write(p,p.name)
    manifest=json.loads((out/'manifest.json').read_text())
    assert board.read_bytes()==frozen,'Export must not change the saved board'
    with zipfile.ZipFile(upstream) as a,zipfile.ZipFile(primary) as b:
        for name,digest in manifest['copied_unchanged_copper_mask_drill_outline'].items():
            assert a.read(name)==b.read(name)
            assert hashlib.sha256(b.read(name)).hexdigest()==digest
    manifest['upstream_native_export_sha256']=hashlib.sha256(upstream.read_bytes()).hexdigest()
    manifest['native_export_sha256']=hashlib.sha256(primary.read_bytes()).hexdigest()
    manifest['default_export_contains_qualified_assembly_corrections']=True
    manifest['upstream_tool_output_retained_as_diagnostic_only']=str(upstream.relative_to(ROOT))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for name in ['bom.csv','pick_and_place.csv']:shutil.copy2(cam/name,ROOT/'artifacts'/name)
    subprocess.run(['python3','scripts/finalize-manufacturing-artifacts.py'],cwd=ROOT,env=env,check=True)
    receipt={'board_sha256':hashlib.sha256(frozen).hexdigest(),'default_export_sha256':manifest['native_export_sha256'],'upstream_native_export_sha256':manifest['upstream_native_export_sha256'],'qualified_paste_silkscreen_BOM_CPL_applied':True,'native_copper_mask_outline_drill_bytes_preserved':True,'supplier_approval':False}
    (stage/'export-policy.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Default export applies qualified assembly policy; native copper and drills preserved')

if __name__=='__main__':main()
