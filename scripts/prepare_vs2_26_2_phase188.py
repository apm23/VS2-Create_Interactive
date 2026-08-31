#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #456 proves all four ordinary walk directions through native Minecraft locomotion.
# Build the existing sustained three-tick acceptance exactly where Phase188 originally owned it,
# but require Minecraft's native sprinting state as part of that acceptance. This is fixture-only
# acceptance logic: no position, velocity, collision, train/world, or VS2/Create physics mutation.
old = """                            if (player.tickCount <= phase154WalkStartTick + 12) {\n"""
new = """                            boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 3
                                && phase154WalkSupportHealthy
                                && phase154Carriage.getId() == phase154WalkCarriageId
                                && phase154Broadphase && player.onGround() && player.isSprinting()
                                && phase165WalkPathDistance >= 0.35 && phase165WalkPathDistance <= 4.00
                                && phase154WalkStartLocal != null
                                && Math.hypot(
                                    phase154Local.x - phase154WalkStartLocal.x,
                                    phase154Local.z - phase154WalkStartLocal.z) >= 0.35
                                && Math.hypot(
                                    phase154Local.x - phase154WalkStartLocal.x,
                                    phase154Local.z - phase154WalkStartLocal.z) <= 3.00;
                            if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady) {
"""

if "phase188PreResetWalkReady" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 188 expected exactly one bounded walk completion branch, found {count}")
    source = source.replace(old, new, 1)

required = [
    "phase188PreResetWalkReady",
    "player.tickCount >= phase154WalkStartTick + 3",
    "phase154WalkSupportHealthy",
    "phase154Broadphase && player.onGround() && player.isSprinting()",
    "phase165WalkPathDistance >= 0.35",
    "Math.hypot(",
    "phase154Local.x - phase154WalkStartLocal.x",
    "phase154Local.z - phase154WalkStartLocal.z",
    "if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady)",
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
print("Phase 188: inserts sustained supported native sprint acceptance at its original bounded-walk boundary; fixture acceptance only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase189.py")), run_name="__main__")
