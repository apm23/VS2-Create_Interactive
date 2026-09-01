#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase162 owns only one boundary: once bounded walking starts, the disposable fixture must
# stop acquisition. Phase129 owns the earlier acquisition/ownership predicate, which has changed
# as real-train evidence improved. Preserve that predicate structurally instead of hard-coding
# whether acquisition currently keys off baseline capture or a stronger native-carry condition.
# No player motion, collision response, train state, world state, or VS2 physics is changed here.
if "fixtureContactAcquireTicks < 32 && !phase154WalkStarted" not in source:
    retry_pattern = re.compile(
        r'(?P<prefix>\|\| \(productionSmokeFixture && )(?P<owned>[^\n)]*fixtureContactAcquireTicks < 32)(?P<suffix>\)\) \{)'
    )
    retry_match = retry_pattern.search(source)
    if retry_match is None:
        raise SystemExit("Phase 162 could not locate current Phase129 bounded fixture retry guard")
    owned = retry_match.group("owned")
    source = source[:retry_match.start()] + (
        retry_match.group("prefix") + owned + " && !phase154WalkStarted" + retry_match.group("suffix")
    ) + source[retry_match.end():]

    count_pattern = re.compile(
        r'(?P<prefix>if \(productionSmokeFixture && )(?P<owned>[^\n)]*fixtureContactAcquireTicks < 32)(?P<suffix>\) \{\n\s*fixtureContactAcquireTicks\+\+;)'
    )
    count_match = count_pattern.search(source)
    if count_match is None:
        raise SystemExit("Phase 162 could not locate current Phase129 acquisition counter guard")
    owned = count_match.group("owned")
    source = source[:count_match.start()] + (
        count_match.group("prefix") + owned + " && !phase154WalkStarted" + count_match.group("suffix")
    ) + source[count_match.end():]

required = [
    "phase154WalkStarted",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_FIXTURE_CONTACT_ACQUIRE",
    "fixtureContactAcquireTicks < 32 && !phase154WalkStarted",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 162 lost walk/fixture isolation anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in "fixtureContactAcquireTicks < 32 && !phase154WalkStarted":
        raise SystemExit("Phase 162 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 162: preserves Phase129 ownership semantics and adds only the bounded walk-start acquisition freeze")
