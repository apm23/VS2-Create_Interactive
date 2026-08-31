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
# Runs #380-#406 showed that reconstructing the complete historical Phase132 expression is brittle:
# later phases have legitimately reshaped the surrounding de-dup condition, so the exact Phase132
# string no longer exists by Phase187. Bind instead to the final scalar phase133ReplayGrace token
# immediately before the unique Phase85 replay-tick predicate. Phase181 telemetry is inserted before
# the replay guard, so selecting the last grace token before the replay predicate explicitly skips
# that LOGGER argument while remaining agnostic to harmless surrounding formatting/evolution.
replay_token = "carryReplayPlayerTick != player.tickCount"
old_term = "phase133ReplayGrace"
new_term = "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"
telemetry_marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"

replay_count = source.count(replay_token)
if replay_count != 1:
    raise SystemExit(f"Phase 187 expected one final Phase85 replay-tick anchor, found {replay_count}")
replay_pos = source.index(replay_token)

telemetry_pos = source.find(telemetry_marker)
if telemetry_pos < 0 or telemetry_pos >= replay_pos:
    raise SystemExit("Phase 187 expected Phase181 telemetry immediately before the final replay guard")

prefix = source[:replay_pos]
if new_term not in prefix:
    grace_pos = prefix.rfind(old_term)
    if grace_pos < 0:
        raise SystemExit("Phase 187 could not find final Phase133 replay-grace token before replay predicate")
    if grace_pos <= telemetry_pos:
        raise SystemExit("Phase 187 final replay-grace candidate did not occur after Phase181 telemetry marker")
    if replay_pos - grace_pos > 6000:
        raise SystemExit("Phase 187 final replay-grace candidate is not local to Phase85 replay predicate")
    source = source[:grace_pos] + new_term + source[grace_pos + len(old_term):]

if source.count(new_term) != 1:
    raise SystemExit(f"Phase 187 expected one widened replay-grace term, found {source.count(new_term)}")

updated_replay_pos = source.index(replay_token)
term_pos = source.index(new_term)
if not (telemetry_pos < term_pos < updated_replay_pos):
    raise SystemExit("Phase 187 widened term is not between Phase181 telemetry and final replay predicate")

# The Phase181 LOGGER argument must remain scalar. Only the later replay guard may carry the widened
# term. Inspect the text from telemetry marker through the widened term rather than guessing a parent if.
telemetry_to_term = source[telemetry_pos:term_pos]
if new_term in telemetry_to_term:
    raise SystemExit("Phase 187 incorrectly widened Phase181 telemetry")
if old_term not in telemetry_to_term:
    raise SystemExit("Phase 187 lost scalar Phase181 phase133ReplayGrace telemetry argument")

required = [
    "phase161SupportedLocomotionNativeLoss",
    new_term,
    "phase150SupportReacquired",
    "GATE_E_PHASE85_CARRY_REPLAY",
    telemetry_marker,
    replay_token,
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 187 lost bounded handoff-recovery anchors: " + ", ".join(missing))

# Inspect only the rewritten predicate neighborhood. Phase187 composes an already-bounded predicate
# and must not add any direct player/world/train/physics mutation.
term_slice = source[max(0, term_pos - 1200):term_pos + len(new_term) + 1200]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in term_slice:
        raise SystemExit("Phase 187 found forbidden direct gameplay mutation near de-dup predicate: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 187: widens only the last replay-grace token between Phase181 telemetry and the unique Phase85 replay predicate")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
