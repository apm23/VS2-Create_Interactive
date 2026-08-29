#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #82 exposed a concrete sibling-carriage frame discontinuity:
# support handed off from carriage 8 to 10 and, one tick later, the otherwise
# Create-computed/filtered carry vector jumped to (-5.5076, 0, +4.0), immediately
# throwing the fixture off support. Do not clamp or synthesize motion. Instead, make
# the compatibility replay wait until the newly selected carriage identity has been
# stable for two LocalPlayer ticks after the existing Phase 71 baseline rebase.
# This preserves Create's own motion/collision result and only rejects a transient
# cross-entity handoff frame.
field_anchor = '''    private static int carryBaselineCarriageId = Integer.MIN_VALUE;\n'''
field_replacement = field_anchor + '''    private static int carryBaselineRebaseTick = Integer.MIN_VALUE;\n'''
if "carryBaselineRebaseTick" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 108 could not find Phase 71 carriage baseline field")
    source = source.replace(field_anchor, field_replacement, 1)

rebase_anchor = '''                        carryBaselineCarriageId = carriage.getId();\n                        carryPlayerX = player.getX();'''
rebase_replacement = '''                        carryBaselineCarriageId = carriage.getId();\n                        carryBaselineRebaseTick = player.tickCount;\n                        carryPlayerX = player.getX();'''
if "carryBaselineRebaseTick = player.tickCount" not in source:
    if rebase_anchor not in source:
        raise SystemExit("Phase 108 could not find Phase 71 sibling-carriage rebase assignment")
    source = source.replace(rebase_anchor, rebase_replacement, 1)

guard_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
guard_replacement = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryBaselineCarriageId == carriage.getId()\n                && (carryBaselineRebaseTick == Integer.MIN_VALUE || player.tickCount - carryBaselineRebaseTick >= 2)\n                && carryReplayPlayerTick != player.tickCount'''
if "player.tickCount - carryBaselineRebaseTick >= 2" not in source:
    if guard_anchor not in source:
        raise SystemExit("Phase 108 could not find Phase 85 carry replay guard")
    source = source.replace(guard_anchor, guard_replacement, 1)

log_anchor = '''                        LOGGER.info(\n                            "GATE_E_CLIENT_CARRY_REBASE previous_carriage_id={} current_carriage_id={} player_tick={} contact={} on_ground={}",'''
log_replacement = '''                        LOGGER.info(\n                            "GATE_E_PHASE108_HANDOFF_SETTLE previous_carriage_id={} current_carriage_id={} player_tick={} settle_ticks=2",\n                            carryBaselineCarriageId, carriage.getId(), player.tickCount);\n                        LOGGER.info(\n                            "GATE_E_CLIENT_CARRY_REBASE previous_carriage_id={} current_carriage_id={} player_tick={} contact={} on_ground={}",'''
if "GATE_E_PHASE108_HANDOFF_SETTLE" not in source:
    if log_anchor not in source:
        raise SystemExit("Phase 108 could not find Phase 71 rebase log anchor")
    source = source.replace(log_anchor, log_replacement, 1)

required = [
    'carryBaselineRebaseTick',
    'carryBaselineRebaseTick = player.tickCount',
    'carryBaselineCarriageId == carriage.getId()',
    'player.tickCount - carryBaselineRebaseTick >= 2',
    'GATE_E_PHASE108_HANDOFF_SETTLE',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 108 lost sibling-handoff settle anchors: " + ", ".join(missing))

# Explicitly reject motion fabrication/clamping in this phase.
for forbidden in ['Math.min(', 'Math.max(', 'clamp(', 'setPos(', 'setDeltaMovement(', 'new Vec3(']:
    if forbidden in guard_replacement:
        raise SystemExit("Phase 108 found forbidden motion workaround: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 108: delayed Create-filtered carry replay for two ticks after sibling-carriage baseline handoff; no vector clamp, teleport, train control, or VS2 physics change")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase105.py")), run_name="__main__")
