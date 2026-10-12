"""Copy delivered preview and extract only the actual current native Gerber archive."""
import pathlib,zipfile,json,hashlib
root=pathlib.Path(__file__).resolve().parents[1];board=root/'artifacts/board.circuit.json';(root/'index.circuit.json').write_bytes(board.read_bytes());out=root/'artifacts/manufacturing';out.mkdir(exist_ok=True)
with zipfile.ZipFile(root/'artifacts/nema14-gerbers.zip') as z:
 members={pathlib.Path(n).name:z.read(n) for n in z.namelist() if not n.endswith('/')};assert len(members)==len([n for n in z.namelist() if not n.endswith('/')]),'Ambiguous archive member basename'
 for path in out.iterdir():
  if path.is_file() and path.suffix.lower() in ['.gbr','.drl','.csv'] and path.name not in members:path.unlink()
 for name,data in members.items():(out/name).write_bytes(data)
print('Current preview copied; native manufacturing members extracted:',len(members))
