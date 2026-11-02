"""Keep unobstructed copper when a new route needs a local crossing cleared."""
from shapely.geometry import LineString
from shapely.ops import unary_union

def retained_trace_fragments(trace, new_copper, used_ids):
    cuts={layer:unary_union([shape for on_layer,shape in new_copper if on_layer==layer])
          for layer in ['top','inner1','inner2','bottom']}
    runs=[];run=[]
    for point in trace['route']:
        if point['route_type']!='wire':
            if len(run)>1:runs.append(run)
            run=[];continue
        if run and (point['layer']!=run[-1]['layer'] or point['width']!=run[-1]['width']):
            if len(run)>1:runs.append(run)
            run=[]
        run.append(point)
    if len(run)>1:runs.append(run)
    fragments=[]
    for run in runs:
        layer,width=run[0]['layer'],run[0]['width']
        original=LineString([(p['x'],p['y']) for p in run])
        retained=original.difference(cuts[layer].buffer(.15+width/2+.006))
        for piece in list(retained.geoms) if hasattr(retained,'geoms') else [retained]:
            if piece.geom_type!='LineString' or piece.length<.01:continue
            shape=piece.buffer(width/2)
            assert shape.difference(original.buffer(width/2+1e-8)).area<1e-7
            assert cuts[layer].is_empty or shape.distance(cuts[layer])>=.15-1e-6
            uid=trace['pcb_trace_id']+'_fragment_'+str(len(fragments))
            while uid in used_ids:uid+='_r'
            used_ids.add(uid)
            fragments.append({**trace,'pcb_trace_id':uid,'pcb_port_ids':[],
                              'route':[{'route_type':'wire','x':x,'y':y,'layer':layer,'width':width}
                                       for x,y in piece.coords]})
    return fragments
