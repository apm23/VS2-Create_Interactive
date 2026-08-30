#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #300 proved Phase162 removed fixture repositioning, but the walk proof
# still sampled whichever carryBaseline carriage happened to be active each tick. The player
# remained on-ground and broadphase=true, while the selector handed off 7 -> 5 -> 7 -> 5 -> 4;
# those sibling-frame changes produced artificial 13-block local jumps and marked the proof
# unhealthy. Pin only the fixture walk measurement to the carriage on which the walk started.
# Production carry selection, Create collision, player motion, train/world state and VS2 physics
# remain untouched.
old_select = '''                net.minecraft.world.entity.Entity phase154Carriage = null;
                if (carryBaselineCarriageId != Integer.MIN_VALUE) {
                    phase154Carriage = client.level.getEntity(carryBaselineCarriageId);
                }'''
new_select = '''                net.minecraft.world.entity.Entity phase154Carriage = null;
                int phase163WalkMeasurementCarriageId = phase154WalkStarted && phase154WalkCarriageId >= 0
                    ? phase154WalkCarriageId : carryBaselineCarriageId;
                if (phase163WalkMeasurementCarriageId != Integer.MIN_VALUE) {
                    phase154Carriage = client.level.getEntity(phase163WalkMeasurementCarriageId);
                }'''
if "phase163WalkMeasurementCarriageId" not in source:
    if source.count(old_select) != 1:
        raise SystemExit("Phase 163 expected exactly one Phase154 walk carriage selector")
    source = source.replace(old_select, new_select, 1)

old_support = '''                        boolean phase154SupportNow = phase154Broadphase && player.onGround()
                            && phase154Carriage.getId() == carryBaselineCarriageId;'''
new_support = '''                        boolean phase154SupportNow = phase154Broadphase && player.onGround()
                            && (!phase154WalkStarted || phase154Carriage.getId() == phase154WalkCarriageId);'''
if "(!phase154WalkStarted || phase154Carriage.getId() == phase154WalkCarriageId)" not in source:
    if source.count(old_support) != 1:
        raise SystemExit("Phase 163 expected exactly one Phase154 support predicate")
    source = source.replace(old_support, new_support, 1)

required = [
    "phase163WalkMeasurementCarriageId",
    "phase154WalkStarted && phase154WalkCarriageId >= 0",
    "phase154Carriage = client.level.getEntity(phase163WalkMeasurementCarriageId)",
    "(!phase154WalkStarted || phase154Carriage.getId() == phase154WalkCarriageId)",
    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 163 lost pinned walk-measurement anchors: " + ", ".join(missing))

patch_text = new_select + new_support
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 163 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 163: pins fixture walk measurement to the start carriage so sibling carry-baseline handoffs cannot corrupt local displacement telemetry")
