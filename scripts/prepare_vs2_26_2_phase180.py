#!/usr/bin/env python3
from pathlib import Path
import re
import runpy

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
#
# Production-world #361 then proved the real carriage stays grounded, broadphase-overlapping, and
# strict-physical-support healthy through the bounded acquisition window, while Phase154 never
# emits WALK_START. Expose the existing Phase158 walk-start predicate inputs read-only so the next
# real-world run can distinguish a stale native-health handshake from support scheduling without
# weakening any movement/collision/physics guard.

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

    healthy_pattern = re.compile(
        r'Integer\.toString\(player\.tickCount\s*-\s*1\)\.equals\(System\.getProperty\(\s*'
        r'"vs2\.phase134NativeCarryHealthyTick\."\s*\+\s*carriage\.getId\(\)\s*\)\)'
    )
    healthy_matches = list(healthy_pattern.finditer(predicate))
    if len(healthy_matches) != 1:
        raise SystemExit(
            "Phase 180 expected exactly one previous-native healthy-tick continuity expression inside Phase161 predicate, found "
            + str(len(healthy_matches)))

    continuity_clause = '''(Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
                || (phase161FixtureWalkWindow
                    && carryReplayPlayerTick == player.tickCount - 1
                    && !Integer.toString(player.tickCount).equals(System.getProperty(
                        "vs2.phase170NativeContactApplicationTick"))))'''
    predicate = healthy_pattern.sub(continuity_clause, predicate, count=1)
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

if "GATE_E_PHASE180_WALK_START_GATE" not in source:
    walk_gate = '''                        if (!phase154WalkStarted && phase154SupportNow && phase81PhysicalSupport && phase158FreshNativeCarry) {'''
    if source.count(walk_gate) != 1:
        raise SystemExit("Phase 180 expected exactly one Phase158 walk-start predicate")
    diagnostic = '''                        if (!phase154WalkStarted && productionSmokeFixture) {
                            LOGGER.info(
                                "GATE_E_PHASE180_WALK_START_GATE player_tick={} carriage_id={} support_now={} strict_physical_support={} fresh_native_carry={} native_health={} native_health_tick={} exact_cell_present={} fixture_only=true read_only=true",
                                player.tickCount, phase154Carriage.getId(), phase154SupportNow, phase81PhysicalSupport,
                                phase158FreshNativeCarry,
                                Boolean.parseBoolean(System.getProperty(
                                    "vs2.phase134NativeCarryHealthy." + phase154Carriage.getId(), "false")),
                                System.getProperty("vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId(), "missing"),
                                java.lang.Boolean.getBoolean("vs2.productionNativePlacementExactCellPresent"));
                        }
''' + walk_gate
    source = source.replace(walk_gate, diagnostic, 1)
    inserted += diagnostic

required = [
    "GATE_E_PHASE180_CONSECUTIVE_NATIVE_LOSS_RECOVERY",
    "GATE_E_PHASE180_WALK_START_GATE",
    "phase161SupportedLocomotionNativeLoss",
    "phase161FixtureWalkWindow",
    "carryReplayPlayerTick == player.tickCount - 1",
    "vs2.phase170NativeContactApplicationTick",
    "phase179ActiveContactMotionAvailable",
    "!phase179CurrentNativeHealthy",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()",
    "phase154SupportNow && phase81PhysicalSupport && phase158FreshNativeCarry",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "existing_create_filtered_replay=true",
    "fixture_only=true",
    "bounded_continuity=true",
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 180 lost bounded recovery/start-gate telemetry anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 180 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 180: extends bounded native-loss recovery and exposes read-only walk-start gate state")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase181.py")), run_name="__main__")
