from pathlib import Path
import json,hashlib,gzip
r=Path('artifacts/iteration-14')
for item in json.loads((r/'compressed-artifacts.json').read_text()):
 z=(r/(item['path']+'.gz')).read_bytes();assert hashlib.sha256(z).hexdigest()==item['gzip_sha256'];b=gzip.decompress(z);assert hashlib.sha256(b).hexdigest()==item['raw_sha256'];p=r/item['path']
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
print('Expanded/verified5 native evidence archives')
