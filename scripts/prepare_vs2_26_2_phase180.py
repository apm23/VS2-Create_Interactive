#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #357 proves the bounded walk stays carriage-local stable while the existing
# Create-computed/collision-filtered recovery replay runs at ticks 21-22. Native Create contact
# application stopped after tick 20; once the previous-native-health-only continuity guard stopped
# recovery, the very next observed sample began drifting by exactly the carriage frame step.
# Preserve the same strict support/collision/grounded guards and the existing Phase85 replay vector,
# but allow a consecutive fixture-walk native-loss tick to inherit eligibility from a replay that
# actually ran on the immediately preceding tick. A same-tick native Create application still wins.
# This is bounded smoke-fixture recovery continuity only; it adds no new movement/vector/physics path.

old = '''&& Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
            && (phase161MeasuredUndercarry || (phase170FixtureWalkRecoveryWindow && phase179ActiveContactMotionAvailable))'''
new = '''&& (Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
                || (phase161FixtureWalkWindow
                    && carryReplayPlayerTick == player.tickCount - 1
                    && !Integer.toString(player.tickCount).equals(System.getProperty(
                        "vs2.phase170NativeContactApplicationTick"))))
            && (phase161MeasuredUndercarry || (phase170FixtureWalkRecoveryWindow && phase179ActiveContactMotionAvailable))'''

inserted = ""
if "GATE_E_PHASE180_CONSECUTIVE_NATIVE_LOSS_RECOVERY" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 180 expected exactly one Phase179 previous-native continuity clause, found {count}")
    source = source.replace(old, new, 1)
    inserted = new

    marker = "if (phase161SupportedLocomotionNativeLoss) {"
    marker_pos = source.find(marker)
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
print("Phase 180: keeps existing Create-filtered fixture recovery continuous across consecutive native-loss walk ticks")
