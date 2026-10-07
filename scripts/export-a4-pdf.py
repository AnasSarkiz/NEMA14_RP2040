"""Export native A4 SVG sheets as a compact, searchable vector PDF."""
from pathlib import Path
from io import BytesIO
import cairosvg
from pypdf import PdfReader, PdfWriter
r=Path(__file__).resolve().parents[1]
writer=PdfWriter()
paths=sorted((r/'artifacts').glob('schematic-a4-page-*.svg'))
assert paths
for p in paths:
    reader=PdfReader(BytesIO(cairosvg.svg2pdf(bytestring=p.read_bytes())))
    assert len(reader.pages)==1
    page=reader.pages[0]
    assert abs(float(page.mediabox.width)*25.4/72-297)<.01
    assert abs(float(page.mediabox.height)*25.4/72-210)<.01
    writer.add_page(page)
with (r/'artifacts/schematic-a4.pdf').open('wb') as f: writer.write(f)
print('Exported',len(paths),'vector A4 landscape sheets, 297 x 210 mm')
