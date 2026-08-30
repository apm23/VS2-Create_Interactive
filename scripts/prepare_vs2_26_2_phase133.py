#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #191 proved an exact 1:1 carry interval on carriage 7, followed by
# sustained strict physical support on sibling carriage 2 while the carry baseline stayed
# pinned to carriage 7. Phase85 already owns the Create-computed, Create-collision-filtered
# carry vector; this phase only transfers baseline identity/coordinates to the currently
# supported sibling so the existing replay path can resume after Phase108's one-tick settle.
# No player position, velocity, world, train-control, or VS2 physics mutation is introduced.
if "GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE" not in source:
    replay_tick_token = "carryReplayPlayerTick != player.tickCount"
    replay_tick_pos = source.find(replay_tick_token)
    if replay_tick_pos < 0 or source.find(replay_tick_token, replay_tick_pos + 1) >= 0:
        raise SystemExit("Phase 133 expected one final Phase85 replay tick predicate")

    search_start = max(0, replay_tick_pos - 9000)
    prefix = source[search_start:replay_tick_pos]
    candidates = list(re.finditer(r'(?m)^(?P<indent>[ \t]*)if \(', prefix))
    replay_if_pos = None
    replay_indent = None
    for candidate in reversed(candidates):
        absolute = search_start + candidate.start()
        segment = source[absolute:replay_tick_pos]
        if "phase81PhysicalSupport" in segment and "collisionEligible" in segment:
            replay_if_pos = absolute
            replay_indent = candidate.group("indent")
            break
    if replay_if_pos is None or replay_indent is None:
        raise SystemExit("Phase 133 could not locate final Phase85 replay guard")

    handoff = (
        f'{replay_indent}boolean phase136SupportedSiblingHandoff = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId != carriage.getId()\n'
        f'{replay_indent}    && phase81PhysicalSupport && collisionEligible && broadphaseOverlap\n'
        f'{replay_indent}    && player.onGround() && carryBaselineRebaseTick != player.tickCount;\n'
        f'{replay_indent}if (phase136SupportedSiblingHandoff) {{\n'
        f'{replay_indent}    int phase136PreviousCarriageId = carryBaselineCarriageId;\n'
        f'{replay_indent}    carryBaselineCarriageId = carriage.getId();\n'
        f'{replay_indent}    carryBaselineRebaseTick = player.tickCount;\n'
        f'{replay_indent}    carryPlayerX = player.getX();\n'
        f'{replay_indent}    carryPlayerY = player.getY();\n'
        f'{replay_indent}    carryPlayerZ = player.getZ();\n'
        f'{replay_indent}    carryCarriageX = carriage.getX();\n'
        f'{replay_indent}    carryCarriageY = carriage.getY();\n'
        f'{replay_indent}    carryCarriageZ = carriage.getZ();\n'
        f'{replay_indent}    carryDeltaReported = false;\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE previous_carriage_id={{}} carriage_id={{}} player_tick={{}} physical_support=true collision_eligible=true broadphase=true on_ground=true settle_one_tick=true",\n'
        f'{replay_indent}        phase136PreviousCarriageId, carriage.getId(), player.tickCount);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + handoff + source[replay_if_pos:]

required = [
    "GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE",
    "carryBaselineCarriageId != carriage.getId()",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap",
    "carryBaselineRebaseTick != player.tickCount",
    "carryBaselineCarriageId = carriage.getId()",
    "carryBaselineRebaseTick = player.tickCount",
    "carryDeltaReported = false",
    "settle_one_tick=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 133 lost supported-sibling handoff anchors: " + ", ".join(missing))

marker_pos = source.index("GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE")
handoff_slice = source[max(0, marker_pos - 2200):marker_pos + 1200]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(",
    ".put(", ".remove(", "setSchedule", "setTrain", "setVelocity",
]:
    if forbidden in handoff_slice:
        raise SystemExit("Phase 133 found forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 133: rebases carry baseline only to a sibling carriage with proven strict physical support; existing Create-filtered carry remains authoritative")
