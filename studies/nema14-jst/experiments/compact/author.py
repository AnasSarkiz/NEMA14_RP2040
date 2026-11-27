"""Regenerate native authored paths from actual moved shunt/driver/amplifier pads."""
from pathlib import Path
import json,math
b=json.load(open('artifacts/iteration-5/cluster-placement.circuit.json'));sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};ports={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};co={sc[e['source_component_id']]:e for e in b if e['type']=='pcb_component'}
import sys,importlib.util
sys.path.insert(0,'scripts');spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def xy(n,p):q=ports[n,p];return [q['x'],q['y']]
def geom(n,p):return g.pad_shape(pads[ports[n,p]['pcb_port_id']])
def local(n,p):
 c=co[n];a=math.radians(-c['rotation']);x=p[0]-c['center']['x'];y=p[1]-c['center']['y'];return {'x':x*math.cos(a)-y*math.sin(a),'y':x*math.sin(a)+y*math.cos(a)}
via=[];paths={};returns=[]
def v(name,p,net):via.append({'name':name,'x':p[0],'y':p[1],'net':net});return '.'+name
A=xy('R_SHUNT_A','pin1');AN=xy('R_SHUNT_A','pin2');BP=xy('R_SHUNT_B','pin1');BN=xy('R_SHUNT_B','pin2');a1=geom('R_SHUNT_A','pin1').bounds;a2=geom('R_SHUNT_A','pin2').bounds;b1=geom('R_SHUNT_B','pin1').bounds;b2=geom('R_SHUNT_B','pin2').bounds
edges={'KELVIN_A_POS':[A[0],a1[3]],'KELVIN_A_NEG':[AN[0],a2[1]],'KELVIN_B_POS':[b1[2],BP[1]],'KELVIN_B_NEG':[b2[0],BN[1]]}
def path(name,phase,pin,ps):
 n='R_SHUNT_'+phase;paths[name]={'anchor':'.'+n+' > .'+pin,'paths':[[p if isinstance(p,str) else local(n,p) for p in part] for part in ps]}
ad=xy('U_DRV','OUT1A');bd=xy('U_DRV','OUT2A');adt=[ad[0],geom('U_DRV','OUT1A').bounds[1]];bdt=[bd[0],geom('U_DRV','OUT2A').bounds[1]]
vas=v('V_PA_S',[A[0],.1],'A_DRV_PLUS');vad=v('V_PA_D',[ad[0],4.2],'A_DRV_PLUS');path('POWER_A_DRV','A','pin1',[[ '.R_SHUNT_A > .pin1',[A[0],a1[1]],vas+' > .top'],[vas+' > .inner2',[A[0],2.775],[ad[0],2.775],vad+' > .inner2'],[vad+' > .top',adt]])
acs=v('V_CA_S',[11.8,3.95],'A_PLUS');act=v('V_CA_T',[13.25,xy('J_MOTOR','A_PLUS')[1]],'A_PLUS');path('POWER_A_COIL','A','pin2',[[ '.R_SHUNT_A > .pin2',[AN[0],a2[3]],acs+' > .top'],[acs+' > .inner2',[14.1,3.95],[14.1,xy('J_MOTOR','A_PLUS')[1]],act+' > .inner2'],[act+' > .top','.J_MOTOR > .A_PLUS']])
vbs=v('V_PB_S',[6,1.8],'B_DRV_PLUS');vbd=v('V_PB_D',[8.65,4.05],'B_DRV_PLUS');path('POWER_B_DRV','B','pin1',[[ '.R_SHUNT_B > .pin1',[b1[0],BP[1]],[6.025,BP[1]],[6.025,1.8],vbs+' > .top'],[vbs+' > .bottom',[6,.8],[8.8,.8],[8.8,4.05],vbd+' > .bottom'],[vbd+' > .top',[bd[0],4.05],bdt]])
bcs=v('V_CB_S',[9.45,1.7],'B_PLUS');bct=v('V_CB_T',[13.25,xy('J_MOTOR','B_PLUS')[1]],'B_PLUS');path('POWER_B_COIL','B','pin2',[[ '.R_SHUNT_B > .pin2',[b2[2],BN[1]],[9.45,BN[1]],bcs+' > .top'],[bcs+' > .inner2',[8.8,1.7],[8.8,-1.3],bct+' > .inner2'],[bct+' > .top','.J_MOTOR > .B_PLUS']])
path('KELVIN_A_POS','A','pin1',[[ '.R_SHUNT_A > .pin1',edges['KELVIN_A_POS'],[11.3,edges['KELVIN_A_POS'][1]],[11.3,1.3],[xy('U_IA','IN_POS')[0],1.3],'.U_IA > .IN_POS']])
akn=v('V_KAN_S',[11.8,edges['KELVIN_A_NEG'][1]],'A_PLUS');aknt=v('V_KAN_T',[xy('U_IA','IN_NEG')[0],1.3],'A_PLUS');path('KELVIN_A_NEG','A','pin2',[[ '.R_SHUNT_A > .pin2',edges['KELVIN_A_NEG'],akn+' > .top'],[akn+' > .bottom',aknt+' > .bottom'],[aknt+' > .top','.U_IA > .IN_NEG']])
bkp=v('V_KBP_S',[7.55,2.0],'B_DRV_PLUS');bkpt=v('V_KBP_T',[9.5,xy('U_IB','IN_POS')[1]-.125],'B_DRV_PLUS');path('KELVIN_B_POS','B','pin1',[[ '.R_SHUNT_B > .pin1',edges['KELVIN_B_POS'],[7.55,BP[1]],bkp+' > .top'],[bkp+' > .inner1',[8.8,0],bkpt+' > .inner1'],[bkpt+' > .top','.U_IB > .IN_POS']])
bkn=v('V_KBN_S',[7.75,3.425],'B_PLUS');bknt=v('V_KBN_T',[9.5,xy('U_IB','IN_NEG')[1]],'B_PLUS');path('KELVIN_B_NEG','B','pin2',[[ '.R_SHUNT_B > .pin2',edges['KELVIN_B_NEG'],[7.95,BN[1]],bkn+' > .top'],[bkn+' > .inner1',bknt+' > .inner1'],[bknt+' > .top','.U_IB > .IN_NEG']])
ep=geom('U_DRV','EP');left=geom('U_DRV','GND18');right=geom('U_DRV','GND');stars={'A':[(ep.bounds[0]+left.bounds[2])/2,xy('U_DRV','GND18')[1]],'B':[(ep.bounds[2]+right.bounds[0])/2,xy('U_DRV','GND')[1]]};sources={'A':[4.3,7.45],'B':[11.0,6.7]}
for phase in 'AB':
 vs=v('V_G'+phase,sources[phase],'GND');vt=v('V_STAR_'+phase,stars[phase],'GND')
 for suffix,source,target in [('TOP','.R_S'+phase+' > .pin2',vs+' > .top'),('INNER',vs+' > .inner1',vt+' > .inner1'),('EP',vt+' > .top','.U_DRV > .EP')]:returns.append({'name':'RETURN_'+phase+'_'+suffix,'from':source,'to':target,'paths':[[source,target]]})
report={'paths':paths,'vias':via,'returns':returns,'actual_pad_edges':edges,'star_landings':stars,'source_vias':sources,'min_via_hole_mm':.3,'manufacturing_qualified':False}
Path('experiments/compact/authored.json').write_text(json.dumps(report,indent=2)+'\n');print('authored branches',len(paths),'vias',len(via),'ground segments',len(returns))
