#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #272 proved the extended walk can legitimately transfer the active
# carry baseline across sibling Create carriage entities (5 -> 4 -> 2) while remaining
# grounded and broadphase-supported. Phase154 treated any carriage-id change as immediate
# failure, which conflates valid train-internal handoff with actual drift. Make the proof
# handoff-aware, but keep it strict: reset the local-step baseline only on the exact tick
# where Phase133 has rebased carryBaselineCarriageId, and reject any same-frame local step
# above 0.75 blocks/tick. Run #272 already showed ~2.61-block same-frame steps after handoff,
# so this does not hide the real carry-loss. Fixture/gate logic only; no gameplay mutation.
old = '''                            if (phase154Carriage.getId() != phase154WalkCarriageId || !phase154SupportNow) {
                                phase154WalkSupportHealthy = false;
                            }
                            double phase154Step = phase154WalkPreviousLocal == null
                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);
                            phase154WalkPreviousLocal = phase154Local;
'''
new = '''                            boolean phase156SiblingHandoff = phase154Carriage.getId() != phase154WalkCarriageId
                                && phase154Carriage.getId() == carryBaselineCarriageId
                                && carryBaselineRebaseTick == player.tickCount
                                && phase154SupportNow;
                            double phase154Step = phase154WalkPreviousLocal == null || phase156SiblingHandoff
                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);
                            if (phase156SiblingHandoff) {
                                LOGGER.info(
                                    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF player_tick={} previous_carriage_id={} carriage_id={} grounded={} broadphase={} baseline_rebase=true local_step_reset=true fixture_only=true",
                                    player.tickCount, phase154WalkCarriageId, phase154Carriage.getId(), player.onGround(), phase154Broadphase);
                                phase154WalkCarriageId = phase154Carriage.getId();
                            }
                            if (!phase154SupportNow || phase154Step > 0.75) {
                                phase154WalkSupportHealthy = false;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE156_WALK_FRAME_GUARD player_tick={} carriage_id={} local_step={} max_local_step=0.75 support_now={} sibling_handoff={} support_healthy={} read_only=true",
                                player.tickCount, phase154Carriage.getId(), phase154Step, phase154SupportNow,
                                phase156SiblingHandoff, phase154WalkSupportHealthy);
                            phase154WalkPreviousLocal = phase154Local;
'''
if "GATE_E_PHASE156_WALK_FRAME_GUARD" not in source:
    if old not in source:
        raise SystemExit("Phase 156 could not find Phase154 walk support guard")
    source = source.replace(old, new, 1)

required = [
    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF",
    "GATE_E_PHASE156_WALK_FRAME_GUARD",
    "carryBaselineRebaseTick == player.tickCount",
    "phase154Step > 0.75",
    "phase154WalkCarriageId = phase154Carriage.getId()",
    "local_step_reset=true",
    "max_local_step=0.75",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 156 lost handoff-aware walk anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in new:
        raise SystemExit("Phase 156 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 156: extended walk proof accepts strict supported sibling handoff but rejects >0.75-block same-frame drift; no gameplay/physics mutation")
