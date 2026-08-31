#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #456 proves all four ordinary walk directions through native Minecraft locomotion.
# Strengthen only the existing Phase188 acceptance seam for the next M1 step: require Minecraft's
# native sprinting state on the already-supported three-tick locomotion proof. Match the stable
# onGround/broadphase predicate itself instead of a larger composed block so later Phase composition
# cannot invalidate this harness patch. No position, velocity, collision, train/world, or VS2/Create
# physics state is written here.
old_guard = "                                && phase154Broadphase && player.onGround()\n"
new_guard = "                                && phase154Broadphase && player.onGround() && player.isSprinting()\n"

if new_guard not in source:
    marker = "boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 3"
    start = source.find(marker)
    if start < 0:
        raise SystemExit("Phase 188 lost sustained walk acceptance marker")
    end = source.find(";", start)
    if end < 0:
        raise SystemExit("Phase 188 could not bound sustained walk acceptance expression")
    block = source[start:end + 1]
    count = block.count(old_guard)
    if count != 1:
        raise SystemExit(f"Phase 188 expected one onGround/broadphase guard inside sustained acceptance, found {count}")
    block = block.replace(old_guard, new_guard, 1)
    source = source[:start] + block + source[end + 1:]

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
    if forbidden in new_guard:
        raise SystemExit("Phase 188 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 188: requires sustained supported native sprint state at the stable acceptance guard; fixture acceptance only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase189.py")), run_name="__main__")
