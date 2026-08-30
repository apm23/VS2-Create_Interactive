#!/usr/bin/env python3
from pathlib import Path

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

# Patch only the Phase161 supported-loss declaration body. Later cumulative phases can change
# nearby under-carry thresholds/indentation, so do not depend on one giant verbatim source block.
if "phase170FixtureWalkRecoveryWindow\n                || client.options.keyUp.isDown()" not in source:
    decl_pos = source.find("boolean phase161SupportedLocomotionNativeLoss =")
    if decl_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 supported-loss declaration")
    decl_end = source.find(";", decl_pos)
    if decl_end < 0:
        raise SystemExit("Phase 170 could not bound Phase161 supported-loss declaration")
    predicate = source[decl_pos:decl_end + 1]

    key_expr = '''(client.options.keyUp.isDown() || client.options.keyDown.isDown()
                || client.options.keyLeft.isDown() || client.options.keyRight.isDown())'''
    key_replacement = '''(phase170FixtureWalkRecoveryWindow
                || client.options.keyUp.isDown() || client.options.keyDown.isDown()
                || client.options.keyLeft.isDown() || client.options.keyRight.isDown())'''
    if predicate.count(key_expr) != 1:
        raise SystemExit("Phase 170 expected exactly one key-state clause inside Phase161 predicate")
    predicate = predicate.replace(key_expr, key_replacement, 1)

    previous_native = '''Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()))'''
    previous_native_replacement = '''(phase170FixtureWalkRecoveryWindow
                || Integer.toString(player.tickCount - 1).equals(System.getProperty(
                    "vs2.phase134NativeCarryHealthyTick." + carriage.getId())))'''
    if predicate.count(previous_native) != 1:
        raise SystemExit("Phase 170 expected exactly one previous-native clause inside Phase161 predicate")
    predicate = predicate.replace(previous_native, previous_native_replacement, 1)
    source = source[:decl_pos] + predicate + source[decl_end + 1:]

log_anchor = '''if (phase161SupportedLocomotionNativeLoss) {
            LOGGER.info(
                "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY'''
log_insert = '''if (phase161SupportedLocomotionNativeLoss && phase170FixtureWalkRecoveryWindow) {
            LOGGER.info(
                "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY carriage_id={} player_tick={} current_measurement={} measured_undercarry={} strict_support=true existing_create_filtered_replay=true fixture_only=true",
                carriage.getId(), player.tickCount, phase161CurrentMeasurement, phase161MeasuredUndercarry);
        }
        if (phase161SupportedLocomotionNativeLoss) {
            LOGGER.info(
                "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY'''
if "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY" not in source:
    if source.count(log_anchor) != 1:
        raise SystemExit("Phase 170 expected exactly one Phase161 replay log anchor")
    source = source.replace(log_anchor, log_insert, 1)

required = [
    "phase170FixtureWalkRecoveryWindow",
    "productionSmokeFixture",
    "phase154WalkStarted && !phase154WalkFinished",
    "phase170FixtureWalkRecoveryWindow\n                || client.options.keyUp.isDown()",
    "phase170FixtureWalkRecoveryWindow\n                || Integer.toString(player.tickCount - 1)",
    "phase161MeasuredUndercarry",
    "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "existing_create_filtered_replay=true",
    "fixture_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 170 lost fixture-only recovery anchors: " + ", ".join(missing))

patch_text = new_decl + key_replacement + previous_native_replacement + log_insert
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 170 introduced direct gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 170: fixture-only sustained Create-filtered recovery hypothesis during bounded walk native-loss window")
