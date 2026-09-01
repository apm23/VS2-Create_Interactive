#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #487 exposed a startup-transient false-positive when two fresh native carry ticks
# could start the fixture directly before the active carriage lost frame continuity. Phase194 therefore
# keeps a separate immediate same-carriage confirmation before starting locomotion.
#
# Production-world #537 proved an intervening sibling carriage must invalidate that confirmation, so
# the confirmation remains exactly the next tick (arm_age == 1) and still requires an exact current-tick
# Create native application on the same baseline carriage.
#
# Production-world #538 showed exact same-carriage Create contact can exist while the simplified
# Phase81 support diagnostic is false. Production-world #574 then supplied the missing acceptance
# boundary: starting the locomotion fixture from that false-support state produced immediate local-frame
# escape once exact native application stopped, while the last green production-world #572 started from
# strict support and completed the same locomotion proof. Keep native contact as evidence, but do not use
# it to waive strict physical support when arming movement. This is fixture acceptance only; it changes
# no player position/velocity, carry vector, collision response, train/world state, Create behavior, or
# VS2 physics.
#
# Production-world #541 showed that merely seeing three exact-native ready ticks can start too early,
# before native carry itself has been proven stable. Production-world #542 then showed the opposite
# failure when this was changed to five exact-native ticks: the production carry verifier already proved
# exact native carry, but Create's exact-application sampling became intermittent and the walk could never
# arm. Reuse Phase137's existing replay-aware native-carry-health result as the settled-carry prerequisite
# instead of inventing another exact-application streak. The health tick must be at most two ticks old,
# matching Phase137's bounded health sample window.
#
# Production-world #594 proves the remaining next-tick confirmation can itself starve the finite-world
# fixture after the stronger Phase137/194 hardening: carriage 8 at tick 23 and carriage 5 at tick 33 both
# had proven native carry health, strict physical support, exact current-tick native Create application,
# grounded broadphase overlap, and matching active baseline, but the immediately following tick crossed a
# real carriage geometry/frame boundary before the confirmation could fire. Those arm ticks already meet
# every authoritative condition the later confirmation rechecks. Permit the disposable input fixture to
# start on that exact healthy native-support tick; retain the next-tick path as a fallback.
#
# Production-world #595 then proved that same-tick acceptance must still obey Phase192's completed
# fixture-acquisition boundary. Starting at tick 16 while acquisition was still actively normalizing
# support contaminated the standing-carry proof and immediately entered locomotion before the real
# production carry window was established. Keep same-tick acceptance, but only after the existing
# 32-tick fixture acquisition has completed. This is harness acceptance only: no player position,
# velocity, collision response, carry vector, train/world state, or VS2/Create physics is changed.

field_anchor = "    private static int phase185WalkReadyTicks = 0;\n"
field_insert = field_anchor + (
    "    private static int phase194PendingWalkCarriageId = -1;\n"
    "    private static int phase194PendingWalkTick = Integer.MIN_VALUE;\n"
)
if source.count(field_anchor) != 1:
    raise SystemExit("Phase 194 could not locate unique Phase185 readiness field anchor")
source = source.replace(field_anchor, field_insert, 1)

# Phase162 now preserves the Phase129 acquisition predicate in both the retry gate and
# the matching acquisition-counter gate. Keep Phase194's pending-confirmation freeze
# attached to both canonical guards so the two harness branches cannot diverge.
acquire_guard = "fixtureContactAcquireTicks < 32 && !phase154WalkStarted"
confirm_guard = "fixtureContactAcquireTicks < 32 && !phase154WalkStarted && phase194PendingWalkTick < player.tickCount - 1"
if source.count(acquire_guard) != 2:
    raise SystemExit("Phase 194 expected both canonical Phase162 fixture-acquisition guards")
source = source.replace(acquire_guard, confirm_guard, 2)

old_readiness = '''                        boolean phase185WalkReadyNow = phase154SupportNow
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
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32)
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
if source.count(old_readiness) != 1:
    raise SystemExit("Phase 194 expected one final Phase192 readiness clause")
source = source.replace(old_readiness, new_readiness, 1)

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
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM player_tick={} carriage_id={} native_health_tick={} native_health_age={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194NativeCarryHealthyTick,
                                phase194NativeCarryHealthyAge, phase81PhysicalSupport,
                                phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId);
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
    "phase81PhysicalSupport",
    "fixtureContactAcquireTicks >= 32",
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
print("Phase 194: starts M1 only after completed acquisition on proven strict native support")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase195.py")), run_name="__main__")
