#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Keep the carry baseline attached to the carriage Create itself currently applies to the player.
# Run #570 proves that after supported locomotion the old baseline can remain on carriage 5 while
# Create's native contact application becomes uniquely owned by sibling carriage 4, followed by 2;
# the stale frame then diverges by tens of blocks even though Create continues producing native
# contact motion. Prefer strict physical-support handoff as before. Additionally permit a baseline
# identity rebase when the candidate sibling has a native contact application this exact tick and
# the old baseline does not. This changes only frame identity/bookkeeping: it never applies motion,
# teleports, sets velocity, alters collision response, or mutates train/world state.
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
        f'{replay_indent}boolean phase133CurrentBaselineStrictSupport = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}    && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround();\n'
        f'{replay_indent}if (phase133CurrentBaselineStrictSupport) {{\n'
        f'{replay_indent}    System.setProperty("vs2.phase133BaselineSupportTick", Integer.toString(player.tickCount));\n'
        f'{replay_indent}    System.setProperty("vs2.phase133BaselineSupportCarriageId", Integer.toString(carriage.getId()));\n'
        f'{replay_indent}}}\n'
        f'{replay_indent}boolean phase133PreviousBaselineSupportLease = carryBaselineCaptured\n'
        f'{replay_indent}    && Integer.toString(carryBaselineCarriageId).equals(System.getProperty("vs2.phase133BaselineSupportCarriageId"))\n'
        f'{replay_indent}    && Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase133BaselineSupportTick"));\n'
        f'{replay_indent}boolean phase133CandidateNativeAppliedNow = Integer.toString(player.tickCount).equals(\n'
        f'{replay_indent}    System.getProperty("vs2.phase170NativeContactApplicationTick." + carriage.getId()));\n'
        f'{replay_indent}boolean phase133BaselineNativeAppliedNow = carryBaselineCaptured && Integer.toString(player.tickCount).equals(\n'
        f'{replay_indent}    System.getProperty("vs2.phase170NativeContactApplicationTick." + carryBaselineCarriageId));\n'
        f'{replay_indent}boolean phase133SoleNativeOwner = carryBaselineCaptured\n'
        f'{replay_indent}    && carryBaselineCarriageId != carriage.getId()\n'
        f'{replay_indent}    && phase133CandidateNativeAppliedNow && !phase133BaselineNativeAppliedNow;\n'
        f'{replay_indent}boolean phase136SupportedSiblingHandoff = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId != carriage.getId()\n'
        f'{replay_indent}    && (!phase133PreviousBaselineSupportLease || phase133SoleNativeOwner)\n'
        f'{replay_indent}    && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{replay_indent}    && (phase81PhysicalSupport || phase133SoleNativeOwner)\n'
        f'{replay_indent}    && carryBaselineRebaseTick != player.tickCount;\n'
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
        f'{replay_indent}        "GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE previous_carriage_id={{}} carriage_id={{}} player_tick={{}} physical_support={{}} native_contact_owner={{}} collision_eligible=true broadphase=true on_ground=true previous_baseline_support_lease={{}} settle_one_tick=true identity_only=true",\n'
        f'{replay_indent}        phase136PreviousCarriageId, carriage.getId(), player.tickCount, phase81PhysicalSupport,\n'
        f'{replay_indent}        phase133SoleNativeOwner, phase133PreviousBaselineSupportLease);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + handoff + source[replay_if_pos:]

required = [
    "GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE",
    "phase133CurrentBaselineStrictSupport",
    "vs2.phase133BaselineSupportTick",
    "vs2.phase133BaselineSupportCarriageId",
    "phase133PreviousBaselineSupportLease",
    "phase133CandidateNativeAppliedNow",
    "phase133BaselineNativeAppliedNow",
    "phase133SoleNativeOwner",
    "vs2.phase170NativeContactApplicationTick.",
    "carryBaselineCarriageId != carriage.getId()",
    "(!phase133PreviousBaselineSupportLease || phase133SoleNativeOwner)",
    "(phase81PhysicalSupport || phase133SoleNativeOwner)",
    "carryBaselineRebaseTick != player.tickCount",
    "carryBaselineCarriageId = carriage.getId()",
    "carryBaselineRebaseTick = player.tickCount",
    "carryDeltaReported = false",
    "native_contact_owner={}",
    "identity_only=true",
    "settle_one_tick=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 133 lost native-owner sibling handoff anchors: " + ", ".join(missing))

marker_pos = source.index("GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE")
handoff_slice = source[max(0, marker_pos - 4200):marker_pos + 1600]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    ".put(", ".remove(", "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in handoff_slice:
        raise SystemExit("Phase 133 found forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 133: rebases frame identity to a sole native Create contact owner without synthesizing movement")
