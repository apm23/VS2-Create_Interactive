#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

malformed = "&& && \n"
if malformed not in source:
    raise SystemExit("Phase 131 expected Phase130 malformed duplicate conjunction")

source = source.replace(malformed, "&& ", 1)

if "&& &&" in source:
    raise SystemExit("Phase 131 found another duplicate conjunction after repair")
if "!(productionSmoke && explicitCarryCompat)" not in source:
    raise SystemExit("Phase 131 lost production carry replay suppression predicate")
if "carryReplayPlayerTick != player.tickCount" not in source:
    raise SystemExit("Phase 131 lost original replay tick predicate")

client_probe.write_text(source, encoding="utf-8")
print("Phase 131: repaired Phase130 duplicate conjunction while preserving replay suppression and tick predicate")
