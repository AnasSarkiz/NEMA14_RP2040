"""Verify the exact public allowlist, native preview and manufacturing downloads."""
import datetime, hashlib, importlib.util, json, pathlib, urllib.parse, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lean',ROOT/'scripts/publish-lean-tscircuit.py')
lean=importlib.util.module_from_spec(spec);spec.loader.exec_module(lean)

def main():
    meta,github,expected,stage=lean.stage_package()
    name='AnasSarkiz/'+meta['name'];api=lean.API
    request=urllib.request.Request(api+'package_releases/get',data=lean.encode({'package_name_with_version':name+'@'+meta['version']}),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response:release=json.load(response)['package_release']
    rid=release['package_release_id']
    def get(endpoint,**params):
        with urllib.request.urlopen(api+endpoint+'?'+urllib.parse.urlencode(params),timeout=60) as response:return response.read()
    rows=json.loads(get('package_files/list',package_name=name,use_latest_version='true'))['package_files']
    assert all(e['package_release_id']==rid for e in rows)
    assert {e['file_path'] for e in rows}==set(expected),'Public package has missing or nonessential files'
    assert len(rows)==len(expected)==13
    downloaded={};evidence=[]
    for path,data in expected.items():
        row=json.loads(get('package_files/get',package_name=name,use_latest_version='true',file_path=path))['package_file']
        assert row['package_release_id']==rid
        remote=row['content_text'].encode() if row['is_text'] else get('package_files/download',package_file_id=row['package_file_id'])
        if path.endswith('.circuit.json') or path.startswith('dist/'):
            assert json.loads(remote)==json.loads(data),path+' native records differ'
        else:assert remote==data,path+' bytes differ'
        downloaded[path]=remote
        evidence.append({'path':path,'sha256':hashlib.sha256(remote).hexdigest()})
    native=json.loads((ROOT/'artifacts/board.circuit.json').read_text())
    pcb=json.loads(downloaded['index.circuit.json']);assembly=json.loads(downloaded['assembly.circuit.json'])
    assert lean.strip_models(pcb)==lean.strip_models(native)
    assert assembly[:len(pcb)]==pcb
    preview=json.loads(get('package_releases/get_preview_circuit_json',package_name=name,is_latest='true'))['preview_circuit_json_response']
    assert preview['circuit_json_found'] and preview['component_path']=='assembly.circuit.json'
    assert preview['circuit_json']==assembly
    assert all('/'+json.loads(downloaded['verification.json'])['github_model_revision']+'/imports/supplier/' in e[k]
               for e in pcb if e['type']=='cad_component' for k in ['model_obj_url','model_step_url'] if e.get(k))
    proof={'passed':True,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'version':meta['version'],'release_id':rid,'public_file_count':len(rows),
           'no_datasheets_supplier_models_sources_or_historical_reports_in_registry':True,
           'full_project_preserved_in_GitHub':github['verified_all_tracked_files'],
           'github_source_revision':github['github_commit'],'board_sha256':lean.sha((ROOT/'artifacts/board.circuit.json').read_bytes()),
           'saved_routing_and_schematic_records_preserved':True,'actual_default_preview':'assembly.circuit.json',
           'public_preview_matches_native_assembly':True,'bottom_logo_and_warning_preserved':True,
           'manufacturing_downloads_match_qualified_files':True,'files':evidence}
    (ROOT/'artifacts/lean-publication-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
