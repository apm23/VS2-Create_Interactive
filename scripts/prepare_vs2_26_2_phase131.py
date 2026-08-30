#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

if "&& &&" in source:
    raise SystemExit("Phase 131 found duplicate conjunction after Phase130")
if "!(productionSmoke && explicitCarryCompat)" not in source:
    raise SystemExit("Phase 131 lost production carry replay suppression predicate")
if "carryReplayPlayerTick != player.tickCount" not in source:
    raise SystemExit("Phase 131 lost original replay tick predicate")

print("Phase 131: validated Phase130 replay suppression syntax and preserved tick predicate")
