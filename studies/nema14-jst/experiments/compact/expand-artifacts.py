"""Expand archived native evidence without changing its bytes; never overwrite a mismatch."""
from pathlib import Path
import gzip,hashlib,json
root=Path(__file__).resolve().parents[2];manifest=json.loads((root/'artifacts/iteration-5/archive-manifest.json').read_text())
for e in manifest:
 target=root/e['path'];compressed=root/e['archive'];raw=gzip.decompress(compressed.read_bytes());assert hashlib.sha256(raw).hexdigest()==e['sha256']
 if target.exists():assert target.read_bytes()==raw,target
 else:target.write_bytes(raw)
print('Verified and expanded',len(manifest),'native evidence archives')
