#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #307 proved pinning the walk telemetry to its start carriage is itself
# wrong once Create legitimately transfers the player's active support to a sibling carriage.
# The fixture started on carriage 5, while carry telemetry later showed carriage 4 remained
# grounded/contact-valid. Measuring against stale carriage 5 then produced multi-block local
# jumps even after the single movement-key pulse had been released. Follow the active
# carryBaseline carriage again, but make the Phase156 local-frame reset handoff-aware whenever
# the newly selected baseline has current broadphase+ground support. This is telemetry/test
# accounting only; production carry selection, collision response, player motion, train/world
# state and VS2 physics remain untouched.
old_handoff = '''                            boolean phase156SiblingHandoff = phase154Carriage.getId() != phase154WalkCarriageId
                                && phase154Carriage.getId() == carryBaselineCarriageId
                                && carryBaselineRebaseTick == player.tickCount
                                && phase154SupportNow;'''
new_handoff = '''                            boolean phase156SiblingHandoff = phase154Carriage.getId() != phase154WalkCarriageId
                                && phase154Carriage.getId() == carryBaselineCarriageId
                                && phase154SupportNow;'''
if "phase163SupportedActiveHandoff" not in source:
    if source.count(old_handoff) != 1:
        raise SystemExit("Phase 163 expected exactly one Phase156 sibling-handoff guard")
    source = source.replace(old_handoff, new_handoff, 1)
    source = source.replace(
        '''                                    player.tickCount, phase154WalkCarriageId, phase154Carriage.getId(), player.onGround(), phase154Broadphase);''',
        '''                                    player.tickCount, phase154WalkCarriageId, phase154Carriage.getId(), player.onGround(), phase154Broadphase);\n                                boolean phase163SupportedActiveHandoff = true;''',
        1,
    )

required = [
    "phase163SupportedActiveHandoff",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "&& phase154SupportNow;",
    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF",
    "phase154WalkCarriageId = phase154Carriage.getId()",
    "local_step_reset=true",
    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 163 lost supported active-carriage walk anchors: " + ", ".join(missing))
if "phase163WalkMeasurementCarriageId" in source:
    raise SystemExit("Phase 163 unexpectedly retained stale pinned-carriage measurement")

patch_text = new_handoff + "phase163SupportedActiveHandoff"
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 163 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 163: follows the supported active carry-baseline carriage and resets walk-local telemetry on sibling handoff")
