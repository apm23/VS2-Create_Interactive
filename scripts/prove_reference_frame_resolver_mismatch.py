#!/usr/bin/env python3
import math
import re
import sys
from collections import defaultdict

if len(sys.argv) != 2:
    raise SystemExit('usage: prove_reference_frame_resolver_mismatch.py <minecraft-log>')
text = re.sub(r'\x1b\[[0-9;]*[mK]', '', open(sys.argv[1], encoding='utf-8', errors='replace').read())

jump = re.search(r'GATE_E_M1_NATIVE_JUMP_AIRBORNE player_tick=(\d+)[^\n]*delta_y=([-+0-9.eE]+)', text)
if not jump:
    raise SystemExit('ROOT_FRAME_PROOF missing native airborne marker')
jump_tick = int(jump.group(1))
rise = float(jump.group(2))
if rise <= 0:
    raise SystemExit(f'ROOT_FRAME_PROOF invalid jump rise {rise}')

state_re = re.compile(
    r'REFERENCE_OWNER_V2_POST_ARC_STATE player_tick=(\d+) owner_id=(-?\d+) owner_age=(\d+) '
    r'jump_active=(true|false) lifetime_limit=(\d+) age_within_lifetime=(true|false) '
    r'on_ground=(true|false) delta_y=([-+0-9.eE]+) owner_entity_present=(true|false) owner_local=([^ ]+) read_only=true')
support_re = re.compile(
    r'GATE_E_PHASE131_SUPPORT_SOURCE player_tick=(\d+) carriage_id=(\d+) physical_support=(true|false) '
    r'vertical_gap=([^ ]+) simplified_state=[^\n]*?local_feet=([^; ]+)[^\n]*?ceiling_head_gap=([^ ;]+) read_only=true')
writer_re = re.compile(
    r'GATE_E_LOCALPLAYER_SET_POS index=\d+ player_tick=(\d+) from=[^ ]+ to=[^ ]+ '
    r'delta=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+) [^\n]*callers=([^\n]+)')
frame_re = re.compile(
    r'GATE_E_PHASE171_CARRIAGE_FRAME_STEP player_tick=(\d+) carriage_id=(\d+) previous_player_tick=(\d+) '
    r'frame_step=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)')

states = {}
for m in state_re.finditer(text):
    local = None
    if ',' in m.group(10) and not m.group(10).startswith('error='):
        try: local = tuple(float(v) for v in m.group(10).split(','))
        except ValueError: pass
    states[int(m.group(1))] = dict(owner=int(m.group(2)), age=int(m.group(3)), jump=m.group(4)=='true',
                                    active=m.group(6)=='true', ground=m.group(7)=='true', local=local)

supports = {}
for m in support_re.finditer(text):
    try: local = tuple(float(v) for v in m.group(5).split(','))
    except ValueError: local = None
    try: ceiling = float(m.group(6))
    except ValueError: ceiling = math.nan
    supports[int(m.group(1))] = dict(carriage=int(m.group(2)), support=m.group(3)=='true', local=local, ceiling=ceiling)

pre = [s for t,s in states.items() if t <= jump_tick and s['owner'] >= 0]
if not pre:
    raise SystemExit('ROOT_FRAME_PROOF no owner before jump')
owner = pre[-1]['owner']
arc_ticks = sorted(t for t,s in states.items() if jump_tick <= t and s['owner'] == owner and s['active'])
if len(arc_ticks) < 20:
    raise SystemExit(f'ROOT_FRAME_PROOF insufficient owner lifecycle after jump owner={owner} ticks={arc_ticks}')
if not all(states[t]['jump'] for t in arc_ticks[:10]):
    raise SystemExit(f'ROOT_FRAME_PROOF jump latch not continuously active immediately after jump owner={owner}')

frame_delta = {}
for t in sorted(set(states) & set(supports)):
    s,c = states[t], supports[t]
    if t < jump_tick or s['owner'] != owner or c['carriage'] != owner or s['local'] is None or c['local'] is None:
        continue
    frame_delta[t] = math.dist(s['local'], c['local'])

bad_frame = {t:d for t,d in frame_delta.items() if d > 1e-3}
if not bad_frame:
    raise SystemExit('ROOT_FRAME_PROOF expected owner-vs-Create local frame divergence was not reproduced')
max_frame_tick = max(bad_frame, key=bad_frame.get)
max_frame_delta = bad_frame[max_frame_tick]
if max_frame_delta < 1.0:
    raise SystemExit(f'ROOT_FRAME_PROOF divergence too small max={max_frame_delta}')

writers = defaultdict(list)
for m in writer_re.finditer(text):
    if 'EntityDragger#dragEntitiesWithShips' not in m.group(5):
        continue
    writers[int(m.group(1))].append(tuple(float(m.group(i)) for i in (2,3,4)))

frames = defaultdict(list)
for m in frame_re.finditer(text):
    t, carriage, prev = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if carriage != owner or prev != t - 1:
        continue
    frames[t].append(tuple(float(m.group(i)) for i in (4,5,6)))

residuals = {}
writer_pairs = {}
for t in sorted(set(writers) & set(frames)):
    if t < jump_tick or t not in arc_ticks:
        continue
    body = writers[t][0]
    step = frames[t][0]
    residual = math.dist(body, step)
    residuals[t] = residual
    writer_pairs[t] = (body, step)

bad_writer = {t:d for t,d in residuals.items() if d > 1e-3}
if not bad_writer:
    raise SystemExit('ROOT_FRAME_PROOF expected EntityDragger/body-vs-carriage frame-step divergence was not reproduced')
max_writer_tick = max(bad_writer, key=bad_writer.get)
max_writer_residual = bad_writer[max_writer_tick]
if max_writer_residual < 1.0:
    raise SystemExit(f'ROOT_FRAME_PROOF writer divergence too small max={max_writer_residual}')

correlated = sorted(set(bad_frame) & set(bad_writer))
if not correlated:
    raise SystemExit(f'ROOT_FRAME_PROOF transform and writer divergence do not correlate bad_frame={bad_frame} bad_writer={bad_writer}')

ceiling_ticks = sorted(t for t in frame_delta if math.isfinite(supports[t]['ceiling']))
if not ceiling_ticks:
    raise SystemExit('ROOT_FRAME_PROOF no Create ceiling geometry observed during owner lifecycle')

print(
    'ROOT_REFERENCE_FRAME_RESOLVER_MISMATCH_PROOF'
    f' owner={owner}'
    f' jump_tick={jump_tick}'
    f' jump_rise={rise}'
    f' continuous_owner_ticks={arc_ticks[0]}..{arc_ticks[-1]}'
    f' frame_divergence_ticks={sorted(bad_frame)}'
    f' max_owner_vs_create_local_delta={max_frame_delta:.9f}'
    f' max_frame_delta_tick={max_frame_tick}'
    f' body_writer_divergence_ticks={sorted(bad_writer)}'
    f' max_body_vs_carriage_step_residual={max_writer_residual:.9f}'
    f' max_writer_residual_tick={max_writer_tick}'
    f' correlated_ticks={correlated}'
    f' body_vs_frame_at_max={writer_pairs[max_writer_tick]}'
    f' ceiling_geometry_ticks={ceiling_ticks[:24]}'
    ' conclusion=external_owner_identity_remains_active_but_EntityDragger_transform_can_leave_Create_collision_frame_during_jump_arc'
    ' create_collision_authority_unchanged=true body_writer_replacement_not_authorized=true read_only=true final_ready=false'
)
