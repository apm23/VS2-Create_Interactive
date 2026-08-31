#!/usr/bin/env python3
"""Validate native sprint, reverse, lateral strafe, and jump/fall proof from the real production-world smoke log.

This is a CI artifact verifier, not a VS2 source preparation phase. Its filename intentionally
matches the production-world workflow path trigger so changes to this proof contract rerun the
real train fixture.
"""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_vs2_26_2_m1_jump_proof.py <production-world-smoke.log>")

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")

walk = re.search(
    r"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*on_ground=true[^\n]*broadphase=true"
    r"[^\n]*support_healthy=true[^\n]*confirmed=true[^\n]*sprinting=true[^\n]*fixture_only=true",
    text,
)
backward_requested = re.search(
    r"GATE_E_M1_NATIVE_BACKWARD_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true"
    r"[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true",
    text,
)
backward_confirmed = re.search(
    r"GATE_E_M1_NATIVE_BACKWARD_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)"
    r"[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true"
    r"[^\n]*vanilla_keymapping=true[^\n]*native_motion=true",
    text,
)
strafe_requested = re.search(
    r"GATE_E_M1_NATIVE_STRAFE_REQUESTED[^\n]*player_tick=(\d+)[^\n]*fixture_only=true"
    r"[^\n]*vanilla_keymapping=true[^\n]*direction=right",
    text,
)
strafe_confirmed = re.search(
    r"GATE_E_M1_NATIVE_STRAFE_CONFIRMED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*duration_ticks=(\d+)[^\n]*horizontal_speed_sq=([-+0-9.eE]+)"
    r"[^\n]*grounding_deferred_to_create_contact=true[^\n]*fixture_only=true"
    r"[^\n]*vanilla_keymapping=true[^\n]*native_motion=true[^\n]*direction=right",
    text,
)
requested = re.search(
    r"GATE_E_M1_NATIVE_JUMP_REQUESTED[^\n]*player_tick=(\d+)[^\n]*on_ground=true"
    r"[^\n]*fixture_only=true[^\n]*vanilla_keymapping=true",
    text,
)
airborne = re.search(
    r"GATE_E_M1_NATIVE_JUMP_AIRBORNE[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*delta_y=([-+0-9.eE]+)[^\n]*on_ground=(?:true|false)[^\n]*fixture_only=true"
    r"[^\n]*native_motion=true[^\n]*vertical_arc=true",
    text,
)
landed = re.search(
    r"GATE_E_M1_NATIVE_JUMP_LANDED[^\n]*player_tick=(\d+)[^\n]*start_tick=(\d+)"
    r"[^\n]*duration_ticks=(\d+)[^\n]*on_ground=true[^\n]*fixture_only=true"
    r"[^\n]*natural_fall=true",
    text,
)

missing = [
    name
    for name, match in (
        ("supported sprint/walk", walk),
        ("native backward request", backward_requested),
        ("native grounded backward confirmation", backward_confirmed),
        ("native right-strafe request", strafe_requested),
        ("native right-strafe confirmation", strafe_confirmed),
        ("native jump request", requested),
        ("native airborne transition", airborne),
        ("natural landing", landed),
    )
    if match is None
]
if missing:
    raise SystemExit("M1 native locomotion proof missing: " + ", ".join(missing))

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
    raise SystemExit(
        f"M1 native backward proof changed start tick: request={backward_request_tick} "
        f"confirmed_start={backward_start}"
    )
if strafe_start != strafe_request_tick:
    raise SystemExit(
        f"M1 native strafe proof changed start tick: request={strafe_request_tick} "
        f"confirmed_start={strafe_start}"
    )
if not (walk_tick < backward_request_tick <= backward_tick <= strafe_request_tick <= strafe_tick < request_tick):
    raise SystemExit(
        f"M1 native locomotion ordering changed: walk={walk_tick} reverse_request={backward_request_tick} "
        f"reverse_confirmed={backward_tick} strafe_request={strafe_request_tick} "
        f"strafe_confirmed={strafe_tick} jump_request={request_tick}"
    )
if backward_duration != backward_tick - backward_request_tick or backward_speed_sq <= 0.0004:
    raise SystemExit(
        f"M1 native backward proof is inconsistent: duration={backward_duration} "
        f"ticks={backward_request_tick}->{backward_tick} speed_sq={backward_speed_sq}"
    )
if strafe_duration != strafe_tick - strafe_request_tick or strafe_speed_sq <= 0.0004:
    raise SystemExit(
        f"M1 native strafe proof is inconsistent: duration={strafe_duration} "
        f"ticks={strafe_request_tick}->{strafe_tick} speed_sq={strafe_speed_sq}"
    )

if not (airborne_start == request_tick == landed_start):
    raise SystemExit(
        f"M1 native jump proof changed start tick: request={request_tick} "
        f"airborne_start={airborne_start} landed_start={landed_start}"
    )
# Create can publish moving-contraption ground contact later in the same tick than LocalPlayer's
# native jump arc. The proof therefore keys on positive vanilla vertical motion, not an intermediate
# onGround flag, and still requires a strictly later natural landing.
if not (request_tick <= airborne_tick < landed_tick):
    raise SystemExit(
        f"M1 native jump transitions are out of order: request={request_tick} "
        f"airborne={airborne_tick} landed={landed_tick}"
    )
if delta_y <= 0.0:
    raise SystemExit(f"M1 native jump never gained upward motion: delta_y={delta_y}")
if duration != landed_tick - request_tick or duration < 2:
    raise SystemExit(
        f"M1 native jump landing duration is inconsistent: duration={duration} "
        f"ticks={request_tick}->{landed_tick}"
    )

# M1 is only accepted when the real production smoke completes without any compatibility carry
# recovery path. Native Create/VS2 contact must own locomotion end-to-end; this verifier changes
# no player position, velocity, collision response, train state, or physics behavior.
for forbidden_marker in (
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY",
):
    if forbidden_marker in text:
        raise SystemExit(f"M1 native locomotion used compatibility carry recovery: {forbidden_marker}")

print(
    "M1_NATIVE_LOCOMOTION_PROOF "
    f"walk={walk_tick} reverse_request={backward_request_tick} reverse_confirmed={backward_tick} "
    f"reverse_speed_sq={backward_speed_sq} strafe_request={strafe_request_tick} "
    f"strafe_confirmed={strafe_tick} strafe_speed_sq={strafe_speed_sq} "
    f"jump_request={request_tick} airborne={airborne_tick} landed={landed_tick} "
    f"duration={duration} delta_y={delta_y} natural_fall=true replay_free=true recovery_free=true"
)
