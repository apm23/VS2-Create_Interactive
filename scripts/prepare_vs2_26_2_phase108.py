#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #158 exposed a concrete one-tick sibling-carriage carry dead zone:
# after Phase 71 rebased onto a new carriage, the previous two-tick settle guard withheld
# Create's already-computed and collision-filtered carry at rebase_age=1, producing visible
# relative drift; the same carry path reached drift_sq=0.0 as soon as it was allowed at
# rebase_age=2. Keep one rebase tick to avoid the original same-tick frame discontinuity,
# but allow replay on the following LocalPlayer tick. No clamp, synthetic vector, teleport,
# train control, or VS2 physics change is introduced.
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

# Later phases have evolved the beginning of the replay if-condition several times.
# Anchor on the unique per-tick replay term instead of assuming the preceding guard
# text is byte-for-byte identical.
replay_tick = '''                && carryReplayPlayerTick != player.tickCount'''
settled_replay_tick = '''                && carryBaselineCarriageId == carriage.getId()\n                && (carryBaselineRebaseTick == Integer.MIN_VALUE || player.tickCount - carryBaselineRebaseTick >= 1)\n                && carryReplayPlayerTick != player.tickCount'''
if "player.tickCount - carryBaselineRebaseTick >= 1" not in source:
    count = source.count(replay_tick)
    if count != 1:
        raise SystemExit(f"Phase 108 expected one carry replay tick anchor, found {count}")
    source = source.replace(replay_tick, settled_replay_tick, 1)

log_anchor = '''                        LOGGER.info(\n                            "GATE_E_CLIENT_CARRY_REBASE previous_carriage_id={} current_carriage_id={} player_tick={} contact={} on_ground={}",'''
log_replacement = '''                        LOGGER.info(\n                            "GATE_E_PHASE108_HANDOFF_SETTLE previous_carriage_id={} current_carriage_id={} player_tick={} settle_ticks=1",\n                            carryBaselineCarriageId, carriage.getId(), player.tickCount);\n                        LOGGER.info(\n                            "GATE_E_CLIENT_CARRY_REBASE previous_carriage_id={} current_carriage_id={} player_tick={} contact={} on_ground={}",'''
if "GATE_E_PHASE108_HANDOFF_SETTLE" not in source:
    if log_anchor not in source:
        raise SystemExit("Phase 108 could not find Phase 71 rebase log anchor")
    source = source.replace(log_anchor, log_replacement, 1)

required = [
    'carryBaselineRebaseTick',
    'carryBaselineRebaseTick = player.tickCount',
    'carryBaselineCarriageId == carriage.getId()',
    'player.tickCount - carryBaselineRebaseTick >= 1',
    'GATE_E_PHASE108_HANDOFF_SETTLE',
    'GATE_E_PHASE85_CARRY_REPLAY',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 108 lost sibling-handoff settle anchors: " + ", ".join(missing))

for forbidden in ['Math.min(', 'Math.max(', 'clamp(', 'setPos(', 'setDeltaMovement(', 'new Vec3(']:
    if forbidden in settled_replay_tick:
        raise SystemExit("Phase 108 found forbidden motion workaround: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 108: permits Create-filtered carry on the first tick after sibling-carriage rebase; no vector clamp, teleport, train control, or VS2 physics change")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase105.py")), run_name="__main__")

# Phase 104 rewrites the local-frame synchronization block installed by Phase 100.
# world/client smoke can reach Phase 108 without production-world's later explicit
# Phase 98 pass, so install only Phase 100's prerequisite edits here and suppress its
# descendant chain to avoid a 100 -> 101 -> ... -> 108 recursion cycle.
runpy.run_path(
    str(Path(__file__).with_name("prepare_vs2_26_2_phase100.py")),
    init_globals={"PHASE100_PREREQUISITE_ONLY": True},
    run_name="__main__",
)

# Phase 104 then installs the exact-carriage resolver, chains Phase 106, and advances
# into Phase 109+ with all prerequisites present.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase104.py")), run_name="__main__")
