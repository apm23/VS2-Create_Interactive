#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world run 33348083330 started the bounded walk on carriage 2 at tick 17 after the
# existing three-tick settled predicate, then the end-tick local frame jumped 6.998 blocks at tick
# 18 and support became unhealthy. The following carriage 4 interval lasted only ticks 19-22 before
# another handoff. These are short-lived fixture frame windows, not evidence for a new physics
# correction. Require five consecutive ready ticks and four ticks since the most recent baseline
# rebase before pressing the disposable forward key. This changes fixture timing only: no player
# movement, carry vector, collision, train/world state, inventory, Create behavior, or VS2 physics.

old_age = "player.tickCount - carryBaselineRebaseTick >= 2"
new_age = "player.tickCount - carryBaselineRebaseTick >= 4"
if new_age not in source:
    count = source.count(old_age)
    if count != 1:
        raise SystemExit(f"Phase 192 expected one Phase185 rebase-age guard, found {count}")
    source = source.replace(old_age, new_age, 1)

old_ready = "phase185WalkReadyTicks >= 3"
new_ready = "phase185WalkReadyTicks >= 5"
if new_ready not in source:
    count = source.count(old_ready)
    if count != 1:
        raise SystemExit(f"Phase 192 expected one Phase185 ready-tick guard, found {count}")
    source = source.replace(old_ready, new_ready, 1)

required = [
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "phase185WalkReadyCarriageId == phase154Carriage.getId()",
    "phase185WalkReadyTicks >= 5",
    "player.tickCount - carryBaselineRebaseTick >= 4",
    "phase81PhysicalSupport",
    "phase185FreshNativeEvidence",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 192 lost settled-frame fixture anchors: " + ", ".join(missing))

inserted = new_age + new_ready
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 192 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 192: delays only disposable walk input until five consecutive settled supported/native ticks and four ticks after rebase")
