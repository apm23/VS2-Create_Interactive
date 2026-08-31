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
# Production-carry #380 exposed a selector bug after Phase181 added replay-guard telemetry: the old
# global anchor search could bind to the telemetry argument `phase133ReplayGrace` instead of the
# actual Phase85 boolean guard. In production isolation that telemetry sits outside the local grace
# variable's lexical scope, so javac failed before Minecraft could boot. Locate the unique replay
# predicate first, then walk backward to the final replay `if (` and rewrite only that condition.
anchor = "phase150SupportReacquired"
replay_token = "carryReplayPlayerTick != player.tickCount"
old_term = "phase133ReplayGrace"
new_term = "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"

replay_positions = [match.start() for match in re.finditer(re.escape(replay_token), source)]
if len(replay_positions) != 1:
    raise SystemExit(f"Phase 187 expected one final Phase85 replay-tick anchor, found {len(replay_positions)}")
replay_pos = replay_positions[0]

search_start = max(0, replay_pos - 12000)
prefix = source[search_start:replay_pos]
if_candidates = list(re.finditer(r"(?m)^(?P<indent>[ \t]*)if \(", prefix))
guard_start = None
for candidate in reversed(if_candidates):
    absolute = search_start + candidate.start()
    segment = source[absolute:replay_pos]
    if (
        "phase81PhysicalSupport" in segment
        and anchor in segment
        and old_term in segment
        and "LOGGER.info" not in segment
    ):
        guard_start = absolute
        break

if guard_start is None:
    raise SystemExit("Phase 187 could not locate structural final Phase85 replay guard")

guard_segment = source[guard_start:replay_pos]
if new_term not in guard_segment:
    anchor_pos = guard_segment.rfind(anchor)
    grace_pos = guard_segment.find(old_term, anchor_pos + len(anchor)) if anchor_pos >= 0 else -1
    if grace_pos < 0:
        raise SystemExit("Phase 187 could not locate Phase133 de-dup grace inside final replay guard")
    guard_segment = (
        guard_segment[:grace_pos]
        + new_term
        + guard_segment[grace_pos + len(old_term):]
    )
    source = source[:guard_start] + guard_segment + source[replay_pos:]

# Fail closed if the rewrite ever lands in Phase181 telemetry again. The telemetry must retain the
# scalar phase133ReplayGrace argument; only the final replay predicate may contain the widened term.
telemetry_marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"
telemetry_pos = source.find(telemetry_marker)
if telemetry_pos >= 0:
    telemetry_slice = source[max(0, telemetry_pos - 800):telemetry_pos + 1800]
    if new_term in telemetry_slice:
        raise SystemExit("Phase 187 incorrectly rewrote Phase181 telemetry instead of the replay guard")

updated_replay_pos = source.find(replay_token)
updated_search_start = max(0, updated_replay_pos - 12000)
updated_prefix = source[updated_search_start:updated_replay_pos]
updated_if_candidates = list(re.finditer(r"(?m)^(?P<indent>[ \t]*)if \(", updated_prefix))
updated_guard = None
for candidate in reversed(updated_if_candidates):
    absolute = updated_search_start + candidate.start()
    segment = source[absolute:updated_replay_pos]
    if "phase81PhysicalSupport" in segment and anchor in segment and new_term in segment:
        updated_guard = segment
        break
if updated_guard is None:
    raise SystemExit("Phase 187 widened term is not contained by the final Phase85 replay guard")

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
print("Phase 187: structurally widens only the final Phase85 de-dup guard with bounded Phase161 recovery; Phase181 telemetry remains read-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
