#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #416 proved that the two-tick exact-native readiness path can start the disposable
# walk on the final tick of a transient support window. Carriage 7 had strict support plus exact native
# Create application at ticks 23-24, the walk started at tick 24, then strict Phase81 support was already
# false/NaN on tick 25 even though the player stayed grounded and broadphase-overlapping. Tick 25 was
# covered by the existing one-tick replay grace, but tick 26 then drifted exactly by the carriage frame
# step. Do not alter carry vectors or support thresholds. Arm the direct-native shortcut after its two
# qualifying ticks, then require one full following tick of the same active-baseline carriage with strict
# support before actually pressing the fixture key. The conservative five-tick readiness path is unchanged.
# Harness timing/accounting only: no player position/velocity, collision response, train/world state,
# inventory, Create behavior, or VS2 physics is changed.

field_anchor = "    private static int phase185WalkReadyTicks = 0;\n"
field_insert = field_anchor + (
    "    private static int phase194PendingWalkCarriageId = -1;\n"
    "    private static int phase194PendingWalkTick = Integer.MIN_VALUE;\n"
)
if "phase194PendingWalkTick" not in source:
    if source.count(field_anchor) != 1:
        raise SystemExit("Phase 194 could not locate unique Phase185 readiness field anchor")
    source = source.replace(field_anchor, field_insert, 1)

old_branch = '''                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && (phase185WalkReadyTicks >= 5
                                    || (phase185NativeApplicationFresh && phase185WalkReadyTicks >= 2))) {'''
new_branch = '''                        boolean phase194DirectNativeCandidate = !phase154WalkStarted
                            && phase185WalkReadyNow
                            && phase185WalkReadyCarriageId == phase154Carriage.getId()
                            && phase185NativeApplicationFresh
                            && phase185WalkReadyTicks >= 2;
                        boolean phase194ConfirmedDirectNativeReady = !phase154WalkStarted
                            && phase194PendingWalkCarriageId == phase154Carriage.getId()
                            && phase194PendingWalkTick == player.tickCount - 1
                            && phase154SupportNow
                            && phase81PhysicalSupport
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
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "phase81PhysicalSupport",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase185WalkReadyTicks >= 5",
    "phase185NativeApplicationFresh",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM",
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_CONFIRMED",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 194 lost strict-confirmed walk-start anchors: " + ", ".join(missing))

inserted = field_insert + new_branch
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 194 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 194: requires one full strict-support tick after the two-tick direct-native walk arm; fixture timing only")
