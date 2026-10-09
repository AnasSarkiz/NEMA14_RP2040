"""Draw current harness/carrier datums and assembled installation views."""
import pathlib,json,hashlib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle,Circle
root=pathlib.Path(__file__).resolve().parents[1];out=root/'artifacts/assembly';m=json.loads((root/'artifacts/mechanical/mechanical-review.json').read_text());h=m['service_harness'];b=m['mounted_assembly_bbox_mm'];title=m['project']
with PdfPages(out/'harness-carrier-drawings.pdf')as pdf:
 for image in ['mounted-isometric','mounted-side','mounted-top']:
  fig,ax=plt.subplots(figsize=(11.69,8.27));ax.imshow(plt.imread(root/('artifacts/mechanical/'+image+'.png')));ax.axis('off');fig.suptitle(title+' — HAR-001 / HAR-002 installation',fontsize=14);fig.text(.05,.035,'Nominal installation envelopes; factory key/contact and lead stock qualification pending. No measured fit.',fontsize=9);pdf.savefig(fig);plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(11.69,8.27));ax=axes[0]
 ax.add_patch(Rectangle((-12,-49),24,14,fill=False,lw=2,label='HC-001 PEEK24×14×6'))
 ax.add_patch(Circle((0,-42),5.5,fill=False,label='VMQ linerØ11'))
 ax.add_patch(Circle((0,-42),5,fill=False,ls='--',label='Carrier clearanceØ10'))
 for v in h['wire_paths']:
  x,y=v['clamp_axis_mm'];ax.add_patch(Circle((x,y),.475,fill=False));ax.text(x,y+.7,str(v['pin']),ha='center')
 for x in [-9,9]:ax.add_patch(Circle((x,-42),1.35,fill=False));ax.text(x,-45,'M2.5×10',fontsize=8,ha='center')
 ax.axvline(0,color='gray',ls=':');ax.set_xlim(-15,15);ax.set_ylim(-51,-32);ax.set_aspect('equal');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.1),fontsize=8);ax.set_title('Clamp top datum, mm; X split halves');ax.set_xlabel('X mm');ax.set_ylabel('Y mm')
 ax=axes[1];ax.add_patch(Rectangle((-17.5,-22.5),35,40,fill=False,label='INS-00135×40×0.51'))
 for x,y in [(-13,-13),(13,-13),(-14.8,13),(14.8,13)]:ax.add_patch(Circle((x,y),2.4,fill=False))
 ax.set_xlim(-21,21);ax.set_ylim(-26,21);ax.set_aspect('equal');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.1),fontsize=8);ax.set_title('Barrier pattern,4×Ø4.8; sheet centerY−2.5');ax.set_xlabel('X mm');ax.set_ylabel('Y mm');fig.suptitle('HC-001 / INS-001 manufacture and assembly datums')
 fig.text(.07,.035,'Clamp boresØ0.95±0.05; accepted wireOD1.05..1.20. SeatZ−2.8; carrier±0.05. Certificates/preload/pull-test pending.',fontsize=9);fig.tight_layout(rect=(0,.08,1,.92));pdf.savefig(fig);fig.savefig(out/'harness-restraint-dimensions.svg');plt.close(fig)
 fig,ax=plt.subplots(figsize=(8.27,11.69));ax.axis('off')
 lines=['Front carrier:49.2×36.4×4mm;6061-T6/T651 ±0.05mm.', 'Front motor4×M3 at26±0.2square, depth≥4mm; never use rear screws.', 'Carrier4×Ø4.1±0.05 at26±0.05; Ø22.15±0.05 locating bore.', 'Pilot root reliefØ23.4±0.05×0.40±0.05deep from motor mating face.', 'Motor fasteners4×M3×8 +0.5mm washers; bounded engagement3.2..3.8mm.', 'Host4×M3 atX±21.6,Y±13;6mm available depth, engage4.5..5.5mm.', 'Host frontfaceZ−44.2; shaftprojection beyondhost14.9..17.1mm.', 'PCB4×M2.5×8; PEEKtop0.5/lower1mm; nominal metalengagement4.9mm.', 'Motor PCBheader:JST B4B-PH-K-S(LF)(SN), C131334; bore0.75±0.05.', 'MatePHR-4 +4×SPH-002T-P0.5S; AWG24..30, OD0.8..1.5mm.', '1 Black A+/OUT1A;2 Green A−/OUT1B;3 Red B+/OUT2A;4 Blue B−/OUT2B.', 'Belden83004:010100black /005100green /002100red /006100blue.', 'ExtensionnomOD1.1,PTFE200°C,minstaticbend11mm; modeled12mm.', 'HAR-002 factorylead OD/AWG/material unknown: inspectbeforecutting.', 'Individually insulated/staggered lapsplices in bounded2.8×8×2.8 envelopes.', 'Spliceinsulation candidateRT-375-1/8-X; certificate/process qualification pending.', 'Tail projection≤0.8,fillet≤0.5 belowPCB; qualified temperature-rated tailcaps.', 'INS-001Nomex4100.51; ≥150°C materialcertificate required.', 'HC-001PEEK/VMQ50±5ShoreA,2×M2.5×10;4mm nominalmetalengagement.', 'Headerwithdrawal≥10mm, grippinghousing; deenergize/discharge before unplug.', 'PD Tensility10-06137; DATA Tensility10-06139; maximumbody12.5×32.5×7.6.', 'USBpitch14mm; worstplacementbodyseparation1.3mm; reserveR30 bend.', 'R30 is hostspace, not manufacturer-qualified cablebend/fatigue radius.', 'Complete reservedbbox(mm): '+str([round(x,3)for x in b]), 'Minimum hostenvelope(mm): '+str([round(b[i+3]-b[i],3)for i in range(3)])]
 ax.text(0,1,'Assembly specification and host requirements',va='top',fontsize=15);ax.text(0,.95,'\n\n'.join(lines),va='top',fontsize=9);pdf.savefig(fig);plt.close(fig)
report={'source_sha256':hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'mechanical_report_sha256':hashlib.sha256((root/'artifacts/mechanical/mechanical-review.json').read_bytes()).hexdigest(),'drawings_sha256':hashlib.sha256((out/'harness-carrier-drawings.pdf').read_bytes()).hexdigest(),'physical_fit_verified':False};(out/'harness-drawings-review.json').write_text(json.dumps(report,indent=2)+'\n');print('Harness/carrier drawing PDF generated')
