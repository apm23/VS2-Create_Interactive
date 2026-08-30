#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #221 proved the generic settled-ray streak anchor could observe native
# hits without the Phase101 held-block handshake seeing readiness. Bind the consecutive-hit
# state directly to the exact arm-request block instead: same carriage, immediately previous
# player tick, and the current code path is already inside settledCreateNativeRayReady=true.
# Fixture synchronization only; no movement, collision, train, world, or physics mutation.
field_anchor = "    private static boolean nativeRightClickProbeDispatched;\n"
field_insert = field_anchor + (
    "    private static int productionSettledNativeRayLastTick = Integer.MIN_VALUE;\n"
    "    private static int productionSettledNativeRayLastCarriageId = Integer.MIN_VALUE;\n"
)
if "productionSettledNativeRayLastTick" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 142 could not find native right-click fixture field anchor")
    source = source.replace(field_anchor, field_insert, 1)

arm_anchor = '''                                                if (productionSmokeFixture && player.tickCount >= 30
                                                        && settledExactNativeRightClickEntrypoint
                                                        && !Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {'''
arm_insert = '''                                                boolean productionSettledNativeRayHandshakeReady =
                                                    productionSettledNativeRayLastCarriageId == carriage.getId()
                                                        && productionSettledNativeRayLastTick == player.tickCount - 1;
                                                productionSettledNativeRayLastCarriageId = carriage.getId();
                                                productionSettledNativeRayLastTick = player.tickCount;
                                                if (productionSmokeFixture && productionSettledNativeRayHandshakeReady
                                                        && settledExactNativeRightClickEntrypoint
                                                        && !Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {'''
if "productionSettledNativeRayHandshakeReady" not in source:
    if arm_anchor not in source:
        raise SystemExit("Phase 142 could not find exact Phase101 arm-request guard")
    source = source.replace(arm_anchor, arm_insert, 1)

# Once the exact handshake-local readiness exists, use it for the matching wait and dispatch
# guards as well. Limit replacements to the Phase101/Phase138 handshake region so unrelated
# historical probes keep their own timing semantics.
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
    "productionSettledNativeRayLastTick",
    "productionSettledNativeRayLastCarriageId",
    "productionSettledNativeRayHandshakeReady",
    "productionSettledNativeRayLastTick == player.tickCount - 1",
    "GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST",
    "GATE_F_SERVER_HELD_BLOCK_ARM_WAIT",
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 142 lost handshake-local settled-ray anchors: " + ", ".join(missing))

handshake_region = source[region_start:source.find("GATE_F_CONTRAPTION_MUTATION_SURFACE", region_start)]
if "player.tickCount >= 30" in handshake_region:
    raise SystemExit("Phase 142 left a fixed tick guard inside the held-block handshake region")

for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in arm_insert:
        raise SystemExit("Phase 142 found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 142: binds consecutive settled-ray readiness directly to the held-block handshake")
