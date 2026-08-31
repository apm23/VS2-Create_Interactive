#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #389 proves the sampled-input fixture produces real horizontal locomotion
# while grounded/broadphase-supported at tick 41, then the finite saved route resets the same
# carriage frame at tick 42. Complete the disposable walk proof as soon as material horizontal
# locomotion has been observed after at least one full input-sampling interval, before that known
# route discontinuity can poison the verifier. This only changes fixture completion timing; it
# does not alter player motion, carry vectors, collision, train/world state, or VS2/Create physics.
old = """                            if (player.tickCount <= phase154WalkStartTick + 12) {\n"""
new = """                            boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 2
                                && phase154WalkSupportHealthy
                                && phase154Carriage.getId() == phase154WalkCarriageId
                                && phase154Broadphase && player.onGround()
                                && phase165WalkPathDistance >= 0.20 && phase165WalkPathDistance <= 4.00
                                && phase154WalkStartLocal != null
                                && Math.hypot(
                                    phase154Local.x - phase154WalkStartLocal.x,
                                    phase154Local.z - phase154WalkStartLocal.z) >= 0.20
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
    "player.tickCount >= phase154WalkStartTick + 2",
    "phase154WalkSupportHealthy",
    "phase165WalkPathDistance >= 0.20",
    "Math.hypot(",
    "phase154Local.x - phase154WalkStartLocal.x",
    "phase154Local.z - phase154WalkStartLocal.z",
    "if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady)",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 188 lost pre-reset walk-proof anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in new:
        raise SystemExit("Phase 188 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 188: completes bounded walk after material supported horizontal locomotion before the finite-route reset; fixture timing only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase189.py")), run_name="__main__")
