#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = client_probe.read_text(encoding="utf-8")
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #330 reached the real train and proved carry, native handled right-click, and
# packet-authoritative new-cell replication. During the bounded one-pulse walk, native Create carry
# disappeared on alternating ticks: Phase161 recovery succeeded on ticks with a same-tick balance
# measurement, but the immediately following no-measurement tick drifted by exactly carriage motion.
# In the disposable production smoke fixture only, permit the already-measured material under-carry
# result to remain valid for one additional tick when Phase170 proves no native Create application
# happened this tick. This changes recovery eligibility only; Phase85 remains the sole producer of
# the existing Create-computed/collision-filtered carry vector. No new movement vector or physics
# behavior is introduced outside the fixture.
anchor = '''        boolean phase170FixtureWalkRecoveryWindow = phase170FixtureWalkActive
            && !phase170NativeContactAppliedThisTick;
        boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat'''
replacement = '''        boolean phase170FixtureWalkRecoveryWindow = phase170FixtureWalkActive
            && !phase170NativeContactAppliedThisTick;
        boolean phase172PreviousMeasurement = Integer.toString(player.tickCount - 1).equals(
            System.getProperty("vs2.phase161MeasurementTick." + carriage.getId()));
        boolean phase172FixturePreviousUndercarry = phase170FixtureWalkRecoveryWindow
            && phase172PreviousMeasurement
            && Double.isFinite(phase161CarriageMotionSq) && Double.isFinite(phase161NativeCarryProjection)
            && phase161CarriageMotionSq > 1.0E-8
            && phase161NativeCarryProjection < phase161CarriageMotionSq * 0.75;
        boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat'''
inserted = ""
if "phase172FixturePreviousUndercarry" not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Phase 172 expected exactly one Phase170 recovery-window declaration")
    source = source.replace(anchor, replacement, 1)
    inserted += replacement

    decl_pos = source.find("boolean phase161SupportedLocomotionNativeLoss =")
    decl_end = source.find(";", decl_pos)
    if decl_pos < 0 or decl_end < 0:
        raise SystemExit("Phase 172 could not bound Phase161 recovery predicate")
    predicate = source[decl_pos:decl_end + 1]
    old = "&& phase161MeasuredUndercarry;"
    new = "&& (phase161MeasuredUndercarry || phase172FixturePreviousUndercarry);"
    if predicate.count(old) != 1:
        raise SystemExit("Phase 172 expected exactly one Phase161 undercarry terminal predicate")
    predicate = predicate.replace(old, new, 1)
    source = source[:decl_pos] + predicate + source[decl_end + 1:]
    inserted += new

    marker = '''        if (phase170FixtureWalkActive && phase170NativeContactAppliedThisTick) {'''
    log = '''        if (phase172FixturePreviousUndercarry && !phase161MeasuredUndercarry) {
            LOGGER.info(
                "GATE_E_PHASE172_PREVIOUS_TICK_UNDERCARRY_RECOVERY player_tick={} carriage_id={} previous_measurement=true native_application_this_tick=false strict_support_required=true fixture_only=true",
                player.tickCount, carriage.getId());
        }
'''
    if source.count(marker) != 1:
        raise SystemExit("Phase 172 expected exactly one Phase170 accounting log anchor")
    source = source.replace(marker, log + marker, 1)
    inserted += log

required_client = [
    "GATE_E_CARRIAGE_LOCAL_CONTINUITY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED",
    "GATE_E_PHASE170_NATIVE_CONTACT_SUPPRESSES_RECOVERY",
    "phase172FixturePreviousUndercarry",
    "GATE_E_PHASE172_PREVIOUS_TICK_UNDERCARRY_RECOVERY",
    "phase161MeasuredUndercarry || phase172FixturePreviousUndercarry",
]
required_contact = [
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
    "GATE_E_PHASE171_CARRIAGE_FRAME_STEP",
]
missing = [token for token in required_client if token not in source] + [token for token in required_contact if token not in contact_source]
if missing:
    raise SystemExit("Phase 172 lost bounded recovery/proof anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 172 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 172: bridges one-tick fixture undercarry telemetry gaps without changing carry vectors or production physics")
