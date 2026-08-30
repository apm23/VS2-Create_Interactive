#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #291 proves the strict walk start is now valid, but a later tick can
# lose ~1.4 blocks of native carriage carry while the player remains grounded, inside the
# simplified collider, broadphase-overlapping, and actively walking. Phase158 deliberately
# marks that large locomotion drift unhealthy so the existing Phase85 Create-filtered replay
# can recover it. The native-health de-dup still suppresses that replay on the exact first
# loss tick. Bypass only that de-dup condition for this tightly bounded case.
#
# Production-world #295 then exposed the opposite case: at tick 28 the player had already
# moved 14.406 blocks while carriage 5 moved only 6.207 blocks. The previous Phase161 test
# treated every large unhealthy locomotion sample as native carry *loss* and replayed another
# 6.207 blocks, even though this sample was an over-carry/overshoot. Require measured
# under-carry along the carriage-motion vector before bypassing de-dup. This only decides
# whether the existing Create-filtered replay is allowed; it creates no vector and changes no
# VS2 physics, collision response, train control, teleport, or world state.
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
        f'{replay_indent}double phase161CarriageMotionSq = phase134CarriageDx * phase134CarriageDx\n'
        f'{replay_indent}    + phase134CarriageDy * phase134CarriageDy + phase134CarriageDz * phase134CarriageDz;\n'
        f'{replay_indent}double phase161NativeCarryProjection = phase134NativePlayerDx * phase134CarriageDx\n'
        f'{replay_indent}    + phase134NativePlayerDy * phase134CarriageDy + phase134NativePlayerDz * phase134CarriageDz;\n'
        f'{replay_indent}boolean phase161MeasuredUndercarry = phase161CarriageMotionSq > 1.0E-8\n'
        f'{replay_indent}    && phase161NativeCarryProjection < phase161CarriageMotionSq - 0.01;\n'
        f'{replay_indent}boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}    && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{replay_indent}    && (client.options.keyUp.isDown() || client.options.keyDown.isDown()\n'
        f'{replay_indent}        || client.options.keyLeft.isDown() || client.options.keyRight.isDown())\n'
        f'{replay_indent}    && !Boolean.parseBoolean(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))\n'
        f'{replay_indent}    && Integer.toString(player.tickCount - 1).equals(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))\n'
        f'{replay_indent}    && phase161MeasuredUndercarry;\n'
        f'{replay_indent}if (productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}        && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}        && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{replay_indent}        && (client.options.keyUp.isDown() || client.options.keyDown.isDown()\n'
        f'{replay_indent}            || client.options.keyLeft.isDown() || client.options.keyRight.isDown())\n'
        f'{replay_indent}        && !Boolean.parseBoolean(System.getProperty(\n'
        f'{replay_indent}            "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE161_LOCOMOTION_NATIVE_LOSS_CLASSIFICATION carriage_id={{}} player_tick={{}} carriage_motion_sq={{}} native_projection={{}} measured_undercarry={{}} read_only_accounting=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, phase161CarriageMotionSq, phase161NativeCarryProjection, phase161MeasuredUndercarry);\n'
        f'{replay_indent}}}\n'
        f'{replay_indent}if (phase161SupportedLocomotionNativeLoss) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY carriage_id={{}} player_tick={{}} previous_native_tick={{}} physical_support=true collision_eligible=true broadphase=true grounded=true locomoting=true measured_undercarry=true existing_create_filtered_replay=true bounded_same_tick=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, player.tickCount - 1);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + selector + source[replay_if_pos:]

    # The cumulative chain can reach this phase with the Phase137, Phase150, or Phase132
    # shape of the same native-health de-dup guard, depending on which recursive preparation
    # path invoked it. Support those known semantic forms explicitly instead of depending on
    # one later phase's formatting. Only the native de-dup term is widened; all surrounding
    # Phase85 support/collision/rebase/tick predicates remain untouched.
    replay_tick_pos = source.find(replay_tick_token, replay_if_pos + len(selector))
    replay_if_pos = source.rfind("if (", 0, replay_tick_pos)
    guard_segment = source[replay_if_pos:replay_tick_pos]

    phase137 = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))))'''
    phase150 = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
                                || phase150SupportReacquired))'''
    phase132 = '''(!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
                                || phase150SupportReacquired)) || phase133ReplayGrace)'''

    matched = None
    for candidate in (phase132, phase150, phase137):
        if candidate in guard_segment:
            if matched is not None:
                raise SystemExit("Phase 161 found multiple native de-dup guard variants")
            matched = candidate
    if matched is None:
        raise SystemExit("Phase 161 could not find a known native carry de-dup guard variant")

    widened = f'({matched} || phase161SupportedLocomotionNativeLoss)'
    guard_segment = guard_segment.replace(matched, widened, 1)
    source = source[:replay_if_pos] + guard_segment + source[replay_tick_pos:]

required = [
    "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY",
    "GATE_E_PHASE161_LOCOMOTION_NATIVE_LOSS_CLASSIFICATION",
    "phase161SupportedLocomotionNativeLoss",
    "phase161MeasuredUndercarry",
    "phase161CarriageMotionSq",
    "phase161NativeCarryProjection",
    "phase134NativePlayerDx * phase134CarriageDx",
    "phase161NativeCarryProjection < phase161CarriageMotionSq - 0.01",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()",
    "client.options.keyUp.isDown()",
    "client.options.keyDown.isDown()",
    "client.options.keyLeft.isDown()",
    "client.options.keyRight.isDown()",
    "!Boolean.parseBoolean(System.getProperty(",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "&& phase161MeasuredUndercarry",
    "|| phase161SupportedLocomotionNativeLoss)",
    "measured_undercarry=true",
    "existing_create_filtered_replay=true",
    "bounded_same_tick=true",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 161 lost supported-locomotion under-carry recovery anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in selector or forbidden in widened:
        raise SystemExit("Phase 161 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 161: gates existing Create-filtered locomotion recovery replay to measured native under-carry and rejects over-carry overshoot")
