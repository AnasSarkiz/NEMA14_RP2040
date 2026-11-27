from pathlib import Path
import sys,json,math
sys.path.insert(0,'experiments/external-star')
from model import *
r=Path('artifacts/iteration-14');plan=read(r/'plan.json');assert plan['grid_search_found'];q=co['C_VREG'];p=ports['C_VREG','pin2'];a=-math.radians(q['rotation']);points=plan['path_mm'];local=[]
for x,y in points:
 dx=x-q['center']['x'];dy=y-q['center']['y'];local.append({'x':dx*math.cos(a)-dy*math.sin(a),'y':dx*math.sin(a)+dy*math.cos(a),'layer':'top'})
path={'name':'VREG_GROUND_LOOP','from':'.C_VREG > .pin2','to':'.U_DRV > .EP','anchor':'.C_VREG > .pin2','width_mm':.16,'world_points_mm':points,'local_points':local,'new_vias':0,'full_port_centre_wire_mm':plan['centreline_length_mm'],'clearance_and_width_rules_unchanged':True};Path('experiments/loop-check/path.json').write_text(json.dumps(path,indent=2)+'\n')
