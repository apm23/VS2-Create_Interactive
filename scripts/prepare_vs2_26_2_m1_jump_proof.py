#!/usr/bin/env python3
"""Validate native M1 locomotion plus real carriage floor/wall collision from production-world smoke."""
import math
import re
import sys
import time
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_vs2_26_2_m1_jump_proof.py <production-world-smoke.log>")

log_path = Path(sys.argv[1])
# The workflow invokes this verifier as soon as the native landing marker appears. Run #535
# proved that can race the five post-land continuity samples: landing was tick 57 while only tick
# 58 had reached the log. Wait only for already-running read-only continuity telemetry; do not
# extend fixture input, movement, collision, or any gameplay state.
deadline = time.monotonic() + 3.0
while True:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    landed_wait = re.search(r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)", text)
    if landed_wait is not None:
        landed_wait_tick = int(landed_wait.group(1))
        continuity_ticks = [int(value) for value in re.findall(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)", text)]
        if continuity_ticks and max(continuity_ticks) >= landed_wait_tick + 5:
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
strafe_confirmed = need(r"GATE_E_M1_NATIVE_STRAFE_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true[^\n]*native_motion=true[^\n]*direction=right", "native right-strafe confirmation")
requested = need(r"GATE_E_M1_NATIVE_JUMP_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true", "native jump request")
airborne = need(r"GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*delta_y=([-+0-9.eE]+)[^\n]*on_ground=(?:true|false)[^\n]*fixture_only=true[^\n]*native_motion=true[^\n]*vertical_arc=true", "native airborne transition")
landed = need(r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)[^\n]*duration_ticks=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*natural_fall=true", "natural landing")

walk_tick = int(walk.group(1)); backward_request_tick = int(backward_requested.group(1)); backward_tick = int(backward_confirmed.group(1)); backward_start = int(backward_confirmed.group(2)); backward_duration = int(backward_confirmed.group(3)); backward_speed_sq = float(backward_confirmed.group(4)); strafe_request_tick = int(strafe_requested.group(1)); strafe_tick = int(strafe_confirmed.group(1)); strafe_start = int(strafe_confirmed.group(2)); strafe_duration = int(strafe_confirmed.group(3)); strafe_speed_sq = float(strafe_confirmed.group(4)); request_tick = int(requested.group(1)); airborne_tick = int(airborne.group(1)); airborne_start = int(airborne.group(2)); delta_y = float(airborne.group(3)); landed_tick = int(landed.group(1)); landed_start = int(landed.group(2)); duration = int(landed.group(3))

if backward_start != backward_request_tick: raise SystemExit(f"M1 native backward proof changed start tick: request={backward_request_tick} confirmed_start={backward_start}")
if strafe_start != strafe_request_tick: raise SystemExit(f"M1 native strafe proof changed start tick: request={strafe_request_tick} confirmed_start={strafe_start}")
if not (walk_tick < backward_request_tick <= backward_tick <= strafe_request_tick <= strafe_tick < request_tick): raise SystemExit(f"M1 native locomotion ordering changed: walk={walk_tick} reverse_request={backward_request_tick} reverse_confirmed={backward_tick} strafe_request={strafe_request_tick} strafe_confirmed={strafe_tick} jump_request={request_tick}")
if backward_duration != backward_tick - backward_request_tick or backward_speed_sq <= 0.0004: raise SystemExit(f"M1 native backward proof is inconsistent: duration={backward_duration} speed_sq={backward_speed_sq}")
if strafe_duration != strafe_tick - strafe_request_tick or strafe_speed_sq <= 0.0004: raise SystemExit(f"M1 native strafe proof is inconsistent: duration={strafe_duration} speed_sq={strafe_speed_sq}")
if not (airborne_start == request_tick == landed_start): raise SystemExit(f"M1 native jump proof changed start tick: request={request_tick} airborne_start={airborne_start} landed_start={landed_start}")
if not (request_tick <= airborne_tick < landed_tick) or delta_y <= 0.0: raise SystemExit(f"M1 native jump arc invalid: request={request_tick} airborne={airborne_tick} landed={landed_tick} delta_y={delta_y}")
if duration != landed_tick - request_tick or duration < 2: raise SystemExit(f"M1 native jump landing duration is inconsistent: duration={duration} ticks={request_tick}->{landed_tick}")
for forbidden_marker in ("GATE_E_PHASE85_CARRY_REPLAY", "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY"):
    if forbidden_marker in text: raise SystemExit(f"M1 native locomotion used compatibility carry recovery: {forbidden_marker}")

continuity_pattern = re.compile(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*local_feet=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)[^\n]*broadphase=(true|false)[^\n]*on_ground=(true|false)[^\n]*baseline_frame=(true|false)")
samples = [(int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), m.group(6)=="true", m.group(7)=="true", m.group(8)=="true") for m in continuity_pattern.finditer(text)]

# Run #567 shows a one-time supported local-Y floor step followed by ten stable ticks. Distinguish
# that geometry transition from continuous sinking by requiring a stable five-tick floor plateau.
floor_window = [s for s in samples if walk_tick <= s[0] < request_tick and s[5] and s[6] and s[7]]
best_floor = []
for i in range(len(floor_window)):
    streak = [floor_window[i]]
    for sample in floor_window[i+1:]:
        previous = streak[-1]
        if sample[0] != previous[0] + 1 or sample[1] != previous[1]: break
        streak.append(sample)
        ys = [s[3] for s in streak]
        if max(ys) - min(ys) > 0.05: break
    ys = [s[3] for s in streak]
    if max(ys) - min(ys) <= 0.05 and len(streak) > len(best_floor): best_floor = streak
if len(best_floor) < 5: raise SystemExit("M1 floor proof missing five consecutive grounded supported samples on a stable carriage-local floor plateau")
floor_y = [s[3] for s in best_floor]; floor_y_span = max(floor_y) - min(floor_y)

frame_pattern = re.compile(r"GATE_E_PHASE171_CARRIAGE_FRAME_STEP[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)[^\n]*frame_step=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)")
frame_speed = {}
for m in frame_pattern.finditer(text):
    key=(int(m.group(1)),int(m.group(2))); speed=math.sqrt(sum(float(m.group(i))**2 for i in range(3,6))); frame_speed[key]=max(frame_speed.get(key,0.0),speed)
speed_change_proof=None; supported=[s for s in samples if s[5] and s[6] and s[7]]
for previous,current in zip(supported,supported[1:]):
    if current[0]!=previous[0]+1 or current[1]!=previous[1]: continue
    local_step=math.dist(previous[2:5],current[2:5]); previous_speed=frame_speed.get((previous[0],previous[1])); current_speed=frame_speed.get((current[0],current[1]))
    if previous_speed is not None and current_speed is not None and local_step<=0.75 and abs(current_speed-previous_speed)>=1.0: speed_change_proof=(previous,current,previous_speed,current_speed,local_step); break
if speed_change_proof is None: raise SystemExit("M1 speed-change stability missing: no consecutive supported bounded-locomotion samples across material carriage speed change")

client_state_pattern = re.compile(r"GATE_E_CLIENT_STATE[^\n]*local_support=local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+);[^\n]*nearby_blocks=([^;]*)")
wall_geometry_seen = any(re.search(r"(?:^|\|)-?\d+, [123], -2(?:\||$)", m.group(4)) for m in client_state_pattern.finditer(text))
if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")
before=[s for s in samples if s[0]==strafe_request_tick-1 and s[5] and s[6] and s[7]]; after_window=[s for s in samples if strafe_request_tick<=s[0]<=strafe_request_tick+7 and s[5] and s[6] and s[7]]
if not before or not after_window: raise SystemExit("M1 wall proof missing supported carriage-local samples around native right-strafe")
# Run #571 proved the right-strafe can coincide with a legitimate Create-authoritative sibling
# handoff: tick 24 rebased 5 -> 7 with native_contact_owner=true, then carriage 7 held the same
# local-z collision boundary for five consecutive supported ticks. Do not require the pre-strafe
# carriage id to survive. Accept a new wall frame only when the exact strafe tick has the existing
# Phase136 identity-only native-contact-owner rebase marker. This changes verifier bookkeeping only.
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
start_z=before[-1][4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)
if start_z-min_z<0.015: raise SystemExit(f"M1 right-strafe did not make material progress toward the carriage side: before_z={start_z} samples={wall_z}")
if min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")
# Run #579 proved the verifier was selecting the final minimum rather than the actual collision
# plateau: ticks 43-49 held exactly z=1.774802 for seven supported samples, then the last sampled
# tick drifted only 0.014 after the strafe pulse. Find a consecutive stable plateau directly,
# while still requiring material progress and retaining the independent no-penetration guard above.
plateau=None
for i in range(len(after)-2):
    candidate=after[i:i+3]
    if candidate[1][0]!=candidate[0][0]+1 or candidate[2][0]!=candidate[1][0]+1: continue
    candidate_z=[s[4] for s in candidate]
    if start_z-min(candidate_z)>=0.015 and max(candidate_z)-min(candidate_z)<=0.005:
        plateau=candidate
        break
if plateau is None: raise SystemExit(f"M1 carriage side stable collision plateau missing: local_z_samples={wall_z}")
impact_z=[s[4] for s in plateau]

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
if len(best_streak)<5:
    detail="none" if not best_streak else f"carriage={best_streak[0][1]} ticks={best_streak[0][0]}-{best_streak[-1][0]} samples={len(best_streak)}"; raise SystemExit("M1 post-landing carriage stability missing: "+detail)

speed_prev,speed_now,speed_before,speed_after,speed_local_step=speed_change_proof
print("M1_NATIVE_LOCOMOTION_PROOF "+f"walk={walk_tick} reverse_request={backward_request_tick} reverse_confirmed={backward_tick} reverse_speed_sq={backward_speed_sq} strafe_request={strafe_request_tick} strafe_confirmed={strafe_tick} strafe_speed_sq={strafe_speed_sq} floor_solid=true floor_samples={len(best_floor)} floor_y_span={floor_y_span:.9f} wall_solid=true wall_local_z_min={min_z:.6f} wall_impact_ticks={plateau[0][0]}-{plateau[-1][0]} wall_impact_span={max(impact_z)-min(impact_z):.9f} speed_change_stable=true speed_change_ticks={speed_prev[0]}-{speed_now[0]} frame_speed={speed_before:.6f}->{speed_after:.6f} speed_change_local_step={speed_local_step:.9f} jump_request={request_tick} airborne={airborne_tick} landed={landed_tick} duration={duration} delta_y={delta_y} natural_fall=true replay_free=true recovery_free=true post_land_stable_samples={len(best_streak)}")
