#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world run 33347367499 kept the bounded walk fixture grounded, broadphase-overlapping,
# and support-healthy from tick 15 through tick 28 after Phase190 removed the sibling discontinuity,
# but the existing +12 completion window ended before any material horizontal locomotion arrived.
# Phase166 already defines delayed fixture-pulse accounting through +20 ticks, and the known finite
# route reset is later than this bounded window. Align the walk completion deadline with that existing
# +20 observation bound. Harness-only: no player movement, carry vector, collision, train/world state,
# inventory, Create behavior, or VS2 physics mutation is introduced.

old = "if (player.tickCount <= phase154WalkStartTick + 12) {"
new = "if (player.tickCount <= phase154WalkStartTick + 20) {"
count = source.count(old)
if count != 1:
    raise SystemExit(f"Phase 191 expected exactly one final +12 walk observation bound, found {count}")
source = source.replace(old, new, 1)

required = [
    "phase166FixturePulseObservation",
    "player.tickCount <= phase154WalkStartTick + 20",
    "phase165WalkPathDistance >= 0.20",
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
print("Phase 191: extends only the fixture walk observation deadline to the existing Phase166 delayed-input bound")
