#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase194 hardens the disposable locomotion fixture after proven native Create carry.
# Phase192 now releases its readiness gate when Phase129 has already ended fixture assistance via
# fixtureNativeCarrySettled, so consume that cumulative predicate directly instead of requiring the
# historical counter-only spelling. This is harness composition only: no player position/velocity,
# carry vector, collision response, train/world state, Create behavior, or VS2 physics is changed.

field_anchor = "    private static int phase185WalkReadyTicks = 0;\n"
field_insert = field_anchor + (
    "    private static int phase194PendingWalkCarriageId = -1;\n"
    "    private static int phase194PendingWalkTick = Integer.MIN_VALUE;\n"
)
if source.count(field_anchor) != 1:
    raise SystemExit("Phase 194 could not locate unique Phase185 readiness field anchor")
source = source.replace(field_anchor, field_insert, 1)

acquire_guard = "fixtureContactAcquireTicks < 32 && !phase154WalkStarted"
confirm_guard = "fixtureContactAcquireTicks < 32 && !phase154WalkStarted && phase194PendingWalkTick < player.tickCount - 1"
if source.count(acquire_guard) != 2:
    raise SystemExit("Phase 194 expected both canonical Phase162 fixture-acquisition guards")
source = source.replace(acquire_guard, confirm_guard, 2)

old_readiness = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (!productionSmokeFixture || fixtureNativeCarrySettled || fixtureContactAcquireTicks >= 32)
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
legacy_readiness = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32)
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
new_readiness = '''                        boolean phase194NativeAuthoritativeSupport = phase154SupportNow
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();
                        int phase194NativeCarryHealthyTick = Integer.MIN_VALUE;
                        try {
                            phase194NativeCarryHealthyTick = Integer.parseInt(System.getProperty(
                                "vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId(), "-2147483648"));
                        } catch (NumberFormatException ignored) {
                            phase194NativeCarryHealthyTick = Integer.MIN_VALUE;
                        }
                        int phase194NativeCarryHealthyAge = player.tickCount - phase194NativeCarryHealthyTick;
                        boolean phase194ProvenNativeCarryHealth = Boolean.parseBoolean(System.getProperty(
                                "vs2.phase134NativeCarryHealthy." + phase154Carriage.getId(), "false"))
                            && phase194NativeCarryHealthyTick != Integer.MIN_VALUE
                            && phase194NativeCarryHealthyAge >= 0 && phase194NativeCarryHealthyAge <= 2
                            && phase154SupportNow
                            && phase81PhysicalSupport
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();
                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32 || fixtureNativeCarrySettled)
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
if source.count(old_readiness) == 1:
    source = source.replace(old_readiness, new_readiness, 1)
elif source.count(legacy_readiness) == 1:
    source = source.replace(legacy_readiness, new_readiness, 1)
else:
    raise SystemExit("Phase 194 expected one final Phase192 readiness clause")

old_branch = '''                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && (phase185WalkReadyTicks >= 5
                                    || (phase185NativeApplicationFresh && phase185WalkReadyTicks >= 2))) {'''
new_branch = '''                        boolean phase194DirectNativeCandidate = !phase154WalkStarted
                            && phase194ProvenNativeCarryHealth
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32);
                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh;
                        int phase194PendingWalkAge = player.tickCount - phase194PendingWalkTick;
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkAge == 1
                            && phase81PhysicalSupport
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();
                        if (phase194DirectNativeCandidate) {
                            phase194PendingWalkCarriageId = phase154Carriage.getId();
                            phase194PendingWalkTick = player.tickCount;
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM player_tick={} carriage_id={} native_health_tick={} native_health_age={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} fixture_native_settled={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194NativeCarryHealthyTick,
                                phase194NativeCarryHealthyAge, phase81PhysicalSupport,
                                phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId,
                                fixtureNativeCarrySettled);
                        }
                        if (phase194ConfirmedDirectNativeReady) {
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} arm_age={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} exact_native_application=true fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick, phase194PendingWalkAge,
                                phase81PhysicalSupport, phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId);
                        }
                        if (phase194ImmediateHealthyNativeReady) {
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_IMMEDIATE player_tick={} carriage_id={} native_health_tick={} native_health_age={} strict_support=true native_authoritative_support=true exact_native_application=true fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194NativeCarryHealthyTick,
                                phase194NativeCarryHealthyAge);
                        }
                        if (!phase154WalkStarted
                                && ((phase185WalkReadyNow
                                    && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                    && phase185WalkReadyTicks >= 5)
                                    || (phase194DirectNativeCandidate && phase194NativeAuthoritativeSupport)
                                    || phase194ImmediateHealthyNativeReady
                                    || phase194ConfirmedDirectNativeReady)) {'''
if source.count(old_branch) != 1:
    raise SystemExit("Phase 194 expected one Phase192 direct-native start branch")
source = source.replace(old_branch, new_branch, 1)

required = [
    "phase194PendingWalkCarriageId",
    "phase194PendingWalkTick",
    "phase194NativeAuthoritativeSupport",
    "phase194NativeCarryHealthyTick",
    "phase194NativeCarryHealthyAge",
    "phase194ProvenNativeCarryHealth",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "phase194NativeCarryHealthyAge <= 2",
    "phase194DirectNativeCandidate",
    "phase194ImmediateHealthyNativeReady",
    "phase194PendingWalkAge",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkAge == 1",
    "phase194PendingWalkTick < player.tickCount - 1",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase185WalkReadyTicks >= 5",
    "phase185NativeApplicationFresh",
    "fixtureContactAcquireTicks >= 32 || fixtureNativeCarrySettled",
    "fixtureNativeCarrySettled",
    "phase194DirectNativeCandidate && phase194NativeAuthoritativeSupport",
    "native_health_age={}",
    "exact_native_application=true",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_IMMEDIATE",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 194 lost native-health walk-start anchors: " + ", ".join(missing))

inserted = new_readiness + field_insert + confirm_guard + new_branch
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 194 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 194: accepts Phase129-settled cumulative readiness while preserving native-health walk hardening")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase195.py")), run_name="__main__")
