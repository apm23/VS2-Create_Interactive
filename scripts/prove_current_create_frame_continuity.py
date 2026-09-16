#!/usr/bin/env python3
import math
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: prove_current_create_frame_continuity.py <minecraft-log>')

root = Path(__file__).resolve().parents[1]
post_arc_src = (root / 'scripts/prepare_vs2_26_2_natural_landing_post_arc_owner_trace.py').read_text(encoding='utf-8')
phase66_src = (root / 'scripts/prepare_vs2_26_2_phase66.py').read_text(encoding='utf-8')
resolver_src = (root / 'scripts/prepare_vs2_26_2_reference_owner_v1.py').read_text(encoding='utf-8')

# Source semantics: the old owner_local diagnostic intentionally calls the two-arg
# toLocalVector(..., 0.0f), while Phase66 explicitly uses Create's worldToLocalPos
# because toLocalVector is not the ContinuousOBBCollider frame during rotation.
required_source = [
    (post_arc_src, 'postArcOwnerEntity, player.position(), 0.0f'),
    (phase66_src, 'worldToLocalPos'),
    (phase66_src, 'Using toLocalVector here mixed two'),
    (resolver_src, '"toLocalVector", worldPosition, 0.0f, true'),
    (resolver_src, '"toGlobalVector", localPosition, 1.0f, false'),
]
for source, token in required_source:
    if token not in source:
        raise SystemExit('CURRENT_CREATE_FRAME_PROOF missing source semantic token: ' + token)

text = re.sub(r'\x1b\[[0-9;]*[mK]', '', Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace'))

air = re.search(r'GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)[^\n]*delta_y=([-+0-9.eE]+)', text)
if not air:
    raise SystemExit('CURRENT_CREATE_FRAME_PROOF missing native airborne marker')
air_tick = int(air.group(1))

state_re = re.compile(
    r'REFERENCE_OWNER_V2_POST_ARC_STATE player_tick=(\d+) owner_id=(-?\d+) owner_age=(\d+) '
    r'jump_active=(true|false) lifetime_limit=(\d+) age_within_lifetime=(true|false)')
states = [(int(t), int(o), j == 'true', live == 'true') for t, o, _age, j, _limit, live in state_re.findall(text)]
pre = [s for s in states if s[0] == air_tick and s[1] >= 0]
if not pre:
    raise SystemExit('CURRENT_CREATE_FRAME_PROOF no active owner at airborne tick')
owner = pre[-1][1]
owner_ticks = sorted(t for t, o, j, live in states if t >= air_tick and o == owner and j and live)
if len(owner_ticks) < 20:
    raise SystemExit(f'CURRENT_CREATE_FRAME_PROOF insufficient continuous owner lifecycle owner={owner} ticks={owner_ticks}')

candidate_lines = {}
for line in text.splitlines():
    if 'GATE_E_CARRIAGE_CANDIDATES player_tick=' not in line:
        continue
    m_tick = re.search(r'player_tick=(\d+)', line)
    if not m_tick:
        continue
    t = int(m_tick.group(1))
    candidate_lines[t] = line

def candidate_vecs(line, entity_id):
    marker = f'@id={entity_id};'
    idx = line.find(marker)
    if idx < 0:
        return None
    end = line.find(' || ', idx)
    seg = line[idx:] if end < 0 else line[idx:end]
    old = re.search(r'(?:^|;)local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)', seg)
    cur = re.search(r'(?:^|;)collider_local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)', seg)
    if not old or not cur:
        return None
    return tuple(float(x) for x in old.groups()), tuple(float(x) for x in cur.groups())

samples = {}
for t in owner_ticks:
    line = candidate_lines.get(t)
    if not line:
        continue
    v = candidate_vecs(line, owner)
    if v:
        samples[t] = v
if len(samples) < 20:
    raise SystemExit(f'CURRENT_CREATE_FRAME_PROOF insufficient Create-frame samples owner={owner} count={len(samples)}')

# The old diagnostic/current-collider disagreement is expected only on rotation update
# ticks. It must NOT be interpreted as player/body leaving Create's current frame.
diagnostic_divergence = {t: math.dist(old, cur) for t, (old, cur) in samples.items() if math.dist(old, cur) > 1.0}
if not diagnostic_divergence:
    raise SystemExit('CURRENT_CREATE_FRAME_PROOF historical diagnostic divergence not reproduced')

# Evaluate continuity only in Create's actual current collision frame.
current_steps = {}
for t in sorted(samples):
    if t - 1 not in samples:
        continue
    a = samples[t - 1][1]
    b = samples[t][1]
    current_steps[t] = math.hypot(b[0] - a[0], b[2] - a[2])

bad_current = {t: current_steps.get(t, math.inf) for t in diagnostic_divergence if current_steps.get(t, math.inf) > 0.25}
if bad_current:
    raise SystemExit(f'CURRENT_CREATE_FRAME_PROOF current Create frame discontinuity at diagnostic rotation ticks: {bad_current}')

# Phase131 uses the same worldToLocalPos frame as ContinuousOBBCollider. Require exact
# agreement with candidate collider_local_feet and require ceiling geometry to be visible.
support_re = re.compile(
    r'GATE_E_PHASE131_SUPPORT_SOURCE player_tick=(\d+) carriage_id=(\d+) physical_support=(?:true|false) '
    r'vertical_gap=[^ ]+ simplified_state=[^\n]*?local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)[^\n]*?ceiling_head_gap=([^ ;]+) read_only=true')
phase = {}
for m in support_re.finditer(text):
    t, c = int(m.group(1)), int(m.group(2))
    if c != owner:
        continue
    try:
        ceiling = float(m.group(6))
    except ValueError:
        ceiling = math.nan
    phase[t] = ((float(m.group(3)), float(m.group(4)), float(m.group(5))), ceiling)

frame_residual = {}
ceiling_ticks = []
for t, (_old, cur) in samples.items():
    if t not in phase:
        continue
    p, ceiling = phase[t]
    frame_residual[t] = math.dist(cur, p)
    if math.isfinite(ceiling):
        ceiling_ticks.append(t)
if not frame_residual:
    raise SystemExit('CURRENT_CREATE_FRAME_PROOF no Phase131/Create-frame overlap')
max_frame_residual = max(frame_residual.values())
if max_frame_residual > 1e-9:
    raise SystemExit(f'CURRENT_CREATE_FRAME_PROOF candidate-vs-Phase131 current frame mismatch {max_frame_residual}')

# The existing VS2 body writer must actually execute on every large old-vs-current
# rotation-update tick; this confirms those ticks are resolver/carry ticks, not missing owner ticks.
writer_ticks = set()
for m in re.finditer(r'GATE_E_LOCALPLAYER_SET_POS index=\d+ player_tick=(\d+)[^\n]*callers=([^\n]+)', text):
    if 'EntityDragger#dragEntitiesWithShips' in m.group(2):
        writer_ticks.add(int(m.group(1)))
missing_writer = sorted(set(diagnostic_divergence) - writer_ticks)
if missing_writer:
    raise SystemExit(f'CURRENT_CREATE_FRAME_PROOF diagnostic rotation ticks missing EntityDragger writer {missing_writer}')

max_diag_tick = max(diagnostic_divergence, key=diagnostic_divergence.get)
max_current_step_tick = max((t for t in diagnostic_divergence if t in current_steps), key=lambda t: current_steps[t])
print(
    'CURRENT_CREATE_COLLISION_FRAME_CONTINUITY_PROOF'
    f' owner={owner}'
    f' airborne_tick={air_tick}'
    f' continuous_owner_ticks={owner_ticks[0]}..{owner_ticks[-1]}'
    f' previous_rotation_diagnostic_divergence_ticks={sorted(diagnostic_divergence)}'
    f' max_old_diagnostic_vs_current_collision_delta={diagnostic_divergence[max_diag_tick]:.9f}'
    f' max_current_collision_frame_step_on_those_ticks={current_steps[max_current_step_tick]:.9f}'
    f' max_current_collision_frame_step_tick={max_current_step_tick}'
    f' max_candidate_vs_phase131_current_frame_residual={max_frame_residual:.12g}'
    f' ceiling_geometry_ticks={ceiling_ticks[:24]}'
    ' conclusion=old_toLocalVector_partial0_diagnostic_is_not_current_Create_collision_frame_and_does_not_prove_resolver_failure'
    ' current_Create_collision_frame_remains_continuous_through_observed_rotation_updates=true'
    ' external_owner_lifecycle_continuous=true EntityDragger_writer_present=true'
    ' Create_collision_authority_unchanged=true resolver_patch_not_authorized_from_old_mismatch=true'
    ' read_only=true final_ready=false'
)
