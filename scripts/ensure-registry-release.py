"""Ensure the exact staged registry release exists before bounded uploads.

Readiness gates run in the publisher before this helper. The native create API
creates the same draft release as the CLI; recovery uploads and verifies files.
"""
import json,pathlib,sys,urllib.request,urllib.error
stage=pathlib.Path(sys.argv[1]);meta=json.loads((stage/'package.json').read_text())
name='AnasSarkiz/'+meta['name']+'@'+meta['version']
token=json.loads(pathlib.Path('/workspace/.config/tscircuit-nodejs/config.json').read_text())['sessionToken']
def request(endpoint):
 req=urllib.request.Request('https://registry-api.tscircuit.com/'+endpoint,data=json.dumps({'package_name_with_version':name}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
try:
 result=request('package_releases/get')
 assert result.get('package_release'), 'Unexpected release lookup response'
 print('Resuming exact staged registry release',name,flush=True)
except urllib.error.HTTPError as error:
 if error.code!=404:raise
 result=request('package_releases/create')
 assert result.get('package_release'), 'Registry did not return the created release'
 print('Created exact staged registry release',name,flush=True)
