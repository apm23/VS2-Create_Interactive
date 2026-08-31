#!/usr/bin/env python3
from pathlib import Path
import re
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
# Production-carry #380 exposed a selector bug after Phase181 added replay-guard telemetry: a global
# token search rewrote the telemetry argument outside phase133ReplayGrace's lexical scope. #381 then
# showed that requiring `if (` at the beginning of a line is also too brittle after cumulative phase
# rewrites. The replay-tick token is unique and lives inside the final Phase85 condition, so bind to
# the nearest preceding `if (` regardless of line formatting and modify only that condition prefix.
anchor = "phase150SupportReacquired"
replay_token = "carryReplayPlayerTick != player.tickCount"
old_term = "phase133ReplayGrace"
new_term = "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"

replay_positions = [match.start() for match in re.finditer(re.escape(replay_token), source)]
if len(replay_positions) != 1:
    raise SystemExit(f"Phase 187 expected one final Phase85 replay-tick anchor, found {len(replay_positions)}")
replay_pos = replay_positions[0]

guard_start = source.rfind("if (", max(0, replay_pos - 16000), replay_pos)
if guard_start < 0:
    raise SystemExit("Phase 187 could not locate nearest final Phase85 replay if")
guard_prefix = source[guard_start:replay_pos]
if "phase81PhysicalSupport" not in guard_prefix or anchor not in guard_prefix or old_term not in guard_prefix:
    raise SystemExit("Phase 187 nearest replay if lost expected Phase85 support/de-dup anchors")

# The Phase132 de-dup escape hatch is the grace identifier nearest the replay-tick predicate.
# Restrict replacement to the nearest replay if so Phase181 LOGGER arguments can never be selected.
if new_term not in guard_prefix:
    grace_pos = guard_prefix.rfind(old_term)
    anchor_pos = guard_prefix.rfind(anchor)
    if grace_pos < 0 or anchor_pos < 0 or grace_pos <= anchor_pos:
        raise SystemExit("Phase 187 could not locate final Phase133 grace after Phase150 reacquire anchor")
    guard_prefix = guard_prefix[:grace_pos] + new_term + guard_prefix[grace_pos + len(old_term):]
    source = source[:guard_start] + guard_prefix + source[replay_pos:]

# Fail closed if the widened expression appears in Phase181 telemetry. The scalar telemetry argument
# must remain untouched; only the final replay condition may contain the widened expression.
telemetry_marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"
telemetry_pos = source.find(telemetry_marker)
if telemetry_pos >= 0:
    telemetry_slice = source[max(0, telemetry_pos - 800):telemetry_pos + 1800]
    if new_term in telemetry_slice:
        raise SystemExit("Phase 187 incorrectly rewrote Phase181 telemetry instead of the replay guard")

updated_replay_pos = source.find(replay_token)
updated_guard_start = source.rfind("if (", max(0, updated_replay_pos - 16000), updated_replay_pos)
if updated_guard_start < 0:
    raise SystemExit("Phase 187 lost final replay if after rewrite")
updated_guard = source[updated_guard_start:updated_replay_pos]
if new_term not in updated_guard or anchor not in updated_guard or "phase81PhysicalSupport" not in updated_guard:
    raise SystemExit("Phase 187 widened term is not contained by final Phase85 replay guard")

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
print("Phase 187: binds to nearest final Phase85 replay if and widens only its bounded de-dup grace")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
