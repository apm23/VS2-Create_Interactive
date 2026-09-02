#!/usr/bin/env python3
"""Validate complete M1 native locomotion/collision proof from production-world smoke."""
import math
import re
import sys
import time
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_vs2_26_2_m1_jump_proof.py <production-world-smoke.log>")
log_path = Path(sys.argv[1])

deadline = time.monotonic() + 3.0
continuity_wait_pattern = re.compile(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*local_feet=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)[^\n]*broadphase=(true|false)[^\n]*on_ground=(true|false)[^\n]*baseline_frame=(true|false)")
while True:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    landed_wait = re.search(r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)", text)
    stable_wait = []
    if landed_wait is not None:
        landed_wait_tick = int(landed_wait.group(1))
        for match in continuity_wait_pattern.finditer(text):
            sample = (int(match.group(1)), int(match.group(2)), float(match.group(3)), float(match.group(4)), float(match.group(5)), match.group(6)=="true", match.group(7)=="true", match.group(8)=="true")
            if sample[0] <= landed_wait_tick:
                continue
            if not (sample[5] and sample[6] and sample[7]):
                stable_wait = []
                continue
            if stable_wait:
                previous = stable_wait[-1]
                step_sq = (sample[2]-previous[2])**2 + (sample[3]-previous[3])**2 + (sample[4]-previous[4])**2
                if sample[0] != previous[0] + 1 or sample[1] != previous[1] or step_sq > 0.75**2:
                    stable_wait = []
            stable_wait.append(sample)
            if len(stable_wait) >= 5:
                break
        if len(stable_wait) >= 5:
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
backward_requested = need(r"GATE_E_M1_NATIVE_BACKWARD_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true", "native backward request")
backward_confirmed = need(r"GATE_E_M1_NATIVE_BACKWARD_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*native_motion=true", "native grounded backward confirmation")
strafe_requested = need(r"GATE_E_M1_NATIVE_STRAFE_REQUESTED[^\n]*player_tick=(\d+)[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*direction=right", "native right-strafe request")
strafe_confirmed = need(r"GATE_E_M1_NATIVE_STRAFE_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*native_motion=true[^\n]*direction=right", "native grounded right-strafe confirmation")
requested = need(r"GATE_E_M1_NATIVE_JUMP_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true", "native jump request")
airborne = need(r"GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*delta_y=([-+0-9.eE]+)[^\n]*on_ground=(?:true|false)[^\n]*fixture_only=true[^\n]*native_motion=true[^\n]*vertical_arc=true", "native airborne transition")
landed = need(r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*natural_fall=true", "natural landing")

walk_tick=int(walk.group(1)); backward_request_tick=int(backward_requested.group(1)); backward_tick=int(backward_confirmed.group(1)); backward_start=int(backward_confirmed.group(2)); backward_duration=int(backward_confirmed.group(3)); backward_speed_sq=float(backward_confirmed.group(4))
strafe_request_tick=int(strafe_requested.group(1)); strafe_tick=int(strafe_confirmed.group(1)); strafe_start=int(strafe_confirmed.group(2)); strafe_duration=int(strafe_confirmed.group(3)); strafe_speed_sq=float(strafe_confirmed.group(4))
request_tick=int(requested.group(1)); airborne_tick=int(airborne.group(1)); airborne_start=int(airborne.group(2)); delta_y=float(airborne.group(3)); landed_tick=int(landed.group(1)); landed_start=int(landed.group(2)); duration=int(landed.group(3))
if backward_start != backward_request_tick or backward_duration != backward_tick-backward_request_tick or backward_speed_sq <= 0.0004: raise SystemExit("M1 native backward proof is inconsistent")
if strafe_start != strafe_request_tick or strafe_duration != strafe_tick-strafe_request_tick or strafe_speed_sq <= 0.0004: raise SystemExit("M1 native strafe proof is inconsistent")
if not (walk_tick < backward_request_tick <= backward_tick <= strafe_request_tick <= strafe_tick < request_tick): raise SystemExit("M1 native locomotion ordering changed")
if not (airborne_start == request_tick == landed_start and request_tick <= airborne_tick < landed_tick and delta_y > 0.0 and duration == landed_tick-request_tick and duration >= 2): raise SystemExit("M1 native jump proof is inconsistent")
for forbidden_marker in ("GATE_E_PHASE85_CARRY_REPLAY", "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY"):
    if forbidden_marker in text: raise SystemExit("M1 native locomotion used compatibility carry recovery: " + forbidden_marker)

continuity_pattern = re.compile(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*local_feet=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)[^\n]*broadphase=(true|false)[^\n]*on_ground=(true|false)[^\n]*baseline_frame=(true|false)")
samples=[(int(m.group(1)),int(m.group(2)),float(m.group(3)),float(m.group(4)),float(m.group(5)),m.group(6)=="true",m.group(7)=="true",m.group(8)=="true") for m in continuity_pattern.finditer(text)]

floor_window=[s for s in samples if walk_tick<=s[0]<request_tick and s[5] and s[6] and s[7]]
best_floor=[]
for i in range(len(floor_window)):
    streak=[floor_window[i]]
    for sample in floor_window[i+1:]:
        previous=streak[-1]
        if sample[0]!=previous[0]+1 or sample[1]!=previous[1]: break
        streak.append(sample)
        ys=[s[3] for s in streak]
        if max(ys)-min(ys)>0.05: break
    ys=[s[3] for s in streak]
    if max(ys)-min(ys)<=0.05 and len(streak)>len(best_floor): best_floor=streak
if len(best_floor)<5: raise SystemExit("M1 floor proof missing five consecutive grounded supported samples on a stable carriage-local floor plateau")
floor_y=[s[3] for s in best_floor]; floor_y_span=max(floor_y)-min(floor_y)

frame_pattern=re.compile(r"GATE_E_PHASE171_CARRIAGE_FRAME_STEP[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*frame_step=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)")
frame_speed={}
for m in frame_pattern.finditer(text):
    key=(int(m.group(1)),int(m.group(2))); speed=math.sqrt(sum(float(m.group(i))**2 for i in range(3,6))); frame_speed[key]=max(frame_speed.get(key,0.0),speed)
speed_change_proof=None; supported=[s for s in samples if s[5] and s[6] and s[7]]
for previous,current in zip(supported,supported[1:]):
    if current[0]!=previous[0]+1 or current[1]!=previous[1]: continue
    local_step=math.dist(previous[2:5],current[2:5]); previous_speed=frame_speed.get((previous[0],previous[1])); current_speed=frame_speed.get((current[0],current[1]))
    if previous_speed is not None and current_speed is not None and local_step<=0.75 and abs(current_speed-previous_speed)>=1.0:
        speed_change_proof=(previous,current,previous_speed,current_speed,local_step); break
if speed_change_proof is None: raise SystemExit("M1 speed-change stability missing: no consecutive supported bounded-locomotion samples across material carriage speed change")

client_state_pattern = re.compile(r"GATE_E_CLIENT_STATE[^\n]*local_support=local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+);[^\n]*nearby_blocks=([^;]*)")
wall_geometry_seen = any(re.search(r"(?:^|\|)-?\d+, [123], -2(?:\||$)", m.group(4)) for m in client_state_pattern.finditer(text))
if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")
# Native strafe may cross a one-to-two-tick Create contact/handoff seam before ordinary grounded
# continuity resumes. Use the last supported baseline from that same bounded lease instead of
# requiring the immediately previous callback; the proof remains read-only and pre-request.
pre_window=[s for s in samples if strafe_request_tick-2<=s[0]<strafe_request_tick and s[5] and s[6] and s[7]]
after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+9, request_tick-1) and s[5] and s[6] and s[7]]
if not pre_window or not after_window: raise SystemExit("M1 wall proof missing supported carriage-local samples around native right-strafe")
start_sample=pre_window[-1]
after=[]
for i in range(len(after_window)):
    streak=[after_window[i]]
    for sample in after_window[i+1:]:
        previous=streak[-1]
        if sample[0]!=previous[0]+1 or sample[1]!=previous[1]: break
        streak.append(sample)
    if len(streak)>=3:
        candidate_z=[s[4] for s in streak]
        if max(candidate_z)-min(candidate_z)<=0.005:
            after=streak
            break
if len(after)<3: raise SystemExit("M1 wall proof did not retain three consecutive supported samples on one Create carriage during strafe")
start_z=start_sample[4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)
if min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")
strafe_move_pattern = re.compile(rf"GATE_E_PHASE201_WALK_MOVE_CALLER[^\n]*player_tick={strafe_request_tick}[^\n]*mover=SELF[^\n]*requested=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)")
strafe_move=strafe_move_pattern.search(text)
strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02
material_approach = start_z-min_z >= 0.015
plateau=None
for i in range(len(after)-2):
    candidate=after[i:i+3]
    if candidate[1][0]!=candidate[0][0]+1 or candidate[2][0]!=candidate[1][0]+1: continue
    candidate_z=[s[4] for s in candidate]
    stable_plateau=max(candidate_z)-min(candidate_z)<=0.005
    if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):
        plateau=candidate
        break
if plateau is None:
    if not material_approach and not strafe_requested_toward_wall: raise SystemExit(f"M1 wall proof lacks a native strafe request toward the occupied side: before_z={start_z} samples={wall_z}")
    raise SystemExit(f"M1 carriage side stable collision plateau missing: local_z_samples={wall_z}")
impact_z=[s[4] for s in plateau]

# Existing Phase66/73 telemetry already distinguishes a native ceiling stop: vanilla takeoff asks
# for +0.42 Y, the next airborne SELF move is vertically zero while finite overhead geometry is
# present, then ordinary negative-Y gravity resumes. This verifier is read-only.
move_pattern=re.compile(r"GATE_E_LOCALPLAYER_ENTITY_MOVE_HEAD[^\n]*player_tick=(\d+)[^\n]*mover=SELF[^\n]*requested=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+)[^\n]*on_ground=(true|false)")
moves=[(int(m.group(1)),float(m.group(2)),float(m.group(3)),float(m.group(4)),m.group(5)=="true") for m in move_pattern.finditer(text) if request_tick<=int(m.group(1))<=landed_tick]
takeoff=next((m for m in moves if m[0]==request_tick and m[2]>=0.40 and m[4]),None)
apex=next((m for m in moves if request_tick<m[0]<landed_tick and not m[4] and abs(m[2])<=1e-6),None)
descent=next((m for m in moves if apex is not None and apex[0]<m[0]<landed_tick and not m[4] and m[2]<=-0.05),None)
if takeoff is None or apex is None or descent is None: raise SystemExit(f"M1 ceiling collision signature missing: moves={moves}")
continuity_tick=None; overhead=[]
for line in text.splitlines():
    cm=re.search(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)", line)
    if cm: continuity_tick=int(cm.group(1))
    if continuity_tick is None or not (request_tick<=continuity_tick<=landed_tick) or "GATE_E_CLIENT_STATE" not in line: continue
    gm=re.search(r"lowest_bottom_over_head=([-+0-9.eE]+);ceiling_head_gap=([-+0-9.eE]+)", line)
    if gm:
        bottom=float(gm.group(1)); gap=float(gm.group(2))
        if bottom<1e100 and gap>=0.0: overhead.append((continuity_tick,bottom,gap))
if not overhead: raise SystemExit("M1 ceiling proof missing finite carriage overhead geometry during jump")

post_land=[s for s in samples if s[0]>landed_tick]; best_streak=[]; streak=[]
for sample in post_land:
    tick,carriage,x,y,z,broadphase,on_ground,baseline_frame=sample
    if not (broadphase and on_ground and baseline_frame): streak=[]; continue
    if not streak: streak=[sample]
    else:
        prev=streak[-1]; step_sq=(x-prev[2])**2+(y-prev[3])**2+(z-prev[4])**2
        if tick==prev[0]+1 and carriage==prev[1] and step_sq<=0.75**2: streak.append(sample)
        else: streak=[sample]
    if len(streak)>len(best_streak): best_streak=list(streak)
if len(best_streak)<5: raise SystemExit("M1 post-landing carriage stability missing")

speed_prev,speed_now,speed_before,speed_after,speed_local_step=speed_change_proof
print("M1_NATIVE_LOCOMOTION_PROOF "+f"walk={walk_tick} reverse_request={backward_request_tick} reverse_confirmed={backward_tick} reverse_speed_sq={backward_speed_sq} strafe_request={strafe_request_tick} strafe_confirmed={strafe_tick} strafe_speed_sq={strafe_speed_sq} floor_solid=true floor_samples={len(best_floor)} floor_y_span={floor_y_span:.9f} wall_solid=true wall_local_z_boundary={impact_z[-1]:.6f} wall_impact_ticks={plateau[0][0]}-{plateau[-1][0]} wall_impact_span={max(impact_z)-min(impact_z):.9f} ceiling_solid=true ceiling_stop_tick={apex[0]} ceiling_overhead_tick={overhead[0][0]} ceiling_gap={overhead[0][2]:.6f} speed_change_stable=true speed_change_ticks={speed_prev[0]}-{speed_now[0]} frame_speed={speed_before:.6f}->{speed_after:.6f} speed_change_local_step={speed_local_step:.9f} jump_request={request_tick} airborne={airborne_tick} landed={landed_tick} duration={duration} delta_y={delta_y} natural_fall=true replay_free=true recovery_free=true post_land_stable_samples={len(best_streak)}")