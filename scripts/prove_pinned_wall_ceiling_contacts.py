#!/usr/bin/env python3
import math
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: prove_pinned_wall_ceiling_contacts.py <minecraft-log>')

text = re.sub(r'\x1b\[[0-9;]*[mK]', '', Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace'))
air = re.search(r'GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)', text)
if not air:
    raise SystemExit('PINNED_CONTACT_PROOF missing native airborne marker')
air_tick = int(air.group(1))

num = r'[-+0-9.eE]+'
row_re = re.compile(
    rf'GATE_E_CREATE_COLLIDE_MANY_RESULT index=(\d+)[^\n]*?surface=(true|false) '
    rf'temporal=({num}) response=\(({num}), ({num}), ({num})\) '
    rf'normal=\(({num}), ({num}), ({num})\)[^\n]*?player_tick=(\d+)[^\n]*?player_on_ground=(true|false)'
)
rows=[]
for m in row_re.finditer(text):
    idx,surface,temporal,rx,ry,rz,nx,ny,nz,tick,on_ground=m.groups()
    rows.append({
        'index': int(idx), 'surface': surface == 'true', 'temporal': float(temporal),
        'response': (float(rx),float(ry),float(rz)),
        'normal': (float(nx),float(ny),float(nz)),
        'tick': int(tick), 'on_ground': on_ground == 'true',
    })
if not rows:
    raise SystemExit('PINNED_CONTACT_PROOF no parseable OBB rows in pinned log')

surface=[r for r in rows if r['surface']]
def nonzero(v):
    return sum(x*x for x in v) > 1.0e-12

def horizontal_normal(r):
    nx,ny,nz=r['normal']
    return abs(ny) < 0.5 and max(abs(nx),abs(nz)) >= 0.5

def upward_normal(r):
    return r['normal'][1] >= 0.5

def downward_normal(r):
    return r['normal'][1] <= -0.5

wall=[r for r in surface if horizontal_normal(r)]
floor=[r for r in surface if upward_normal(r)]
ceiling=[r for r in surface if downward_normal(r)]
wall_nonzero=[r for r in wall if nonzero(r['response'])]
ceiling_nonzero=[r for r in ceiling if nonzero(r['response'])]
ceiling_air=[r for r in ceiling if r['tick'] >= air_tick]

if wall and ceiling_air:
    classification='PINNED_WALL_AND_CEILING_DIRECTIONAL_CONTACT_PRESENT'
elif wall:
    classification='PINNED_WALL_CONTACT_PRESENT_CEILING_CONTACT_NOT_OBSERVED'
elif ceiling_air:
    classification='PINNED_CEILING_CONTACT_PRESENT_WALL_CONTACT_NOT_OBSERVED'
else:
    classification='PINNED_WALL_CEILING_DIRECTIONAL_CONTACT_NOT_OBSERVED'

def ticks(rs):
    return sorted({r['tick'] for r in rs})[:32]

def normals(rs):
    out=[]
    for r in rs:
        n=tuple(round(v,6) for v in r['normal'])
        if n not in out: out.append(n)
        if len(out) >= 8: break
    return out

print(
    'M1_PINNED_WALL_CEILING_CONTACT_PROOF '
    f'classification={classification} airborne_tick={air_tick} '
    f'obb_rows={len(rows)} surface_rows={len(surface)} '
    f'wall_rows={len(wall)} wall_nonzero_response_rows={len(wall_nonzero)} wall_ticks={ticks(wall)} wall_normals={normals(wall)} '
    f'floor_rows={len(floor)} floor_ticks={ticks(floor)} '
    f'ceiling_rows={len(ceiling)} ceiling_airborne_rows={len(ceiling_air)} ceiling_nonzero_response_rows={len(ceiling_nonzero)} '
    f'ceiling_ticks={ticks(ceiling)} ceiling_normals={normals(ceiling)} '
    'source_run=35089177675 source_artifact=10444135201 production_unchanged=true read_only=true final_ready=false'
)
