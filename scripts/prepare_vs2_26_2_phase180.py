#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #357 showed that the bounded walk stays carriage-local stable while the
# existing Create-computed/collision-filtered recovery replay runs, then starts drifting when
# native contact application remains absent and continuity eligibility expires. Phase179 already
# makes native health tick-fresh. Extend only that existing continuity rule during the bounded
# disposable walk, and only when the immediately previous tick actually replayed and this tick has
# no native Create application. Do not depend on cumulative predicate whitespace/order: later
# phases have legitimately reshaped the declaration several times.

inserted = ""
if "GATE_E_PHASE180_CONSECUTIVE_NATIVE_LOSS_RECOVERY" not in source:
    decl_token = "boolean phase161SupportedLocomotionNativeLoss ="
    decl_pos = source.find(decl_token)
    if decl_pos < 0:
        raise SystemExit("Phase 180 could not locate Phase161 supported-loss declaration")
    decl_end = source.find(";", decl_pos)
    if decl_end < 0:
        raise SystemExit("Phase 180 could not bound Phase161 supported-loss declaration")
    predicate = source[decl_pos:decl_end + 1]

    healthy_clause = '''Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))'''
    if predicate.count(healthy_clause) != 1:
        raise SystemExit(
            "Phase 180 expected exactly one previous-native healthy-tick continuity clause inside Phase161 predicate, found "
            + str(predicate.count(healthy_clause)))

    continuity_clause = '''(Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
                || (phase161FixtureWalkWindow
                    && carryReplayPlayerTick == player.tickCount - 1
                    && !Integer.toString(player.tickCount).equals(System.getProperty(
                        "vs2.phase170NativeContactApplicationTick"))))'''
    predicate = predicate.replace(healthy_clause, continuity_clause, 1)
    source = source[:decl_pos] + predicate + source[decl_end + 1:]
    inserted += continuity_clause

    marker = "if (phase161SupportedLocomotionNativeLoss) {"
    marker_pos = source.find(marker, decl_pos)
    if marker_pos < 0:
        raise SystemExit("Phase 180 could not locate Phase161 recovery publication")
    line_start = source.rfind("\n", 0, marker_pos) + 1
    indent = source[line_start:marker_pos]
    log = (
        f'{indent}if (phase161SupportedLocomotionNativeLoss && phase161FixtureWalkWindow\n'
        f'{indent}        && carryReplayPlayerTick == player.tickCount - 1\n'
        f'{indent}        && !Integer.toString(player.tickCount).equals(System.getProperty(\n'
        f'{indent}            "vs2.phase170NativeContactApplicationTick"))) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE180_CONSECUTIVE_NATIVE_LOSS_RECOVERY carriage_id={{}} player_tick={{}} previous_replay_tick={{}} strict_support=true same_tick_native_application=false existing_create_filtered_replay=true fixture_only=true bounded_continuity=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, carryReplayPlayerTick);\n'
        f'{indent}}}\n'
    )
    source = source[:line_start] + log + source[line_start:]
    inserted += log

required = [
    "GATE_E_PHASE180_CONSECUTIVE_NATIVE_LOSS_RECOVERY",
    "phase161SupportedLocomotionNativeLoss",
    "phase161FixtureWalkWindow",
    "carryReplayPlayerTick == player.tickCount - 1",
    "vs2.phase170NativeContactApplicationTick",
    "phase179ActiveContactMotionAvailable",
    "!phase179CurrentNativeHealthy",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "existing_create_filtered_replay=true",
    "fixture_only=true",
    "bounded_continuity=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 180 lost bounded consecutive native-loss recovery anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 180 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 180: structurally extends existing Create-filtered fixture recovery across consecutive native-loss walk ticks")
