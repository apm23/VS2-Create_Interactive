#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #298 proved the movement failure was contaminated by the smoke harness:
# the twenty-tick walk began on strict supported carriage 8 at tick 33, but Phase129's bounded
# fixture-acquisition loop was still active and performed another fixture reposition at tick 34,
# selecting carriage 4. The next walk sample therefore measured the now-distant carriage-8 frame
# as a 51.7-block local jump. Stop fixture contact acquisition once the walk proof has started.
# Production-world #334 required extending Phase129's bounded acquisition window from 32 to 48
# attempts because genuine strict support arrived late. Keep this guard aligned with that bound.
# This only disables further test-fixture repositioning; it does not change production carry,
# player movement, Create collision, train state, world state, or VS2 physics.

old_retry = '''|| (productionSmokeFixture && fixtureContactAcquireTicks < 48)) {'''
new_retry = '''|| (productionSmokeFixture && fixtureContactAcquireTicks < 48 && !phase154WalkStarted)) {'''
if "fixtureContactAcquireTicks < 48 && !phase154WalkStarted" not in source:
    if source.count(old_retry) != 1:
        raise SystemExit("Phase 162 expected exactly one Phase129 bounded fixture retry guard")
    source = source.replace(old_retry, new_retry, 1)

old_count = '''if (productionSmokeFixture && fixtureContactAcquireTicks < 48) {
        fixtureContactAcquireTicks++;'''
new_count = '''if (productionSmokeFixture && fixtureContactAcquireTicks < 48 && !phase154WalkStarted) {
        fixtureContactAcquireTicks++;'''
if old_count in source:
    source = source.replace(old_count, new_count, 1)

required = [
    "phase154WalkStarted",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_FIXTURE_CONTACT_ACQUIRE",
    "fixtureContactAcquireTicks < 48 && !phase154WalkStarted",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 162 lost walk/fixture isolation anchors: " + ", ".join(missing))

patch_text = new_retry + new_count
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 162 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 162: freezes fixture contact acquisition once the bounded walk proof starts")
