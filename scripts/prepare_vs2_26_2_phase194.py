#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #487 exposed a startup-transient false-positive when two fresh native carry ticks
# could start the fixture directly before the active carriage lost frame continuity. Phase194 now has
# a separate strict-support confirmation. Production-world #523 proved a one-tick sibling-carriage
# selection can occupy the immediate confirmation tick even though the armed carriage returns one tick
# later with strict support and an exact current-tick native Create application.
#
# Production-world #536 then exposed the remaining fixture boundary: three consecutive ready samples
# on carriage 5 (ticks 15-17) were followed immediately by a sibling handoff at tick 18. The walk was
# started at tick 17, remained grounded/broadphase-valid, but necessarily crossed carriage identity and
# could not satisfy the bounded single-frame proof. Require three fresh same-carriage native-ready ticks
# before arming.
#
# Production-world #537 proves that accepting a two-tick confirmation after an intervening sibling seam
# still starts locomotion on a discontinuous route frame: carriage 8 armed at tick 17, sibling carriage
# 10 occupied tick 18, then carriage 8 returned at tick 19 and the old age<=2 rule started the walk.
# Reject that seam entirely. Direct-native confirmation must now be the immediately following tick on
# the same carriage.
#
# Production-world #538 then proved the remaining readiness mismatch: Create applied exact native
# same-carriage contact for a stable multi-tick interval while the simplified Phase81 collider classified
# the player's XZ point outside its reduced support boxes. The player nevertheless remained grounded,
# broadphase-overlapping, on the baseline carriage, and Create's exact native contact application was
# current. For the direct-native path, treat that exact Create application as the authoritative support
# signal instead of requiring the simplified diagnostic collider to agree. The sibling-seam age==1 rule
# remains mandatory. This is fixture acceptance only; no player position/velocity, collision response,
# carry vector, train/world state, Create behavior, or VS2 physics is changed.

field_anchor = "    private static int phase185WalkReadyTicks = 0;\n"
field_insert = field_anchor + (
    "    private static int phase194PendingWalkCarriageId = -1;\n"
    "    private static int phase194PendingWalkTick = Integer.MIN_VALUE;\n"
)
if "phase194PendingWalkTick" not in source:
    if source.count(field_anchor) != 1:
        raise SystemExit("Phase 194 could not locate unique Phase185 readiness field anchor")
    source = source.replace(field_anchor, field_insert, 1)

acquire_guard = "fixtureContactAcquireTicks < 32 && !phase154WalkStarted"
confirm_guard = "fixtureContactAcquireTicks < 32 && !phase154WalkStarted && phase194PendingWalkTick < player.tickCount - 1"
if confirm_guard not in source:
    count = source.count(acquire_guard)
    if count != 1:
        raise SystemExit(f"Phase 194 expected one canonical Phase162 fixture-acquisition guard, found {count}")
    source = source.replace(acquire_guard, confirm_guard, 1)

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
                        boolean phase185WalkReadyNow = phase154SupportNow
                            && (phase81PhysicalSupport || phase194NativeAuthoritativeSupport)
                            && phase185FreshNativeEvidence
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32)
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
if "phase194NativeAuthoritativeSupport" not in source:
    count = source.count(old_readiness)
    if count != 1:
        raise SystemExit(f"Phase 194 expected one final Phase192 readiness clause, found {count}")
    source = source.replace(old_readiness, new_readiness, 1)

old_branch = '''                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && (phase185WalkReadyTicks >= 5
                                    || (phase185NativeApplicationFresh && phase185WalkReadyTicks >= 2))) {'''
new_branch = '''                        boolean phase194DirectNativeCandidate = !phase154WalkStarted
                            && phase185WalkReadyNow
                            && phase185WalkReadyCarriageId == phase154Carriage.getId()
                            && phase185NativeApplicationFresh
                            && phase185WalkReadyTicks >= 3;
                        int phase194PendingWalkAge = player.tickCount - phase194PendingWalkTick;
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkAge == 1
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();
                        if (phase194DirectNativeCandidate) {
                            phase194PendingWalkCarriageId = phase154Carriage.getId();
                            phase194PendingWalkTick = player.tickCount;
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM player_tick={} carriage_id={} ready_ticks={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyTicks,
                                phase81PhysicalSupport, phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId);
                        }
                        if (phase194ConfirmedDirectNativeReady) {
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} arm_age={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} exact_native_application=true fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick, phase194PendingWalkAge,
                                phase81PhysicalSupport, phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId);
                        }
                        if (!phase154WalkStarted
                                && ((phase185WalkReadyNow
                                    && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                    && phase185WalkReadyTicks >= 5)
                                    || phase194ConfirmedDirectNativeReady)) {'''
if "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM" not in source:
    count = source.count(old_branch)
    if count != 1:
        raise SystemExit(f"Phase 194 expected one Phase192 direct-native start branch, found {count}")
    source = source.replace(old_branch, new_branch, 1)
else:
    old_confirmation = '''                        int phase194PendingWalkAge = player.tickCount - phase194PendingWalkTick;
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkAge == 1
                            && phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();'''
    new_confirmation = '''                        int phase194PendingWalkAge = player.tickCount - phase194PendingWalkTick;
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkAge == 1
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();'''
    if old_confirmation in source:
        source = source.replace(old_confirmation, new_confirmation, 1)
    source = source.replace(
        "&& phase185WalkReadyTicks >= 2;",
        "&& phase185WalkReadyTicks >= 3;",
        1,
    )
    source = source.replace(
        '"GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM player_tick={} carriage_id={} ready_ticks={} strict_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",\n                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyTicks,\n                                phase81PhysicalSupport, phase154SupportNow, carryBaselineCarriageId);',
        '"GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM player_tick={} carriage_id={} ready_ticks={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",\n                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyTicks,\n                                phase81PhysicalSupport, phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId);',
        1,
    )
    source = source.replace(
        '"GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} arm_age={} strict_support={} support_now={} baseline_carriage_id={} exact_native_application=true fixture_only=true accounting_only=true",\n                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick, phase194PendingWalkAge,\n                                phase81PhysicalSupport, phase154SupportNow, carryBaselineCarriageId);',
        '"GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} arm_age={} strict_support={} native_authoritative_support={} support_now={} baseline_carriage_id={} exact_native_application=true fixture_only=true accounting_only=true",\n                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick, phase194PendingWalkAge,\n                                phase81PhysicalSupport, phase194NativeAuthoritativeSupport, phase154SupportNow, carryBaselineCarriageId);',
        1,
    )

required = [
    "phase194PendingWalkCarriageId",
    "phase194PendingWalkTick",
    "phase194NativeAuthoritativeSupport",
    "phase81PhysicalSupport || phase194NativeAuthoritativeSupport",
    "phase194DirectNativeCandidate",
    "phase194PendingWalkAge",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkAge == 1",
    "phase194PendingWalkTick < player.tickCount - 1",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase185WalkReadyTicks >= 5",
    "phase185WalkReadyTicks >= 3",
    "phase185NativeApplicationFresh",
    "native_authoritative_support={}",
    "arm_age={}",
    "exact_native_application=true",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 194 lost native-authoritative walk-start anchors: " + ", ".join(missing))

inserted = new_readiness + field_insert + confirm_guard + new_branch
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 194 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 194: trusts exact same-carriage Create native support while preserving immediate seam rejection")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase195.py")), run_name="__main__")
