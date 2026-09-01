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
# before arming, then retain the existing strict next-tick/two-tick confirmation. This makes four stable
# observations necessary before fixture locomotion starts, without changing player position/velocity,
# collision response, carry vectors, train/world state, Create behavior, or VS2 physics.

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
                            && phase194PendingWalkAge >= 1
                            && phase194PendingWalkAge <= 2
                            && phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();
                        if (phase194DirectNativeCandidate) {
                            phase194PendingWalkCarriageId = phase154Carriage.getId();
                            phase194PendingWalkTick = player.tickCount;
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM player_tick={} carriage_id={} ready_ticks={} strict_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyTicks,
                                phase81PhysicalSupport, phase154SupportNow, carryBaselineCarriageId);
                        }
                        if (phase194ConfirmedDirectNativeReady) {
                            LOGGER.info(
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} arm_age={} strict_support={} support_now={} baseline_carriage_id={} exact_native_application=true fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick, phase194PendingWalkAge,
                                phase81PhysicalSupport, phase154SupportNow, carryBaselineCarriageId);
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
    old_confirmation = '''                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkTick == player.tickCount - 1
                            && phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();'''
    new_confirmation = '''                        int phase194PendingWalkAge = player.tickCount - phase194PendingWalkTick;
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkAge >= 1
                            && phase194PendingWalkAge <= 2
                            && phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185NativeApplicationFresh
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround();'''
    if "phase194PendingWalkAge" not in source:
        count = source.count(old_confirmation)
        if count != 1:
            raise SystemExit(f"Phase 194 expected one strict confirmation branch, found {count}")
        source = source.replace(old_confirmation, new_confirmation, 1)
        source = source.replace(
            '"GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} strict_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",\n                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick,\n                                phase81PhysicalSupport, phase154SupportNow, carryBaselineCarriageId);',
            '"GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} arm_age={} strict_support={} support_now={} baseline_carriage_id={} exact_native_application=true fixture_only=true accounting_only=true",\n                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick, phase194PendingWalkAge,\n                                phase81PhysicalSupport, phase154SupportNow, carryBaselineCarriageId);',
            1,
        )
    source = source.replace(
        "&& phase185WalkReadyTicks >= 2;",
        "&& phase185WalkReadyTicks >= 3;",
        1,
    )

required = [
    "phase194PendingWalkCarriageId",
    "phase194PendingWalkTick",
    "phase194DirectNativeCandidate",
    "phase194PendingWalkAge",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkAge >= 1",
    "phase194PendingWalkAge <= 2",
    "phase194PendingWalkTick < player.tickCount - 1",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "phase81PhysicalSupport",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase185WalkReadyTicks >= 5",
    "phase185WalkReadyTicks >= 3",
    "phase185NativeApplicationFresh",
    "arm_age={}",
    "exact_native_application=true",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 194 lost strict-confirmed walk-start anchors: " + ", ".join(missing))

inserted = field_insert + confirm_guard + new_branch
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 194 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 194: requires three native-ready ticks plus strict confirmation before fixture walk")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase195.py")), run_name="__main__")
