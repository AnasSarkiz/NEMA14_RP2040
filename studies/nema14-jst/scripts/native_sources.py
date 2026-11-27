"""Native source owners include PCB-only manually placed vias, not fitted parts."""
def source_owner_names(board):
 owners={e['source_component_id']:e['name'] for e in board if e['type']=='source_component'}
 for e in board:
  if e['type']!='source_manually_placed_via':continue
  ident=e['source_manually_placed_via_id']
  if ident in owners:raise ValueError('Conflicting native source owner '+ident)
  owners[ident]=ident
 for e in board:
  if e['type']=='source_port' and e['source_component_id'] not in owners:raise ValueError('Unknown native source owner '+e['source_component_id'])
 return owners
