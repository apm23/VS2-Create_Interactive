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
# Production-world #494 then failed before Minecraft because Phase129's acquisition bound was
# intentionally reduced from 48 to 32 after Run 493 proved earlier native support. Phase129 now
# also stops acquisition as soon as Create captures the native carriage baseline. Preserve that
# stricter ownership boundary and add only the existing walk-start freeze. This changes only the
# disposable test fixture; it does not change production carry, player movement, Create collision,
# train state, world state, or VS2 physics.

old_retry = '''|| (productionSmokeFixture && !carryBaselineCaptured && fixtureContactAcquireTicks < 32)) {'''
new_retry = '''|| (productionSmokeFixture && !carryBaselineCaptured && fixtureContactAcquireTicks < 32 && !phase154WalkStarted)) {'''
if "!carryBaselineCaptured && fixtureContactAcquireTicks < 32 && !phase154WalkStarted" not in source:
    if source.count(old_retry) != 1:
        raise SystemExit("Phase 162 expected exactly one current Phase129 native-baseline bounded fixture retry guard")
    source = source.replace(old_retry, new_retry, 1)

old_count = '''if (productionSmokeFixture && !carryBaselineCaptured && fixtureContactAcquireTicks < 32) {
        fixtureContactAcquireTicks++;'''
new_count = '''if (productionSmokeFixture && !carryBaselineCaptured && fixtureContactAcquireTicks < 32 && !phase154WalkStarted) {
        fixtureContactAcquireTicks++;'''
if old_count in source:
    source = source.replace(old_count, new_count, 1)

required = [
    "phase154WalkStarted",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_FIXTURE_CONTACT_ACQUIRE",
    "!carryBaselineCaptured && fixtureContactAcquireTicks < 32 && !phase154WalkStarted",
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
print("Phase 162: freezes fixture acquisition on native baseline capture or bounded walk start at the current 32-attempt bound")
