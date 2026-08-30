#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #291 proves the strict walk start is now valid, but a later tick can
# lose ~1.4 blocks of native carriage carry while the player remains grounded, inside the
# simplified collider, broadphase-overlapping, and actively walking. Phase158 deliberately
# marks that large locomotion drift unhealthy so the existing Phase85 Create-filtered replay
# can recover it. Phase132's previous-native-healthy de-dup still suppresses that replay on
# the exact first loss tick. Bypass only that de-dup condition for this tightly bounded case.
# This does not create a carry vector: Phase85 remains the sole producer and keeps Create's
# collision filtering. No teleport, world/train mutation, or VS2 physics mutation is added.
if "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY" not in source:
    replay_tick_token = "carryReplayPlayerTick != player.tickCount"
    replay_tick_pos = source.find(replay_tick_token)
    if replay_tick_pos < 0 or source.find(replay_tick_token, replay_tick_pos + 1) >= 0:
        raise SystemExit("Phase 161 expected exactly one final Phase85 replay tick predicate")

    replay_if_pos = source.rfind("if (", 0, replay_tick_pos)
    if replay_if_pos < 0:
        raise SystemExit("Phase 161 could not locate final Phase85 replay guard")
    line_start = source.rfind("\n", 0, replay_if_pos) + 1
    replay_indent = source[line_start:replay_if_pos]

    selector = (
        f'{replay_indent}boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}    && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{replay_indent}    && (client.options.keyUp.isDown() || client.options.keyDown.isDown()\n'
        f'{replay_indent}        || client.options.keyLeft.isDown() || client.options.keyRight.isDown())\n'
        f'{replay_indent}    && !Boolean.parseBoolean(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))\n'
        f'{replay_indent}    && Integer.toString(player.tickCount - 1).equals(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthyTick." + carriage.getId()));\n'
        f'{replay_indent}if (phase161SupportedLocomotionNativeLoss) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY carriage_id={{}} player_tick={{}} previous_native_tick={{}} physical_support=true collision_eligible=true broadphase=true grounded=true locomoting=true existing_create_filtered_replay=true bounded_same_tick=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, player.tickCount - 1);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + selector + source[replay_if_pos:]

    # Phase150 and later replay-guard patches may add predicates around the native de-dup
    # expression. Do not require their whole formatting to match byte-for-byte. The stable
    # semantic seam owned by Phase132 is the final phase133ReplayGrace escape hatch inside
    # this one, already-identified Phase85 guard. Widen only that tail, and require it once.
    replay_tick_pos = source.find(replay_tick_token, replay_if_pos + len(selector))
    replay_if_pos = source.rfind("if (", 0, replay_tick_pos)
    guard_segment = source[replay_if_pos:replay_tick_pos]
    grace_tail = "|| phase133ReplayGrace)"
    widened_tail = "|| phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"
    if guard_segment.count(grace_tail) != 1:
        raise SystemExit(
            "Phase 161 expected exactly one Phase133 replay-grace tail in the final Phase85 guard"
        )
    guard_segment = guard_segment.replace(grace_tail, widened_tail, 1)
    source = source[:replay_if_pos] + guard_segment + source[replay_tick_pos:]

required = [
    "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY",
    "phase161SupportedLocomotionNativeLoss",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()",
    "client.options.keyUp.isDown()",
    "client.options.keyDown.isDown()",
    "client.options.keyLeft.isDown()",
    "client.options.keyRight.isDown()",
    "!Boolean.parseBoolean(System.getProperty(",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "|| phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)",
    "existing_create_filtered_replay=true",
    "bounded_same_tick=true",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 161 lost supported-locomotion recovery anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in selector or forbidden in widened_tail:
        raise SystemExit("Phase 161 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 161: lets the existing Create-filtered replay recover the first strictly-supported locomotion native-carry loss tick")
