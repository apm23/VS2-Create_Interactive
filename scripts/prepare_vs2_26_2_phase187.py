#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #378 proved a one-tick handoff hole: at tick 33 the newly selected sibling
# carriage had strict support, broadphase, grounding, active contact motion and Phase161's bounded
# native-loss predicate was already true, but Phase150's support-reacquired de-dup clause still
# suppressed the final Phase85 replay. The player therefore missed exactly one 2.2045-block frame
# step and Phase85 recovered only at tick 35. Let the already-bounded Phase161 loss predicate bypass
# only that final native de-dup suppression. Phase85 remains the sole carry implementation and still
# uses Create-computed, Create-collision-filtered horizontal motion; no new vector or physics path.
#
# Phase132 legitimately places phase133ReplayGrace twice in this final guard: first in the physical-
# support widening and again at the tail of Phase150's native de-dup suppression. Phase184 may add
# more grouping around the support side. Therefore bind to the unique final Phase85 guard by replay-
# tick anchor and replace only the LAST phase133ReplayGrace occurrence, which is the de-dup tail.
replay_token = "carryReplayPlayerTick != player.tickCount"
replay_pos = source.find(replay_token)
if replay_pos < 0:
    raise SystemExit("Phase 187 could not locate final Phase85 replay-tick anchor")
if_pos = source.rfind("if (", 0, replay_pos)
if_end = source.find(") {", replay_pos)
if if_pos < 0 or if_end < 0:
    raise SystemExit("Phase 187 could not bound final Phase85 replay guard")
final_guard = source[if_pos:if_end + 3]
old_term = "phase133ReplayGrace"
new_term = "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"
if new_term not in final_guard:
    term_count = final_guard.count(old_term)
    if term_count < 2:
        raise SystemExit(f"Phase 187 expected support and de-dup Phase133 grace occurrences inside final Phase85 guard, found {term_count}")
    last_pos = final_guard.rfind(old_term)
    final_guard = final_guard[:last_pos] + new_term + final_guard[last_pos + len(old_term):]
    source = source[:if_pos] + final_guard + source[if_end + 3:]

required = [
    "phase161SupportedLocomotionNativeLoss",
    "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE181_FINAL_REPLAY_GUARD",
    "carryReplayPlayerTick != player.tickCount",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 187 lost bounded handoff-recovery anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in final_guard:
        raise SystemExit("Phase 187 introduced forbidden direct gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 187: lets already-bounded supported native-loss recovery survive Phase150 handoff de-dup; existing Create-filtered Phase85 carry only")
