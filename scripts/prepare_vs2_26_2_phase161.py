#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #295 distinguished under-carry from over-carry, but #296 exposed a
# preparation-scope bug: Phase161 inserted its selector at the Phase85 replay site while
# referring directly to Phase137 native-balance locals, which are scoped to an earlier
# block. Publish the already-computed balance as read-only System properties at the
# measurement site, then consume only the same-tick measurement at the replay site.
# Production-world #353 then proved the single-pulse walk fixture can lose native carry
# after the key has already been released: tick 23 retained strict support and material
# under-carry while key_up=false, so the old key-down-only locomotion predicate prevented
# the existing Create-filtered recovery from running. Treat the bounded fixture walk
# observation window as locomotion eligibility even after pulse release; all support,
# under-carry, native-health and de-dup guards remain authoritative. This changes recovery
# eligibility accounting only: Phase85 remains the sole producer of Create-computed/
# collision-filtered carry and no player/train/world/VS2 physics mutation is introduced.

measurement_marker = '''double phase134DriftZ = phase134NativePlayerDz - phase134CarriageDz;\n'''
measurement_publish = ""
if "vs2.phase161CarriageMotionSq." not in source:
    if source.count(measurement_marker) != 1:
        raise SystemExit("Phase 161 expected exactly one Phase137 native-balance measurement site")
    measurement_publish = measurement_marker + '''double phase161PublishedCarriageMotionSq = phase134CarriageDx * phase134CarriageDx
    + phase134CarriageDy * phase134CarriageDy + phase134CarriageDz * phase134CarriageDz;
double phase161PublishedNativeProjection = phase134NativePlayerDx * phase134CarriageDx
    + phase134NativePlayerDy * phase134CarriageDy + phase134NativePlayerDz * phase134CarriageDz;
System.setProperty("vs2.phase161CarriageMotionSq." + carriage.getId(), Double.toString(phase161PublishedCarriageMotionSq));
System.setProperty("vs2.phase161NativeProjection." + carriage.getId(), Double.toString(phase161PublishedNativeProjection));
System.setProperty("vs2.phase161MeasurementTick." + carriage.getId(), Integer.toString(player.tickCount));
'''
    source = source.replace(measurement_marker, measurement_publish, 1)

selector = ""
widened = ""
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
        f'{replay_indent}double phase161CarriageMotionSq = Double.parseDouble(System.getProperty(\n'
        f'{replay_indent}    "vs2.phase161CarriageMotionSq." + carriage.getId(), "NaN"));\n'
        f'{replay_indent}double phase161NativeCarryProjection = Double.parseDouble(System.getProperty(\n'
        f'{replay_indent}    "vs2.phase161NativeProjection." + carriage.getId(), "NaN"));\n'
        f'{replay_indent}boolean phase161CurrentMeasurement = Integer.toString(player.tickCount).equals(System.getProperty(\n'
        f'{replay_indent}    "vs2.phase161MeasurementTick." + carriage.getId()));\n'
        f'{replay_indent}boolean phase161MeasuredUndercarry = phase161CurrentMeasurement\n'
        f'{replay_indent}    && Double.isFinite(phase161CarriageMotionSq) && Double.isFinite(phase161NativeCarryProjection)\n'
        f'{replay_indent}    && phase161CarriageMotionSq > 1.0E-8\n'
        f'{replay_indent}    && phase161NativeCarryProjection < phase161CarriageMotionSq - 0.01;\n'
        f'{replay_indent}boolean phase161FixtureWalkWindow = productionSmokeFixture\n'
        f'{replay_indent}    && phase154WalkStarted && !phase154WalkFinished;\n'
        f'{replay_indent}boolean phase161LocomotionWindow = phase161FixtureWalkWindow\n'
        f'{replay_indent}    || client.options.keyUp.isDown() || client.options.keyDown.isDown()\n'
        f'{replay_indent}    || client.options.keyLeft.isDown() || client.options.keyRight.isDown();\n'
        f'{replay_indent}boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}    && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{replay_indent}    && phase161LocomotionWindow\n'
        f'{replay_indent}    && !Boolean.parseBoolean(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))\n'
        f'{replay_indent}    && Integer.toString(player.tickCount - 1).equals(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))\n'
        f'{replay_indent}    && phase161MeasuredUndercarry;\n'
        f'{replay_indent}if (productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}        && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}        && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{replay_indent}        && phase161LocomotionWindow\n'
        f'{replay_indent}        && !Boolean.parseBoolean(System.getProperty(\n'
        f'{replay_indent}            "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE161_LOCOMOTION_NATIVE_LOSS_CLASSIFICATION carriage_id={{}} player_tick={{}} carriage_motion_sq={{}} native_projection={{}} current_measurement={{}} measured_undercarry={{}} locomotion_window=true fixture_walk_window={{}} read_only_accounting=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, phase161CarriageMotionSq, phase161NativeCarryProjection, phase161CurrentMeasurement, phase161MeasuredUndercarry, phase161FixtureWalkWindow);\n'
        f'{replay_indent}}}\n'
        f'{replay_indent}if (phase161SupportedLocomotionNativeLoss) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY carriage_id={{}} player_tick={{}} previous_native_tick={{}} physical_support=true collision_eligible=true broadphase=true grounded=true locomotion_window=true fixture_walk_window={{}} measured_undercarry=true existing_create_filtered_replay=true bounded_same_tick=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, player.tickCount - 1, phase161FixtureWalkWindow);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + selector + source[replay_if_pos:]

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
    "vs2.phase161CarriageMotionSq.",
    "vs2.phase161NativeProjection.",
    "vs2.phase161MeasurementTick.",
    "phase161PublishedCarriageMotionSq",
    "phase161PublishedNativeProjection",
    "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY",
    "GATE_E_PHASE161_LOCOMOTION_NATIVE_LOSS_CLASSIFICATION",
    "phase161SupportedLocomotionNativeLoss",
    "phase161MeasuredUndercarry",
    "phase161CurrentMeasurement",
    "phase161NativeCarryProjection < phase161CarriageMotionSq - 0.01",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()",
    "phase161FixtureWalkWindow",
    "phase161LocomotionWindow",
    "productionSmokeFixture",
    "phase154WalkStarted && !phase154WalkFinished",
    "client.options.keyUp.isDown()",
    "client.options.keyDown.isDown()",
    "client.options.keyLeft.isDown()",
    "client.options.keyRight.isDown()",
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
    raise SystemExit("Phase 161 lost scoped under-carry recovery anchors: " + ", ".join(missing))

# Audit only text this phase itself can insert. Scanning the cumulative source produced a
# false positive on historical fixture-only player.setPos code from earlier phases.
phase161_inserted = measurement_publish + selector + widened
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in phase161_inserted:
        raise SystemExit("Phase 161 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 161: keeps Create-filtered recovery eligible through the bounded fixture walk window after the one-tick input pulse ends")
