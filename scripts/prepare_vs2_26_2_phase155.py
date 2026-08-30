#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #270 proved the 20-tick walk starts stable on carriage 8, then the
# compatibility replay later fires for stale sibling carriage 7 after the active carry
# baseline has already rebased to carriage 5. Those stale replay vectors directly precede
# large carriage-local jumps and loss of broadphase. Keep the existing Create-computed,
# Create-collision-filtered replay, but require its carriage to still own the active carry
# baseline. This removes stale sibling application without inventing a carry vector,
# teleporting the player, changing collision response, or touching train/VS2 physics.
old = "carryReplayPlayerTick != player.tickCount"
new = "carryBaselineCarriageId == carriage.getId()\n                            && carryReplayPlayerTick != player.tickCount"
count = source.count(old)
if new not in source:
    if count != 1:
        raise SystemExit(f"Phase 155 expected exactly one final carry replay predicate, found {count}")
    source = source.replace(old, new, 1)

required = [
    "GATE_E_PHASE85_CARRY_REPLAY",
    "carryBaselineCarriageId == carriage.getId()",
    "carryReplayPlayerTick != player.tickCount",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 155 lost stale-sibling replay guard anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 155: blocks stale sibling-carriage compatibility replay after active-baseline handoff; existing Create-filtered carry remains authoritative")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase156.py")), run_name="__main__")
