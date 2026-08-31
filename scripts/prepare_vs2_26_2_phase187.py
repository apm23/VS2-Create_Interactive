#!/usr/bin/env python3
from pathlib import Path
import runpy

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
# Cumulative phases may regroup the final Phase85 boolean expression, so punctuation-based matching
# is intentionally avoided. Bind first to Phase150's unique support-reacquired identifier, then to
# the first Phase133 grace identifier following it before the final replay-tick predicate. That is
# the de-dup escape hatch Phase132 created; the separate physical-support grace occurs earlier.
anchor = "phase150SupportReacquired"
replay_token = "carryReplayPlayerTick != player.tickCount"
new_term = "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"

if new_term not in source:
    anchor_positions = []
    start = 0
    while True:
        pos = source.find(anchor, start)
        if pos < 0:
            break
        anchor_positions.append(pos)
        start = pos + len(anchor)

    replay_pos = source.find(replay_token)
    if replay_pos < 0:
        raise SystemExit("Phase 187 could not locate final Phase85 replay-tick anchor")

    candidates = []
    for anchor_pos in anchor_positions:
        if anchor_pos >= replay_pos:
            continue
        grace_pos = source.find("phase133ReplayGrace", anchor_pos + len(anchor), replay_pos)
        if grace_pos >= 0:
            candidates.append((anchor_pos, grace_pos))

    if not candidates:
        raise SystemExit("Phase 187 could not locate Phase133 de-dup grace after Phase150 reacquire anchor")

    # The final Phase85 guard is the Phase150 occurrence closest to the unique replay-tick predicate.
    anchor_pos, grace_pos = max(candidates, key=lambda pair: pair[0])
    source = source[:grace_pos] + new_term + source[grace_pos + len("phase133ReplayGrace"):]

required = [
    "phase161SupportedLocomotionNativeLoss",
    new_term,
    "phase150SupportReacquired",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE181_FINAL_REPLAY_GUARD",
    replay_token,
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 187 lost bounded handoff-recovery anchors: " + ", ".join(missing))

# Inspect only the rewritten predicate neighborhood. Phase187 changes predicate composition only;
# it must not add any direct player/world/train/physics mutation.
term_pos = source.index(new_term)
term_slice = source[max(0, term_pos - 1200):term_pos + len(new_term) + 1200]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in term_slice:
        raise SystemExit("Phase 187 found forbidden direct gameplay mutation near de-dup predicate: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 187: structurally widens only the Phase150 de-dup grace with already-bounded Phase161 recovery; existing Create-filtered Phase85 carry only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
