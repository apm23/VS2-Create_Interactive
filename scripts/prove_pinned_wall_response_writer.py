#!/usr/bin/env python3
import math
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: prove_pinned_wall_response_writer.py <minecraft-log>')

lines = [re.sub(r'\x1b\[[0-9;]*[mK]', '', x) for x in Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace').splitlines()]
num = r'[-+0-9.eE]+'
obb_re = re.compile(
    rf'GATE_E_CREATE_COLLIDE_MANY_RESULT index=(\d+)[^\n]*?surface=(true|false) '
    rf'temporal=({num}) response=\(({num}), ({num}), ({num})\) '
    rf'normal=\(({num}), ({num}), ({num})\)[^\n]*?player_tick=(\d+)'
)
setpos_re = re.compile(
    rf'GATE_E_LOCALPLAYER_SET_POS index=(\d+) from=({num}),({num}),({num}) to=({num}),({num}),({num}) '
    rf'delta=({num}),({num}),({num})[^\n]*callers=(.*)'
)
collide_re = re.compile(
    rf'GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index=(\d+) requested=({num}),({num}),({num}) '
    rf'allowed=({num}),({num}),({num})'
)

walls=[]
for line_no,line in enumerate(lines):
    m=obb_re.search(line)
    if not m: continue
    idx,surface,temporal,rx,ry,rz,nx,ny,nz,tick=m.groups()
    row={
        'line': line_no, 'index': int(idx), 'tick': int(tick), 'surface': surface == 'true',
        'temporal': float(temporal), 'response': tuple(float(x) for x in (rx,ry,rz)),
        'normal': tuple(float(x) for x in (nx,ny,nz)),
    }
    if row['surface'] and abs(row['normal'][1]) < 0.5 and max(abs(row['normal'][0]),abs(row['normal'][2])) >= 0.5:
        walls.append(row)
if not walls:
    raise SystemExit('WALL_RESPONSE_WRITER_PROOF no directional wall OBB rows')

def zero(v): return sum(x*x for x in v) <= 1.0e-12
for row in walls:
    row['temporal_only'] = zero(row['response']) and 0.0 < row['temporal'] < 1.0
    # Correlate only within the immediate response-consumption neighborhood. This is diagnostic
    # line-order evidence, not a new gameplay assertion.
    lo=max(0,row['line']-24); hi=min(len(lines),row['line']+25)
    create_setpos=[]
    collide_rows=[]
    for j in range(lo,hi):
        sm=setpos_re.search(lines[j])
        if sm and ('ContraptionCollider#collideEntities' in sm.group(11) or 'ContraptionCollider#collide' in sm.group(11)):
            dx,dy,dz=(float(sm.group(8)),float(sm.group(9)),float(sm.group(10)))
            create_setpos.append((j,int(sm.group(1)),dx,dy,dz,sm.group(11)))
        cm=collide_re.search(lines[j])
        if cm:
            collide_rows.append((j,int(cm.group(1)),tuple(float(cm.group(k)) for k in range(2,5)),tuple(float(cm.group(k)) for k in range(5,8))))
    row['create_setpos']=create_setpos
    row['collide_rows']=collide_rows

temporal_only=[r for r in walls if r['temporal_only']]
unresolved=[r for r in walls if zero(r['response']) and not r['temporal_only']]
nonzero=[r for r in walls if not zero(r['response'])]
writer_rows=[r for r in walls if r['create_setpos']]
collide_rows=[r for r in walls if r['collide_rows']]

if unresolved:
    classification='PINNED_WALL_ZERO_RESPONSE_UNRESOLVED_TEMPORAL'
elif len(temporal_only)==len(walls):
    classification='PINNED_WALL_RESPONSE_TEMPORAL_ONLY_VALID'
elif nonzero:
    classification='PINNED_WALL_RESPONSE_MIXED_VALID_PATHS'
else:
    classification='PINNED_WALL_RESPONSE_INCOMPLETE'

print(
    'M1_PINNED_WALL_RESPONSE_WRITER_PROOF '
    f'classification={classification} wall_rows={len(walls)} '
    f'temporal_only_rows={len(temporal_only)} unresolved_zero_rows={len(unresolved)} nonzero_response_rows={len(nonzero)} '
    f'wall_ticks={[r["tick"] for r in walls]} '
    f'wall_temporals={[round(r["temporal"],9) for r in walls]} '
    f'create_setpos_neighborhood_rows={len(writer_rows)} collide_neighborhood_rows={len(collide_rows)} '
    'source_run=35089177675 source_artifact=10444135201 production_unchanged=true read_only=true final_ready=false'
)
for r in walls:
    print(
        'M1_PINNED_WALL_ROW '
        f'tick={r["tick"]} obb_index={r["index"]} temporal={r["temporal"]:.12g} '
        f'response={r["response"]} normal={r["normal"]} temporal_only={str(r["temporal_only"]).lower()} '
        f'near_create_setpos={len(r["create_setpos"])} near_localplayer_collide={len(r["collide_rows"])}'
    )
