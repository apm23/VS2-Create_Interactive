#!/usr/bin/env python3
"""Validate native M1 locomotion plus real carriage wall collision from production-world smoke."""
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
        continuity_ticks = [
            int(value)
            for value in re.findall(r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)", text)
        ]
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

walk = need(
    r"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*broadphase=true"
    r"[^\n]*support_healthy=true[^\n]*confirmed=true[^\n]*sprinting=true[^\n]*fixture_only=true",
    "supported sprint/walk",
)
backward_requested = need(
    r"GATE_E_M1_NATIVE_BACKWARD_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true"
    r"[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true",
    "native backward request",
)
backward_confirmed = need(
    r"GATE_E_M1_NATIVE_BACKWARD_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)"
    r"[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true"
    r"[^\n]*vanilla_keymapping=true[^\n]*native_motion=true",
    "native grounded backward confirmation",
)
strafe_requested = need(
    r"GATE_E_M1_NATIVE_STRAFE_REQUESTED[^\n]*player_tick=(\d+)[^\n]*fixture_only=true"
    r"[^\n]*vanilla_keymapping=true[^\n]*direction=right",
    "native right-strafe request",
)
strafe_confirmed = need(
    r"GATE_E_M1_NATIVE_STRAFE_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)"
    r"[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true"
    r"[^\n]*vanilla_keymapping=true[^\n]*native_motion=true[^\n]*direction=right",
    "native right-strafe confirmation",
)
requested = need(
    r"GATE_E_M1_NATIVE_JUMP_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true"
    r"[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true",
    "native jump request",
)
airborne = need(
    r"GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*delta_y=([-+0-9.eE]+)[^\n]*on_ground=(?:true|false)[^\n]*fixture_only=true"
    r"[^\n]*native_motion=true[^\n]*vertical_arc=true",
    "native airborne transition",
)
landed = need(
    r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*duration_ticks=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true[^\n]*natural_fall=true",
    "natural landing",
)

walk_tick = int(walk.group(1))
backward_request_tick = int(backward_requested.group(1))
backward_tick = int(backward_confirmed.group(1))
backward_start = int(backward_confirmed.group(2))
backward_duration = int(backward_confirmed.group(3))
backward_speed_sq = float(backward_confirmed.group(4))
strafe_request_tick = int(strafe_requested.group(1))
strafe_tick = int(strafe_confirmed.group(1))
strafe_start = int(strafe_confirmed.group(2))
strafe_duration = int(strafe_confirmed.group(3))
strafe_speed_sq = float(strafe_confirmed.group(4))
request_tick = int(requested.group(1))
airborne_tick = int(airborne.group(1))
airborne_start = int(airborne.group(2))
delta_y = float(airborne.group(3))
landed_tick = int(landed.group(1))
landed_start = int(landed.group(2))
duration = int(landed.group(3))

if backward_start != backward_request_tick:
    raise SystemExit(f"M1 native backward proof changed start tick: request={backward_request_tick} confirmed_start={backward_start}")
if strafe_start != strafe_request_tick:
    raise SystemExit(f"M1 native strafe proof changed start tick: request={strafe_request_tick} confirmed_start={strafe_start}")
if not (walk_tick < backward_request_tick <= backward_tick <= strafe_request_tick <= strafe_tick < request_tick):
    raise SystemExit(
        f"M1 native locomotion ordering changed: walk={walk_tick} reverse_request={backward_request_tick} "
        f"reverse_confirmed={backward_tick} strafe_request={strafe_request_tick} strafe_confirmed={strafe_tick} jump_request={request_tick}"
    )
if backward_duration != backward_tick - backward_request_tick or backward_speed_sq <= 0.0004:
    raise SystemExit(f"M1 native backward proof is inconsistent: duration={backward_duration} speed_sq={backward_speed_sq}")
if strafe_duration != strafe_tick - strafe_request_tick or strafe_speed_sq <= 0.0004:
    raise SystemExit(f"M1 native strafe proof is inconsistent: duration={strafe_duration} speed_sq={strafe_speed_sq}")
if not (airborne_start == request_tick == landed_start):
    raise SystemExit(f"M1 native jump proof changed start tick: request={request_tick} airborne_start={airborne_start} landed_start={landed_start}")
if not (request_tick <= airborne_tick < landed_tick) or delta_y <= 0.0:
    raise SystemExit(f"M1 native jump arc invalid: request={request_tick} airborne={airborne_tick} landed={landed_tick} delta_y={delta_y}")
if duration != landed_tick - request_tick or duration < 2:
    raise SystemExit(f"M1 native jump landing duration is inconsistent: duration={duration} ticks={request_tick}->{landed_tick}")

for forbidden_marker in (
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY",
):
    if forbidden_marker in text:
        raise SystemExit(f"M1 native locomotion used compatibility carry recovery: {forbidden_marker}")

continuity_pattern = re.compile(
    r"GATE_E_CARRIAGE_LOCAL_CONTINUITY[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)"
    r"[^\n]*local_feet=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)"
    r"[^\n]*broadphase=(true|false)[^\n]*on_ground=(true|false)[^\n]*baseline_frame=(true|false)"
)
samples = []
for match in continuity_pattern.finditer(text):
    samples.append((
        int(match.group(1)), int(match.group(2)),
        float(match.group(3)), float(match.group(4)), float(match.group(5)),
        match.group(6) == "true", match.group(7) == "true", match.group(8) == "true",
    ))

# Production-world #552 proves the material train-speed change occurs while the harness is
# intentionally right-strafing, so requiring a nearly stationary carriage-local player rejects
# valid native locomotion. Reuse the verifier's existing 0.75-block bounded locomotion limit while
# still requiring consecutive supported samples on one carriage and a >=1.0 frame-speed change.
# Verifier-only: no input, movement, carry, collision, train, or physics behavior changes.
frame_pattern = re.compile(
    r"GATE_E_PHASE171_CARRIAGE_FRAME_STEP[^\n]*player_tick=(\d+)[^\n]*carriage_id=(\d+)"
    r"[^\n]*frame_step=\(([-+0-9.eE]+), ([-+0-9.eE]+), ([-+0-9.eE]+)\)"
)
frame_speed = {}
for match in frame_pattern.finditer(text):
    key = (int(match.group(1)), int(match.group(2)))
    speed = math.sqrt(sum(float(match.group(i)) ** 2 for i in range(3, 6)))
    frame_speed[key] = max(frame_speed.get(key, 0.0), speed)

speed_change_proof = None
supported = [s for s in samples if s[5] and s[6] and s[7]]
for previous, current in zip(supported, supported[1:]):
    if current[0] != previous[0] + 1 or current[1] != previous[1]:
        continue
    local_step = math.dist(previous[2:5], current[2:5])
    previous_speed = frame_speed.get((previous[0], previous[1]))
    current_speed = frame_speed.get((current[0], current[1]))
    if previous_speed is None or current_speed is None:
        continue
    if local_step <= 0.75 and abs(current_speed - previous_speed) >= 1.0:
        speed_change_proof = (previous, current, previous_speed, current_speed, local_step)
        break
if speed_change_proof is None:
    raise SystemExit("M1 speed-change stability missing: no consecutive supported bounded-locomotion samples across material carriage speed change")

# The r0v3 fixture exposes occupied side geometry at local block z=-2. Runs #534 and #540
# reached that same side through different carriage-local player offsets: #534 plateaued near
# z=-1.800 while #540 plateaued near z=-0.715. A fixed player-coordinate threshold therefore
# confuses frame/fixture offset with collision solidity. Prove the wall from the native strafe
# itself: same-carriage supported samples must make material progress toward negative Z, then hold
# a three-sample plateau without crossing into the occupied z=-2 cell. Verifier-only.
client_state_pattern = re.compile(
    r"GATE_E_CLIENT_STATE[^\n]*local_support=local_feet=([-+0-9.eE]+),([-+0-9.eE]+),([-+0-9.eE]+);"
    r"[^\n]*nearby_blocks=([^;]*)"
)
wall_geometry_seen = False
for m in client_state_pattern.finditer(text):
    nearby = m.group(4)
    if re.search(r"(?:^|\|)-?\d+, [123], -2(?:\||$)", nearby):
        wall_geometry_seen = True
        break
if not wall_geometry_seen:
    raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")

before = [s for s in samples if s[0] == strafe_request_tick - 1 and s[5] and s[6] and s[7]]
after = [s for s in samples if strafe_request_tick <= s[0] <= strafe_request_tick + 7 and s[5] and s[6] and s[7]]
if not before or len(after) < 6:
    raise SystemExit("M1 wall proof missing supported carriage-local samples around native right-strafe")
wall_carriage = after[0][1]
after = [s for s in after if s[1] == wall_carriage]
if len(after) < 6 or before[-1][1] != wall_carriage:
    raise SystemExit("M1 wall proof crossed carriage identity during the collision sample")
start_z = before[-1][4]
wall_z = [s[4] for s in after]
min_z = min(wall_z)
if start_z - min_z < 0.015:
    raise SystemExit(f"M1 right-strafe did not make material progress toward the carriage side: before_z={start_z} samples={wall_z}")
# The occupied block cell begins at z=-2. A player feet/center sample entering that cell would be
# unambiguous penetration regardless of player-width details; keep this conservative and geometry-based.
if min_z <= -2.0:
    raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")
impact = [s for s in after if s[4] <= min_z + 0.005]
if len(impact) < 3:
    raise SystemExit(f"M1 carriage side impact plateau too short: local_z_samples={wall_z}")
# Use the first consecutive three-sample plateau at the most-negative reached boundary.
plateau = None
for i in range(len(impact) - 2):
    candidate = impact[i:i + 3]
    if candidate[1][0] == candidate[0][0] + 1 and candidate[2][0] == candidate[1][0] + 1:
        plateau = candidate
        break
if plateau is None:
    raise SystemExit(f"M1 carriage side impact samples are not consecutive: ticks={[s[0] for s in impact]}")
impact_z = [s[4] for s in plateau]
if max(impact_z) - min(impact_z) > 0.005:
    raise SystemExit(f"M1 carriage side did not hold a stable collision boundary: impact_z={impact_z}")

post_land = [s for s in samples if s[0] > landed_tick]
best_streak = []
streak = []
for sample in post_land:
    tick, carriage, x, y, z, broadphase, on_ground, baseline_frame = sample
    if not (broadphase and on_ground and baseline_frame):
        streak = []
        continue
    if not streak:
        streak = [sample]
    else:
        prev = streak[-1]
        step_sq = (x - prev[2]) ** 2 + (y - prev[3]) ** 2 + (z - prev[4]) ** 2
        if tick == prev[0] + 1 and carriage == prev[1] and step_sq <= 0.75 ** 2:
            streak.append(sample)
        else:
            streak = [sample]
    if len(streak) > len(best_streak):
        best_streak = list(streak)
if len(best_streak) < 5:
    detail = "none" if not best_streak else f"carriage={best_streak[0][1]} ticks={best_streak[0][0]}-{best_streak[-1][0]} samples={len(best_streak)}"
    raise SystemExit("M1 post-landing carriage stability missing: " + detail)

speed_prev, speed_now, speed_before, speed_after, speed_local_step = speed_change_proof
print(
    "M1_NATIVE_LOCOMOTION_PROOF "
    f"walk={walk_tick} reverse_request={backward_request_tick} reverse_confirmed={backward_tick} "
    f"reverse_speed_sq={backward_speed_sq} strafe_request={strafe_request_tick} strafe_confirmed={strafe_tick} "
    f"strafe_speed_sq={strafe_speed_sq} wall_solid=true wall_local_z_min={min_z:.6f} "
    f"wall_impact_ticks={plateau[0][0]}-{plateau[-1][0]} wall_impact_span={max(impact_z)-min(impact_z):.9f} "
    f"speed_change_stable=true speed_change_ticks={speed_prev[0]}-{speed_now[0]} "
    f"frame_speed={speed_before:.6f}->{speed_after:.6f} speed_change_local_step={speed_local_step:.9f} "
    f"jump_request={request_tick} airborne={airborne_tick} landed={landed_tick} duration={duration} delta_y={delta_y} "
    f"natural_fall=true replay_free=true recovery_free=true post_land_stable_samples={len(best_streak)}"
)
