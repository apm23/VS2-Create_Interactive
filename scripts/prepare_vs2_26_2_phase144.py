#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #230 proved the exact Create-native ray can exist for only one client tick:
# the arm request was published on that ray, then the integrated server armed STONE after the
# ray window had already closed. Pre-arm only the disposable production fixture once the
# player is on the active carriage baseline, grounded, and inside the carriage broadphase.
# Actual interaction remains gated by the later exact Create-native ray and authoritative
# server-armed STONE path; this does not dispatch interaction or modify movement/physics.
anchor = '''                    boolean baselineFrame = localFrameCarriage.getId() == carryBaselineCarriageId;
                    LOGGER.info(
                        "GATE_E_CARRIAGE_LOCAL_CONTINUITY player_tick={} carriage_id={} local_feet={} world_distance_sq={} broadphase={} on_ground={} baseline_frame={} read_only=true",'''
insert = '''                    boolean baselineFrame = localFrameCarriage.getId() == carryBaselineCarriageId;
                    if (productionSmokeFixture
                            && player.tickCount >= 30
                            && baselineFrame
                            && broadphase
                            && player.onGround()
                            && !Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {
                        System.setProperty("vs2.productionHeldBlockServerArmRequested", "true");
                        LOGGER.info("GATE_F_SERVER_HELD_BLOCK_PREARM_REQUEST carriage_id={} player_tick={} requested=true fixture_only=true readiness_source=stable_baseline_support",
                            localFrameCarriage.getId(), player.tickCount);
                    }
                    LOGGER.info(
                        "GATE_E_CARRIAGE_LOCAL_CONTINUITY player_tick={} carriage_id={} local_feet={} world_distance_sq={} broadphase={} on_ground={} baseline_frame={} read_only=true",'''

if "GATE_F_SERVER_HELD_BLOCK_PREARM_REQUEST" not in source:
    if anchor not in source:
        raise SystemExit("Phase 144 could not find continuity baseline anchor")
    source = source.replace(anchor, insert, 1)

required = [
    "GATE_F_SERVER_HELD_BLOCK_PREARM_REQUEST",
    "readiness_source=stable_baseline_support",
    "vs2.productionHeldBlockServerArmRequested",
    "baselineFrame",
    "broadphase",
    "player.onGround()",
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 144 lost pre-arm anchors: " + ", ".join(missing))

for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", ".useItemOn(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in insert:
        raise SystemExit("Phase 144 found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 144: pre-arms disposable held-block fixture on stable active-carriage support; exact native ray still gates dispatch")
