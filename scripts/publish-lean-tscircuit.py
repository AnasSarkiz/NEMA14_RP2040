"""Publish only native viewer data and essential manufacturing downloads.

Full sources, datasheets, models, logs and qualification receipts stay in GitHub.
Pruning affects only the exact current version after GitHub preservation.
"""
import argparse, base64, gzip, hashlib, json, pathlib, re, tempfile
import urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = 'https://registry-api.tscircuit.com/'
REPO = 'AnasSarkiz/NEMA14_RP2040'
sha = lambda data: hashlib.sha256(data).hexdigest()
encode = lambda value: (json.dumps(value,separators=(',',':'))+'\n').encode()

def strip_models(records):
    return [{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ['model_obj_url','model_step_url'])} for e in records]

def stage_package():
    meta=json.loads((ROOT/'package.json').read_text())
    proof_path=ROOT/'artifacts/github-source-publication.json'
    github=json.loads(proof_path.read_text()) if proof_path.exists() else {}
    revision=github.get('github_commit','main')
    model=json.loads((ROOT/'artifacts/ch224a-migration/public-model-assets.json').read_text())
    assert model['passed']
    model_revision=model['github_revision']
    raw=(ROOT/'artifacts/board.circuit.json').read_bytes(); board=json.loads(raw)
    assembly=json.loads((ROOT/'assembly.circuit.json').read_text())
    assert assembly[:len(board)]==board
    pattern=re.compile(r'(https://raw\.githubusercontent\.com/AnasSarkiz/(?:NEMA17_Controller|NEMA14_RP2040)/)main(/imports/supplier/)')
    def pin(records):
        out=json.loads(json.dumps(records))
        for e in out:
            if e['type']!='cad_component':continue
            for key in ['model_obj_url','model_step_url']:
                if not e.get(key):continue
                url=pattern.sub(lambda m:'https://raw.githubusercontent.com/'+REPO+'/'+model_revision+m[2],e[key])
                e[key]=url.replace(str(ROOT)+'/imports/supplier/','https://raw.githubusercontent.com/'+REPO+'/'+model_revision+'/imports/supplier/')
        assert strip_models(out)==strip_models(records)
        return out
    pcb,assembled=pin(board),pin(assembly)
    files={'index.circuit.json':encode(pcb),'assembly.circuit.json':encode(assembled),
           'dist/index/circuit.json':encode(pcb),'dist/assembly/circuit.json':encode(assembled)}
    downloads={'Gerbers.zip':'artifacts/jlcpcb-review/JLCPCB-Gerbers.zip',
               'BOM.csv':'artifacts/jlcpcb-review/JLCPCB-BOM.csv',
               'CPL.csv':'artifacts/jlcpcb-review/JLCPCB-CPL.csv',
               'schematic.pdf':'artifacts/schematic-a4.pdf',
               'bottom-silkscreen.png':'artifacts/bottom-markings/bottom-silkscreen.png'}
    files.update({name:(ROOT/path).read_bytes() for name,path in downloads.items()})
    files['package.json']=encode({'name':meta['name'],'version':meta['version'],'description':meta['description'],
                                 'main':'index.circuit.json','repository':'https://github.com/'+REPO})
    files['tscircuit.config.json']=encode({'mainEntrypoint':'index.circuit.json',
        'includeBoardFiles':['index.circuit.json','assembly.circuit.json'],'previewComponentPath':'assembly.circuit.json'})
    files['README.md']=(f'# NEMA14 RP2040 — {meta["version"]}\n\n'
        'Native PCB and motor assembly previews, fabrication Gerbers, JLCPCB BOM/CPL, schematic and bottom silkscreen preview.\n\n'
        f'Full source, datasheets, models and engineering reports: https://github.com/{REPO}/tree/{revision}\n\n'
        f'Order review: https://github.com/{REPO}/blob/{revision}/docs/final-order-review-2026-10-17.md\n').encode()
    silk=json.loads((ROOT/'artifacts/bottom-markings/verification.json').read_text())
    files['verification.json']=encode({'board_sha256':sha(raw),'published_board_sha256':sha(files['index.circuit.json']),
        'only_CAD_model_URL_metadata_changed':True,'routing_preserved':True,
        'github_repository':REPO,'github_source_revision':revision,'github_model_revision':model_revision,
        'bottom_silkscreen_verified':silk['passed'],'silkscreen_warning':silk['warning'],
        'mask_clearance_mm':silk['mask_clearance_mm'],'drill_clearance_mm':silk['drill_clearance_mm'],
        'production_release_approved':False,
        'manufacturing_download_sha256':{name:sha(files[name]) for name in downloads}})
    assert len(files)==13 and not any(n.startswith(('references/','src/','scripts/','imports/','docs/')) for n in files)
    stage=pathlib.Path(tempfile.mkdtemp(prefix='nema14-lean-package.'))
    for name,data in files.items():
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return meta,github,files,stage

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage-only',action='store_true')
    parser.add_argument('--prune',action='store_true')
    parser.add_argument('--bounded-upload',action='store_true',help='Compatibility flag; uploads are always bounded.')
    args=parser.parse_args();meta,github,files,stage=stage_package()
    print('Lean package:',stage,'files:',len(files),'bytes:',sum(map(len,files.values())),flush=True)
    if args.stage_only:return
    assert github.get('verified_all_tracked_files'), 'Verify the full project in GitHub before publishing/pruning'
    assert github['board_sha256']==sha((ROOT/'artifacts/board.circuit.json').read_bytes())
    name='AnasSarkiz/'+meta['name'];version=name+'@'+meta['version']
    token=json.loads(pathlib.Path('/workspace/.config/tscircuit-nodejs/config.json').read_text())['sessionToken']
    def post(endpoint,body):
        req=urllib.request.Request(API+endpoint,data=encode(body),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            print('Registry error',endpoint,error.code,error.read(600).decode(errors='replace'),flush=True);raise
    try:release=post('package_releases/get',{'package_name_with_version':version})['package_release']
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        release=post('package_releases/create',{'package_name_with_version':version})['package_release']
    rid=release['package_release_id']
    def rows():
        query=urllib.parse.urlencode({'package_name':name,'use_latest_version':'true'})
        with urllib.request.urlopen(API+'package_files/list?'+query,timeout=30) as response:result=json.load(response)['package_files']
        assert all(e['package_release_id']==rid for e in result),'Latest version changed; stop without touching other releases'
        return result
    current=rows()
    if args.prune:
        extras=[e for e in current if e['file_path'] not in files]
        extras.sort(key=lambda e:(ROOT/e['file_path']).stat().st_size if (ROOT/e['file_path']).is_file() else (e.get('file_size_kb') or 0)*1024)
        for e in extras:
            post('package_files/delete',{'package_release_id':rid,'file_path':e['file_path']})
            print('Removed registry-only extra:',e['file_path'],flush=True)
        current=rows()
    else:assert {e['file_path'] for e in current}<=set(files),'Use --prune for this exact version to remove nonessential files'
    present={e['file_path'] for e in current}
    for path,data in files.items():
        if path in present:
            query=urllib.parse.urlencode({'package_name':name,'use_latest_version':'true','file_path':path})
            with urllib.request.urlopen(API+'package_files/get?'+query,timeout=60) as response:remote=json.load(response)['package_file']
            assert remote['package_release_id']==rid
            if remote.get('is_text'):
                content=remote['content_text'].encode()
                if path.endswith('.circuit.json') or path.startswith('dist/'):
                    assert json.loads(content)==json.loads(data),'Existing native preview differs; stop before changing it'
                    continue
                if content==data:continue
            else:
                query=urllib.parse.urlencode({'package_file_id':remote['package_file_id']})
                with urllib.request.urlopen(API+'package_files/download?'+query,timeout=60) as response:content=response.read()
                if content==data:continue
        entry={'file_path':path}
        if pathlib.Path(path).suffix in {'.zip','.png','.pdf'}:entry['content_base64']=base64.b64encode(data).decode()
        else:entry['content_text']=data.decode()
        encoded=base64.b64encode(gzip.compress(encode({'files':[entry]}),compresslevel=9)).decode()
        assert len(encoded)<3_000_000
        post('package_files/upload_archive',{'package_release_id':rid,'archive_base64':encoded})
        print('Uploaded:',path,flush=True)
    assert {e['file_path'] for e in rows()}==set(files)
    post('package_releases/update',{'package_release_id':rid,'ready_to_build':True,'is_latest':True,'license':'ISC'})
    result={'version':meta['version'],'release_id':rid,'expected_files':sorted(files),
            'github_source_revision':github['github_commit'],'stage':str(stage),'uploaded':True}
    (ROOT/'artifacts/lean-publication-attempt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
