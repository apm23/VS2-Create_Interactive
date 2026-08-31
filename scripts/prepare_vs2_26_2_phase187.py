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
# Phase132 constructs the final Phase150 tail explicitly. Later phases may add predicates/grouping to
# the support side of the Phase85 guard, so deriving the whole guard from a nearby "if (" is brittle.
# Bind directly to the unique Phase150 de-dup tail that Phase132 itself requires, and widen only its
# bounded Phase133 escape hatch. This cannot accidentally touch the separate physical-support widening.
old_tail = "|| phase150SupportReacquired)) || phase133ReplayGrace)"
new_tail = "|| phase150SupportReacquired)) || (phase133ReplayGrace || phase161SupportedLocomotionNativeLoss))"

if new_tail not in source:
    tail_count = source.count(old_tail)
    if tail_count != 1:
        raise SystemExit(f"Phase 187 expected exactly one Phase150/Phase133 de-dup tail, found {tail_count}")
    source = source.replace(old_tail, new_tail, 1)

required = [
    "phase161SupportedLocomotionNativeLoss",
    new_tail,
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE181_FINAL_REPLAY_GUARD",
    "carryReplayPlayerTick != player.tickCount",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 187 lost bounded handoff-recovery anchors: " + ", ".join(missing))

# Inspect only the rewritten de-dup neighborhood for forbidden direct mutations. Phase187 changes
# predicate composition only; it must not add any player/world/train/physics action.
tail_pos = source.index(new_tail)
tail_slice = source[max(0, tail_pos - 1200):tail_pos + len(new_tail) + 1200]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in tail_slice:
        raise SystemExit("Phase 187 found forbidden direct gameplay mutation near de-dup tail: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 187: widens only the Phase150 de-dup tail with already-bounded Phase161 recovery; existing Create-filtered Phase85 carry only")
