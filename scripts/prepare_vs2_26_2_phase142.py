#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #218 proved sustained carry, but the fixed player_tick>=30 interaction
# gate raced past the only settled native-ray window (ticks 27-28), so no server arm request
# or native dispatch occurred. Replace that wall-clock threshold with two consecutive settled
# Create-native ray samples. This stays fixture-only and changes no movement/physics behavior.
field_anchor = "    private static boolean nativeRightClickProbeDispatched;\n"
field_insert = field_anchor + "    private static int productionSettledNativeRayReadyStreak;\n"
if "productionSettledNativeRayReadyStreak" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 142 could not find native right-click fixture field anchor")
    source = source.replace(field_anchor, field_insert, 1)

ray_anchor = '''                                        boolean settledCreateNativeRayReady = settledNativeRayState.contains("hit=")
                                            && settledNativeRayState.contains("face=")
                                            && !settledNativeRayState.contains("miss");
'''
ray_insert = ray_anchor + '''                                        if (settledCreateNativeRayReady) {
                                            productionSettledNativeRayReadyStreak++;
                                        } else {
                                            productionSettledNativeRayReadyStreak = 0;
                                        }
'''
if "productionSettledNativeRayReadyStreak++;" not in source:
    if ray_anchor not in source:
        raise SystemExit("Phase 142 could not find settled native-ray readiness anchor")
    source = source.replace(ray_anchor, ray_insert, 1)

old = "productionSmokeFixture && player.tickCount >= 30"
count = source.count(old)
if count:
    source = source.replace(old, "productionSmokeFixture && productionSettledNativeRayReadyStreak >= 2")
if "player.tickCount >= 30" in source[source.find("GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST") - 1800:source.find("GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH") + 2400]:
    raise SystemExit("Phase 142 left a fixed tick interaction gate in the held-block handshake")

required = [
    "productionSettledNativeRayReadyStreak",
    "productionSettledNativeRayReadyStreak >= 2",
    "GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST",
    "GATE_F_SERVER_HELD_BLOCK_ARM_WAIT",
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 142 lost settled-ray handshake anchors: " + ", ".join(missing))

for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in ray_insert:
        raise SystemExit("Phase 142 found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 142: gates fixture held-block arm/dispatch on two consecutive settled Create-native rays instead of fixed player tick")
