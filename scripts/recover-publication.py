"""Complete a CLI archive upload using bounded native registry archives; never replace existing rows."""
import base64,gzip,json,pathlib,sys,urllib.parse,urllib.request
stage=pathlib.Path(sys.argv[1]);meta=json.loads((stage/'package.json').read_text());name='AnasSarkiz/'+meta['name'];version=meta['version'];api='https://registry-api.tscircuit.com/'
token=json.loads(pathlib.Path('/workspace/.config/tscircuit-nodejs/config.json').read_text())['sessionToken']
def request(endpoint,body):
 req=urllib.request.Request(api+endpoint,data=json.dumps(body,separators=(',',':')).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
release=request('package_releases/get',{'package_name_with_version':name+'@'+version})['package_release']
query=urllib.parse.urlencode({'package_name':name,'use_latest_version':'true'})
with urllib.request.urlopen(api+'package_files/list?'+query,timeout=60) as r:rows=json.load(r)['package_files']
assert all(e['package_release_id']==release['package_release_id'] for e in rows),'Another release became latest during upload'
existing={e['file_path'] for e in rows};entries=[]
for p in sorted(stage.rglob('*')):
 if not p.is_file():continue
 path=p.relative_to(stage).as_posix()
 if path in existing:continue
 data=p.read_bytes();entry={'file_path':path}
 try:
  if p.suffix.lower() in ['.zip','.png','.pdf']:raise UnicodeDecodeError('binary',b'',0,1,'binary')
  entry['content_text']=data.decode()
 except UnicodeDecodeError:entry['content_base64']=base64.b64encode(data).decode()
 entries.append(entry)
def archive(entries):return base64.b64encode(gzip.compress(json.dumps({'files':entries},separators=(',',':'),ensure_ascii=False).encode(),compresslevel=9)).decode()
def upload(group):
 if not group:return
 encoded=archive(group);assert len(encoded)<3_000_000,'Individual compressed file exceeds safe upload size'
 request('package_files/upload_archive',{'package_name_with_version':name+'@'+version,'archive_base64':encoded});print('Uploaded',len(group),'missing files; encoded bytes',len(encoded),flush=True)
group=[]
for entry in entries:
 if group and len(archive(group+[entry]))>2_500_000:upload(group);group=[]
 group.append(entry)
upload(group)
request('package_releases/update',{'package_name_with_version':name+'@'+version,'ready_to_build':True,'license':'ISC'})
print('Finalized native registry release',name+'@'+version,flush=True)
