#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #222 proved the exact handshake can receive only one settled native-ray
# sample in a run, so requiring two adjacent samples still races the valid interaction window.
# The Phase101 handshake already executes inside settledCreateNativeRayReady=true. Arm on that
# current exact settled ray, then let the authoritative server handshake complete; dispatch can
# occur on any later current settled ray while armed. Fixture synchronization only: no movement,
# collision, train, world, inventory, or physics mutation is introduced here.
arm_anchor = '''                                                if (productionSmokeFixture && player.tickCount >= 30
                                                        && settledExactNativeRightClickEntrypoint
                                                        && !Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {'''
arm_insert = '''                                                boolean productionSettledNativeRayHandshakeReady = true;
                                                if (productionSmokeFixture && productionSettledNativeRayHandshakeReady
                                                        && settledExactNativeRightClickEntrypoint
                                                        && !Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {'''
if "productionSettledNativeRayHandshakeReady" not in source:
    if arm_anchor not in source:
        raise SystemExit("Phase 142 could not find exact Phase101 arm-request guard")
    source = source.replace(arm_anchor, arm_insert, 1)

region_start = source.find("boolean productionSettledNativeRayHandshakeReady")
region_end = source.find("GATE_F_CONTRAPTION_MUTATION_SURFACE", region_start)
if region_start < 0 or region_end < 0:
    raise SystemExit("Phase 142 could not bound the held-block handshake region")
region = source[region_start:region_end]
region = region.replace(
    "productionSmokeFixture && player.tickCount >= 30",
    "productionSmokeFixture && productionSettledNativeRayHandshakeReady",
)
region = region.replace(
    "productionSmokeFixture\n                                                        && player.tickCount >= 30",
    "productionSmokeFixture\n                                                        && productionSettledNativeRayHandshakeReady",
)
source = source[:region_start] + region + source[region_end:]

required = [
    "productionSettledNativeRayHandshakeReady = true",
    "GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST",
    "GATE_F_SERVER_HELD_BLOCK_ARM_WAIT",
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 142 lost current-ray handshake anchors: " + ", ".join(missing))

handshake_region = source[region_start:source.find("GATE_F_CONTRAPTION_MUTATION_SURFACE", region_start)]
if "player.tickCount >= 30" in handshake_region:
    raise SystemExit("Phase 142 left a fixed tick guard inside the held-block handshake region")

for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in arm_insert:
        raise SystemExit("Phase 142 found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 142: arms held-block fixture on the current exact settled native ray")
