#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #487 exposed a startup-transient false-positive: two fresh native carry ticks can
# arm the fixture immediately before the active carriage loses frame continuity. Require three fresh
# supported native-ready ticks before arming, then keep the existing next-tick strict confirmation.
# This only strengthens fixture acceptance; no player position/velocity, collision response, carry
# vector, train/world state, inventory, Create behavior, or VS2 physics is changed.

field_anchor = "    private static int phase185WalkReadyTicks = 0;\n"
field_insert = field_anchor + (
    "    private static int phase194PendingWalkCarriageId = -1;\n"
    "    private static int phase194PendingWalkTick = Integer.MIN_VALUE;\n"
)
if "phase194PendingWalkTick" not in source:
    if source.count(field_anchor) != 1:
        raise SystemExit("Phase 194 could not locate unique Phase185 readiness field anchor")
    source = source.replace(field_anchor, field_insert, 1)

# Phase162 already freezes contact acquisition after the walk starts. Extend that existing harness
# boundary one tick earlier, but only while a direct-native arm is awaiting confirmation. The composed
# Phase193 source has one canonical Phase162 acquisition guard. Because the arm is set later in the same
# client tick, the current acquisition attempt is untouched; the next tick is unassisted, and retries
# automatically resume one tick later if confirmation did not succeed.
acquire_guard = "fixtureContactAcquireTicks < 48 && !phase154WalkStarted"
confirm_guard = "fixtureContactAcquireTicks < 48 && !phase154WalkStarted && phase194PendingWalkTick < player.tickCount - 1"
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
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkTick == player.tickCount - 1
                            && phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
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
                                "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED player_tick={} carriage_id={} armed_tick={} strict_support={} support_now={} baseline_carriage_id={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase194PendingWalkTick,
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

required = [
    "phase194PendingWalkCarriageId",
    "phase194PendingWalkTick",
    "phase194DirectNativeCandidate",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkTick == player.tickCount - 1",
    "phase194PendingWalkTick < player.tickCount - 1",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "phase81PhysicalSupport",
    "phase185FreshNativeEvidence",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase185WalkReadyTicks >= 5",
    "phase185WalkReadyTicks >= 3",
    "phase185NativeApplicationFresh",
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
print("Phase 194: requires three fresh supported native-ready ticks before strict next-tick walk confirmation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase195.py")), run_name="__main__")
