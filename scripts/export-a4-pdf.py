"""Export native A4 SVG sheets as a compact, searchable vector PDF."""
from pathlib import Path
from io import BytesIO
import cairosvg
import xml.etree.ElementTree as ET
from pypdf import PdfReader, PdfWriter
r=Path(__file__).resolve().parents[1]
writer=PdfWriter()
paths=sorted((r/'artifacts').glob('schematic-a4-page-*.svg'))
assert paths
for p in paths:
    svg=ET.fromstring(p.read_bytes())
    for node in svg.iter():
        if node.tag.endswith("text"):
            node.set("stroke", "none")
            node.set("font-family", "DejaVu Sans")
            if "sch-component-text" in node.get("class", ""):
                # SVG viewBox uses 10 units/mm: 6.5pt = 22.9306 SVG units.
                size=float(node.get("font-size", "0px").replace("px", ""))
                node.set("font-size", f"{max(size, 6.5*25.4/72*10):.6f}px")
            node.attrib.pop("stroke-width", None)
            node.attrib.pop("paint-order", None)
    for node in svg.iter():
        if node.tag.endswith("text") and node.text in ["R_USB_SENSE_H", "R_USB_SENSE_L"]:
            node.set("y", str(float(node.get("y"))-26))
            if node.text=="R_USB_SENSE_L":
                node.set("text-anchor", "end")
                node.set("x", str(float(node.get("x"))-16))
    for node in svg.iter():
        if node.tag.endswith("text") and node.text in ["C_BUCK_OUT1", "C_BUCK_OUT2", "C_BUCK_OUT3"]:
            node.set("text-anchor", "middle")
            node.set("x", str(float(node.get("x"))-16))
            if node.text=="C_BUCK_OUT2":node.set("y", str(float(node.get("y"))-65))
        if node.tag.endswith("text") and node.text=="Charge pump, motor decoupling & clamp":node.text="Charge pump & motor decoupling"
    reader=PdfReader(BytesIO(cairosvg.svg2pdf(bytestring=ET.tostring(svg))))
    assert len(reader.pages)==1
    page=reader.pages[0]
    assert abs(float(page.mediabox.width)*25.4/72-297)<.01
    assert abs(float(page.mediabox.height)*25.4/72-210)<.01
    writer.add_page(page)
with (r/'artifacts/schematic-a4.pdf').open('wb') as f: writer.write(f)
print('Exported',len(paths),'vector A4 landscape sheets, 297 x 210 mm')
