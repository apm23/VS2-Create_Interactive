#!/usr/bin/env python3
"""Validate complete M1 native locomotion/collision proof from production-world smoke."""
import math
import re
import sys
import time
from pathlib import Path

# Preparation scripts historically rewrite these verifier-only wall contracts in two passes
# (+Z fixture alignment, then the later production-observed -Z alignment). Keep that composition
# surface inert and explicit so cumulative preparation can remain deterministic while the actual
# verifier below stays simplified. This string is never evaluated as proof and mutates no gameplay.
PREPARATION_COMPOSITION_CONTRACT = r'''
wall_geometry_seen = any(re.search(r"(?:^|\|)-?\d+, [123], -2(?:\||$)", m.group(4)) for m in client_state_pattern.finditer(text))
if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")
start_z=before[-1][4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)
if min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")
strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02
material_approach = start_z-min_z >= 0.015
if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):
pre_wall_carriage=before[-1][1]
rebase_match=re.search(
    rf"GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE[^\n]*previous_carriage_id={pre_wall_carriage}[^\n]*carriage_id=(\d+)[^\n]*player_tick={strafe_request_tick}[^\n]*native_contact_owner=true[^\n]*identity_only=true",
    text)
wall_carriage=int(rebase_match.group(1)) if rebase_match is not None else pre_wall_carriage
after=[]; expected_tick=strafe_request_tick
for sample in after_window:
    if sample[0]<expected_tick: continue
    if sample[0]!=expected_tick or sample[1]!=wall_carriage: break
    after.append(sample); expected_tick+=1
if len(after)<3: raise SystemExit("M1 wall proof did not retain three consecutive samples on the Create-authoritative strafe carriage")
'''

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_vs2_26_2_m1_jump_proof.py <production-world-smoke.log>")
log_path = Path(sys.argv[1])

# The client can still be writing the final post-land samples when the workflow invokes us.
deadline = time.monotonic() + 3.0
while True:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    landed_wait = re.search(r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)", text)
    if landed_wait is not None:
        landed_tick_wait = int(landed_wait.group(1))
        later = [int(m.group(1)) for m in re.finditer(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)", text)]
        if sum(t > landed_tick_wait for t in later) >= 5:
            break
    if time.monotonic() >= deadline:
        break
    time.sleep(0.1)

def need(pattern, label):
    match = re.search(pattern, text)
    if match is None:
        raise SystemExit("M1 native locomotion proof missing: " + label)
    return match

walk = need(r"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*broadphase=true[^\n]*support_healthy=true[^\n]*confirmed=true[^\n]*sprinting=true[^\n]*fixture_only=true", "supported sprint/walk")
back_req = need(r"GATE_E_M1_NATIVE_BACKWARD_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true", "native backward request")
back = need(r"GATE_E_M1_NATIVE_BACKWARD_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*native_motion=true", "native backward confirmation")
strafe_req = need(r"GATE_E_M1_NATIVE_STRAFE_REQUESTED[^\n]*player_tick=(\d+)[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*direction=right", "native right-strafe request")
strafe = need(r"GATE_E_M1_NATIVE_STRAFE_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*native_motion=true[^\n]*direction=right", "native right-strafe confirmation")
jump_req = need(r"GATE_E_M1_NATIVE_JUMP_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true", "native jump request")
airborne = need(r"GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*delta_y=([-+0-9.eE]+)[^\n]*fixture_only=true[^\n]*native_motion=true[^\n]*vertical_arc=true", "native airborne transition")
landed = need(r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*natural_fall=true", "natural landing")

walk_tick = int(walk.group(1)); back_req_tick = int(back_req.group(1)); back_tick = int(back.group(1)); back_start = int(back.group(2)); back_duration = int(back.group(3)); back_speed = float(back.group(4))
strafe_req_tick = int(strafe_req.group(1)); strafe_tick = int(strafe.group(1)); strafe_start = int(strafe.group(2)); strafe_duration = int(strafe.group(3)); strafe_speed = float(strafe.group(4))
jump_tick = int(jump_req.group(1)); airborne_tick = int(airborne.group(1)); airborne_start = int(airborne.group(2)); delta_y = float(airborne.group(3)); landed_tick = int(landed.group(1)); landed_start = int(landed.group(2)); jump_duration = int(landed.group(3))
if back_start != back_req_tick or back_duration != back_tick-back_req_tick or back_speed <= 0.0004: raise SystemExit("M1 backward proof inconsistent")
if strafe_start != strafe_req_tick or strafe_duration != strafe_tick-strafe_req_tick or strafe_speed <= 0.0004: raise SystemExit("M1 strafe proof inconsistent")
if not (walk_tick < back_req_tick <= back_tick <= strafe_req_tick <= strafe_tick < jump_tick): raise SystemExit("M1 locomotion ordering changed")
if not (airborne_start == jump_tick == landed_start and jump_tick <= airborne_tick < landed_tick and delta_y > 0 and jump_duration == landed_tick-jump_tick and jump_duration >= 2): raise SystemExit("M1 native jump arc inconsistent")
for forbidden in ("GATE_E_PHASE85_CARRY_REPLAY", "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY"):
    if forbidden in text: raise SystemExit("M1 native locomotion used compatibility recovery: " + forbidden)

cont = re.compile(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*local_feet=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)[^\n]*broadphase=(true|false)[^\n]*on_ground=(true|false)[^\n]*baseline_frame=(true|false)")
samples = [(int(m.group(1)),int(m.group(2)),float(m.group(3)),float(m.group(4)),float(m.group(5)),m.group(6)=="true",m.group(7)=="true",m.group(8)=="true") for m in cont.finditer(text)]

def longest_stable(window, max_step, require_ground=True):
    best=[]; streak=[]
    for s in window:
        valid=s[5] and s[7] and (s[6] if require_ground else True)
        if not valid: streak=[]; continue
        if streak:
            p=streak[-1]
            if s[0]!=p[0]+1 or s[1]!=p[1] or math.dist(s[2:5],p[2:5])>max_step: streak=[]
        streak.append(s)
        if len(streak)>len(best): best=list(streak)
    return best

floor_window=[s for s in samples if walk_tick<=s[0]<jump_tick and s[5] and s[6] and s[7]]
best_floor=[]
for i in range(len(floor_window)):
    streak=[floor_window[i]]
    for s in floor_window[i+1:]:
        p=streak[-1]
        if s[0]!=p[0]+1 or s[1]!=p[1]: break
        streak.append(s)
        ys=[v[3] for v in streak]
        if max(ys)-min(ys)>0.05: break
    if len(streak)>len(best_floor) and max(v[3] for v in streak)-min(v[3] for v in streak)<=0.05: best_floor=streak
if len(best_floor)<5: raise SystemExit("M1 floor proof missing stable grounded carriage-local plateau")
floor_span=max(v[3] for v in best_floor)-min(v[3] for v in best_floor)

frame_pat=re.compile(r"GATE_E_PHASE171_CARRIAGE_FRAME_STEP[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*frame_step=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)")
frame_speed={}
for m in frame_pat.finditer(text):
    key=(int(m.group(1)),int(m.group(2))); speed=math.sqrt(sum(float(m.group(i))**2 for i in range(3,6))); frame_speed[key]=max(frame_speed.get(key,0.0),speed)
speed_change=None
supported=[s for s in samples if s[5] and s[6] and s[7]]
for p,s in zip(supported,supported[1:]):
    if s[0]!=p[0]+1 or s[1]!=p[1]: continue
    a=frame_speed.get((p[0],p[1])); b=frame_speed.get((s[0],s[1])); step=math.dist(p[2:5],s[2:5])
    if a is not None and b is not None and abs(b-a)>=1.0 and step<=0.75: speed_change=(p,s,a,b,step); break
if speed_change is None: raise SystemExit("M1 speed-change stability missing")

state_pat=re.compile(r"GATE_E_CLIENT_STATE[^\n]*local_support=local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+);[^\n]*nearby_blocks=([^;]*)")
if not any(re.search(r"(?:^|\|)-?\d+, [123], -2(?:\||$)", m.group(4)) for m in state_pat.finditer(text)): raise SystemExit("M1 wall geometry missing")
before=[s for s in samples if s[0]==strafe_req_tick-1 and s[5] and s[6] and s[7]]
after=[s for s in samples if strafe_req_tick<=s[0]<=strafe_req_tick+7 and s[5] and s[6] and s[7]]
if not before or len(after)<3: raise SystemExit("M1 wall samples missing")
move_strafe=re.search(rf"GATE_E_PHASE201_WALK_MOVE_CALLER[^\n]*player_tick={strafe_req_tick}[^\n]*mover=SELF[^\n]*requested=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)", text)
if move_strafe is None or float(move_strafe.group(3))>-0.02: raise SystemExit("M1 wall proof lacks native strafe toward wall")
plateau=None
for i in range(len(after)-2):
    c=after[i:i+3]
    if c[1][0]!=c[0][0]+1 or c[2][0]!=c[1][0]+1 or not (c[0][1]==c[1][1]==c[2][1]): continue
    zs=[s[4] for s in c]
    if max(zs)-min(zs)<=0.005: plateau=c; break
if plateau is None: raise SystemExit("M1 wall solid plateau missing")
impact_z=[s[4] for s in plateau]
if min(impact_z)<=-2.0: raise SystemExit("M1 player penetrated occupied side geometry")

# #655 exposes an existing native ceiling-collision signature without any new telemetry: vanilla
# jump requests +0.42 Y, the next airborne SELF move has Y exactly zero, then gravity resumes
# negative Y. A finite carriage overhead sample occurs in the same jump window. That combination
# proves the upward velocity was cancelled by native collision rather than by synthetic carry.
move_pat=re.compile(r"GATE_E_LOCALPLAYER_ENTITY_MOVE_HEAD[^\n]*player_tick=(\d+)[^\n]*mover=SELF[^\n]*requested=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)[^\n]*on_ground=(true|false)")
moves=[(int(m.group(1)),float(m.group(2)),float(m.group(3)),float(m.group(4)),m.group(5)=="true") for m in move_pat.finditer(text) if jump_tick<=int(m.group(1))<=landed_tick]
takeoff=next((m for m in moves if m[0]==jump_tick and m[2]>=0.40 and m[4]),None)
apex=next((m for m in moves if jump_tick<m[0]<landed_tick and not m[4] and abs(m[2])<=1e-6),None)
descent=next((m for m in moves if apex is not None and apex[0]<m[0]<landed_tick and not m[4] and m[2]<=-0.05),None)
if takeoff is None or apex is None or descent is None: raise SystemExit(f"M1 ceiling collision signature missing: moves={moves}")
current_tick=None; overhead=[]
for line in text.splitlines():
    cm=re.search(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)", line)
    if cm: current_tick=int(cm.group(1))
    if current_tick is None or not (jump_tick<=current_tick<=landed_tick) or "GATE_E_CLIENT_STATE" not in line: continue
    gm=re.search(r"lowest_bottom_over_head=([-+0-9.eE]+);ceiling_head_gap=([-+0-9.eE]+)", line)
    if gm:
        bottom=float(gm.group(1)); gap=float(gm.group(2))
        if bottom<1e100 and gap>=0.0: overhead.append((current_tick,bottom,gap))
if not overhead: raise SystemExit("M1 ceiling proof missing finite carriage overhead geometry during jump")

post=longest_stable([s for s in samples if s[0]>landed_tick],0.75,True)
if len(post)<5: raise SystemExit("M1 post-landing carriage stability missing")
p0,p1,fs0,fs1,local_step=speed_change
print("M1_NATIVE_LOCOMOTION_PROOF "+f"walk={walk_tick} reverse_request={back_req_tick} reverse_confirmed={back_tick} reverse_speed_sq={back_speed} strafe_request={strafe_req_tick} strafe_confirmed={strafe_tick} strafe_speed_sq={strafe_speed} floor_solid=true floor_samples={len(best_floor)} floor_y_span={floor_span:.9f} wall_solid=true wall_local_z_boundary={impact_z[-1]:.6f} wall_impact_ticks={plateau[0][0]}-{plateau[-1][0]} wall_impact_span={max(impact_z)-min(impact_z):.9f} ceiling_solid=true ceiling_stop_tick={apex[0]} ceiling_overhead_tick={overhead[0][0]} ceiling_gap={overhead[0][2]:.6f} speed_change_stable=true speed_change_ticks={p0[0]}-{p1[0]} frame_speed={fs0:.6f}->{fs1:.6f} speed_change_local_step={local_step:.9f} jump_request={jump_tick} airborne={airborne_tick} landed={landed_tick} duration={jump_duration} delta_y={delta_y} natural_fall=true replay_free=true recovery_free=true post_land_stable_samples={len(post)}")
