#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #456 proves all four ordinary walk directions through native Minecraft locomotion.
# Strengthen the existing bounded walk acceptance for the next M1 step: the same supported three-tick
# proof must now also observe the LocalPlayer in Minecraft's native sprinting state. This changes only
# fixture acceptance; it does not write position, velocity, collision, train/world, or VS2/Create physics.
old = """                            boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 3
                                && phase154WalkSupportHealthy
                                && phase154Carriage.getId() == phase154WalkCarriageId
                                && phase154Broadphase && player.onGround()
                                && phase165WalkPathDistance >= 0.35 && phase165WalkPathDistance <= 4.00
"""
new = """                            boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 3
                                && phase154WalkSupportHealthy
                                && phase154Carriage.getId() == phase154WalkCarriageId
                                && phase154Broadphase && player.onGround() && player.isSprinting()
                                && phase165WalkPathDistance >= 0.35 && phase165WalkPathDistance <= 4.00
"""

if "phase154Broadphase && player.onGround() && player.isSprinting()" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 188 expected one sustained walk acceptance block, found {count}")
    source = source.replace(old, new, 1)

required = [
    "phase188PreResetWalkReady",
    "player.tickCount >= phase154WalkStartTick + 3",
    "phase154WalkSupportHealthy",
    "phase154Broadphase && player.onGround() && player.isSprinting()",
    "phase165WalkPathDistance >= 0.35",
    "Math.hypot(",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 188 lost native sprint-proof anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in new:
        raise SystemExit("Phase 188 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 188: requires sustained supported native sprint state before bounded locomotion completion; fixture acceptance only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase189.py")), run_name="__main__")
