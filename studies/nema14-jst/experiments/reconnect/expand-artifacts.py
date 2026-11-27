"""Restore only exact hash-verified public diagnostic evidence; never overwrite different bytes."""
from pathlib import Path
import json,gzip,hashlib
root=Path('artifacts/iteration-8')
for e in json.load(open(root/'compressed-manifest.json')):
 p=root/e['compressed'];assert hashlib.sha256(p.read_bytes()).hexdigest()==e['gzip_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==e['original_bytes'] and hashlib.sha256(raw).hexdigest()==e['original_sha256'];dst=root/e['original']
 if dst.exists():assert dst.read_bytes()==raw,'Different existing evidence: '+str(dst)
 else:dst.write_bytes(raw)
print('Expanded exact NEMA14 JST CP2 and buzzer evidence')
