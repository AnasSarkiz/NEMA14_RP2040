"""Adapt CadQuery Y-up GLBs to the native CAD frame expected by tscircuit's GLB loader.
Only a root transform is added; all tessellated mesh/BIN bytes are preserved.
"""
from pathlib import Path
import base64,hashlib,json,math,struct
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/assembly'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=OUT/'asset-manifest.json';report=json.loads(p.read_text())
if report.get('tscircuit_native_Z_up_normalized'):
 for m in report['models'].values():assert sha(ROOT/m['path'])==m['sha256']
 assert sha(OUT/'models.json')==report['portable_models_json_sha256']
 print('Native CAD frame already normalized');raise SystemExit(0)
data={}
for name,model in report['models'].items():
 p=ROOT/model['path'];assert sha(p)==model['sha256'];raw=p.read_bytes()
 size,jtype=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+size]);tail=raw[20+size:]
 for scene in g['scenes']:
  root=len(g['nodes']);g['nodes'].append({'name':'TSCIRCUIT_NATIVE_Z_UP','rotation':[math.sqrt(.5),0,0,math.sqrt(.5)],'children':scene['nodes']});scene['nodes']=[root]
 encoded=json.dumps(g,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
 fixed=struct.pack('<III',0x46546c67,2,20+len(encoded)+len(tail))+struct.pack('<II',len(encoded),jtype)+encoded+tail
 model['CadQuery_Y_up_glb_sha256']=model['sha256'];model['mesh_BIN_bytes_unchanged_sha256']=hashlib.sha256(tail).hexdigest()
 p.write_bytes(fixed);model['sha256']=sha(p);model['bytes']=len(fixed);data[name]='data:model/gltf-binary;base64,'+base64.b64encode(fixed).decode()
(OUT/'models.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
report.update({'tscircuit_native_Z_up_normalized':True,'coordinates':'Native CAD mm, PCB midplane Z0. Root +90deg X cancels CadQuery -90deg export without editing mesh/BIN bytes. tscircuit loader maps CAD(x,y,z) to Scene3D(x,z,y); final tscircuit glTF export maps to(-x,z,y).','normalization_script_sha256':sha(Path(__file__)),'portable_models_json_sha256':sha(OUT/'models.json')})
(OUT/'asset-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Normalized all eight models; mesh bytes unchanged')
