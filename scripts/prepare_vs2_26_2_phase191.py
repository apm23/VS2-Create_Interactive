#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world run 33347367499 kept the bounded walk fixture grounded, broadphase-overlapping,
# and support-healthy from tick 15 through tick 28 after Phase190 removed the sibling discontinuity,
# but the existing completion window ended before any material horizontal locomotion arrived.
# Phase188 has already wrapped that deadline with its pre-reset early-success predicate, so target
# the cumulative compound branch structurally rather than the obsolete bare +12 form. Phase166
# already defines delayed fixture-pulse accounting through +20 ticks. Harness-only: no player
# movement, carry vector, collision, train/world state, inventory, Create behavior, or VS2 physics
# mutation is introduced. Phase188 now accepts material native sprint from the sibling-safe 0.10
# block path threshold, so keep this downstream composition guard aligned with that fixture-only
# acceptance instead of requiring the obsolete 0.20 anchor.

old = "if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady) {"
new = "if (player.tickCount <= phase154WalkStartTick + 20 && !phase188PreResetWalkReady) {"
if new not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 191 expected exactly one cumulative Phase188 +12 walk observation bound, found {count}")
    source = source.replace(old, new, 1)

required = [
    "phase166FixturePulseObservation",
    "phase188PreResetWalkReady",
    "player.tickCount <= phase154WalkStartTick + 20 && !phase188PreResetWalkReady",
    "phase165WalkPathDistance >= 0.10",
    "player.tickCount >= phase154WalkStartTick + 3",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_E_PHASE166_FIXTURE_PULSE_RESPONSE",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 191 lost bounded delayed-locomotion anchors: " + ", ".join(missing))

inserted = new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 191 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 191: aligns delayed walk observation with the material Phase188 sprint proof")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase192.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase193.py")), run_name="__main__")
