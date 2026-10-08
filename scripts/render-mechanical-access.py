"""Supplementary top-access plan from measured native STEP bounds and probe records.
This is a conservative bounds drawing, not substituted fitted component CAD.
"""
import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/mechanical'
r=json.loads((OUT/'mechanical-review.json').read_text())
fig,ax=plt.subplots(figsize=(10,10))
ax.add_patch(Rectangle((-17.5,-17.5),35,35,facecolor='#f6faf6',edgecolor='#26653b',linewidth=2))
for m in r['component_models']:
 b=m['world_bbox_mm'];ax.add_patch(Rectangle((b[0],b[1]),b[3]-b[0],b[4]-b[1],facecolor='#dde2e6',edgecolor='#929aa1',linewidth=.5))
 if m['reference'] in ['J_PD','J_DATA','U_ESD','R_BOOT']:
  ax.text((b[0]+b[3])/2,(b[1]+b[4])/2+(.9 if m['reference']=='R_BOOT' else 0),m['reference'],ha='center',va='center',fontsize=8)
for x in [-13,13]:
 for y in [-13,13]:
  ax.add_patch(Circle((x,y),2.7,fill=False,edgecolor='#9b4a35',linestyle='--'))
  ax.add_patch(Circle((x,y),1.6,facecolor='white',edgecolor='#26653b'))
for p in r['bare_interface_top_probe_access']:
 x,y=p['xy_mm'];rad=p['tool_diameter_mm']/2
 ax.add_patch(Circle((x,y),rad,facecolor='#008aac',edgecolor='#004d65',zorder=5))
 if p['interface']=='J_BOOT':
  assert not p['straight_top_access_collisions'],'BOOT probe collision requires review'
boot=[p for p in r['bare_interface_top_probe_access'] if p['interface']=='J_BOOT']
if boot:
 bx=sum(p['xy_mm'][0] for p in boot)/len(boot);by=sum(p['xy_mm'][1] for p in boot)/len(boot)
 ax.annotate('BOOT: two Ø0.5 mm straight top probes\nNo native-model intersections',xy=(bx,by),xytext=(-15,19),fontsize=9,arrowprops={'arrowstyle':'->','color':'#008aac'},color='#004d65')
ax.text(-17,-20.8,'Gray: measured native STEP bounding boxes; blue: bounded top probes\nDashed circles: unchanged Ø5.4 mm fastener keepouts\nBounding boxes are conservative; exact 3D collision results are in mechanical-review.json',fontsize=9)
ax.set_xlim(-19,19);ax.set_ylim(-22,22);ax.set_aspect('equal');ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_title(r['project']+' — programming access plan\nFrozen geometry '+r['board_sha256'][:16],fontsize=12)
fig.tight_layout();fig.savefig(OUT/'programming-access-plan.png',dpi=160);fig.savefig(OUT/'programming-access-plan.svg',metadata={'Creator':'render-mechanical-access.py','Description':'Conservative measured native STEP bounds and exact recorded probe coordinates; not substituted component CAD.'});plt.close(fig)
