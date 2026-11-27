"""Expand the exact reviewed native JSON, validating both compressed and raw hashes."""
from pathlib import Path
import gzip,hashlib,json
r=Path('artifacts/iteration-12')
for e in json.loads((r/'compressed-manifest.json').read_text()):
 packed=(r/e['gzip']).read_bytes();assert hashlib.sha256(packed).hexdigest()==e['gzip_sha256'];raw=gzip.decompress(packed);assert hashlib.sha256(raw).hexdigest()==e['raw_sha256'];target=r/e['raw']
 if target.exists():assert target.read_bytes()==raw
 else:target.write_bytes(raw)
 print(target)
