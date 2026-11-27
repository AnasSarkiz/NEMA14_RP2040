"""Expand only published, hash-verified iteration evidence; never overwrite different data."""
from pathlib import Path
import json,gzip,hashlib
root=Path('artifacts/iteration-6')
for e in json.load(open(root/'compressed-manifest.json')):
 src=root/e['compressed'];dst=root/e['original'];assert hashlib.sha256(src.read_bytes()).hexdigest()==e['gzip_sha256'];data=gzip.decompress(src.read_bytes());assert len(data)==e['original_bytes'] and hashlib.sha256(data).hexdigest()==e['original_sha256']
 if dst.exists():assert dst.read_bytes()==data,'Different existing evidence: '+str(dst)
 else:dst.write_bytes(data)
print('Expanded verified NEMA14 JST diagnostic artifacts; no design changes')
