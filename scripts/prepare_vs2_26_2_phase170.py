#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #319 finally exercised the movement-first walk. Tick 23 applied the existing
# Create-computed/collision-filtered recovery and preserved carriage-local position. From tick 24
# onward LocalPlayer world X stayed fixed while the same carriage moved ~3.55 blocks/tick; the
# read-only Phase167 contact motion was exactly the opposite of the measured local drift. The
# current recovery selector is tied to a currently-held movement key / one-tick native-loss grace,
# but Phase165 intentionally releases the key immediately after its pulse. Test only the concrete
# hypothesis that recovery must remain eligible for the bounded fixture walk while native carry is
# absent. This is fixture-only: production behavior is unchanged, and Phase85 remains the sole
# source of the Create-computed, Create-collision-filtered carry vector.

old_decl = "boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat"
new_decl = '''boolean phase170FixtureWalkRecoveryWindow = productionSmokeFixture
            && phase154WalkStarted && !phase154WalkFinished;
        boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat'''
if "phase170FixtureWalkRecoveryWindow" not in source:
    if source.count(old_decl) != 1:
        raise SystemExit("Phase 170 expected exactly one Phase161 recovery declaration")
    source = source.replace(old_decl, new_decl, 1)

# Patch only the Phase161 declaration body. Cumulative phases have changed indentation several
# times, so match Java whitespace rather than depending on a historical formatting snapshot.
if "phase170FixtureWalkRecoveryWindow || client.options.keyUp.isDown()" not in source:
    decl_pos = source.find("boolean phase161SupportedLocomotionNativeLoss =")
    if decl_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 supported-loss declaration")
    decl_end = source.find(";", decl_pos)
    if decl_end < 0:
        raise SystemExit("Phase 170 could not bound Phase161 supported-loss declaration")
    predicate = source[decl_pos:decl_end + 1]

    key_pattern = re.compile(
        r"\(\s*client\.options\.keyUp\.isDown\(\)\s*\|\|\s*client\.options\.keyDown\.isDown\(\)\s*"
        r"\|\|\s*client\.options\.keyLeft\.isDown\(\)\s*\|\|\s*client\.options\.keyRight\.isDown\(\)\s*\)"
    )
    predicate, key_count = key_pattern.subn(
        "(phase170FixtureWalkRecoveryWindow || client.options.keyUp.isDown() || client.options.keyDown.isDown()\n"
        "                || client.options.keyLeft.isDown() || client.options.keyRight.isDown())",
        predicate,
        count=1,
    )
    if key_count != 1:
        raise SystemExit("Phase 170 expected exactly one key-state clause inside Phase161 predicate")

    previous_native_pattern = re.compile(
        r"Integer\.toString\(player\.tickCount\s*-\s*1\)\.equals\(System\.getProperty\(\s*"
        r"\"vs2\.phase134NativeCarryHealthyTick\.\"\s*\+\s*carriage\.getId\(\)\s*\)\)"
    )
    predicate, native_count = previous_native_pattern.subn(
        "(phase170FixtureWalkRecoveryWindow || Integer.toString(player.tickCount - 1).equals(System.getProperty(\n"
        "                    \"vs2.phase134NativeCarryHealthyTick.\" + carriage.getId())))",
        predicate,
        count=1,
    )
    if native_count != 1:
        raise SystemExit("Phase 170 expected exactly one previous-native clause inside Phase161 predicate")
    source = source[:decl_pos] + predicate + source[decl_end + 1:]

if "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY" not in source:
    replay_marker = '"GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY'
    marker_pos = source.find(replay_marker)
    if marker_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 replay log marker")
    if_pos = source.rfind("if (phase161SupportedLocomotionNativeLoss) {", 0, marker_pos)
    if if_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 replay log guard")
    line_start = source.rfind("\n", 0, if_pos) + 1
    indent = source[line_start:if_pos]
    log_insert = (
        f'{indent}if (phase161SupportedLocomotionNativeLoss && phase170FixtureWalkRecoveryWindow) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY carriage_id={{}} player_tick={{}} current_measurement={{}} measured_undercarry={{}} strict_support=true existing_create_filtered_replay=true fixture_only=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, phase161CurrentMeasurement, phase161MeasuredUndercarry);\n'
        f'{indent}}}\n'
    )
    source = source[:line_start] + log_insert + source[line_start:]

required = [
    "phase170FixtureWalkRecoveryWindow",
    "productionSmokeFixture",
    "phase154WalkStarted && !phase154WalkFinished",
    "phase170FixtureWalkRecoveryWindow || client.options.keyUp.isDown()",
    "phase170FixtureWalkRecoveryWindow || Integer.toString(player.tickCount - 1)",
    "phase161MeasuredUndercarry",
    "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "existing_create_filtered_replay=true",
    "fixture_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 170 lost fixture-only recovery anchors: " + ", ".join(missing))

# Phase170 changes eligibility/accounting only. The actual carry remains Phase85's existing
# Create-computed, Create-collision-filtered vector; do not introduce direct movement mutations.
phase170_inserted = new_decl + "phase170FixtureWalkRecoveryWindow" + "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY"
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in phase170_inserted:
        raise SystemExit("Phase 170 introduced direct gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 170: fixture-only sustained Create-filtered recovery hypothesis during bounded walk native-loss window")
