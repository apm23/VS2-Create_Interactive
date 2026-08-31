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
# token search rewrote the telemetry argument outside phase133ReplayGrace's lexical scope. #381/#382
# then showed that line-based or nearest-text `if (` selection is still brittle because nested helper
# conditions can sit between the beginning of the final Phase85 condition and its unique replay token.
# Parse balanced parentheses and select the one if-condition that actually encloses the replay token.
anchor = "phase150SupportReacquired"
replay_token = "carryReplayPlayerTick != player.tickCount"
old_term = "phase133ReplayGrace"
new_term = "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)"

replay_positions = [match.start() for match in re.finditer(re.escape(replay_token), source)]
if len(replay_positions) != 1:
    raise SystemExit(f"Phase 187 expected one final Phase85 replay-tick anchor, found {len(replay_positions)}")
replay_pos = replay_positions[0]


def condition_end(if_pos: int) -> int:
    open_pos = source.find("(", if_pos, if_pos + 8)
    if open_pos < 0:
        return -1
    depth = 0
    in_string = False
    escaped = False
    for pos in range(open_pos, len(source)):
        ch = source[pos]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return pos + 1
    return -1


search_start = max(0, replay_pos - 20000)
enclosing = []
for match in re.finditer(r"\bif\s*\(", source[search_start:replay_pos]):
    absolute = search_start + match.start()
    end = condition_end(absolute)
    if end > replay_pos:
        condition = source[absolute:end]
        if replay_token in condition:
            enclosing.append((absolute, end, condition))

if not enclosing:
    raise SystemExit("Phase 187 could not locate enclosing final Phase85 replay condition")

# The innermost enclosing condition is the exact boolean guard containing the unique replay token.
guard_start, guard_end, guard_condition = max(enclosing, key=lambda item: item[0])
if "phase81PhysicalSupport" not in guard_condition or anchor not in guard_condition or old_term not in guard_condition:
    raise SystemExit("Phase 187 enclosing replay condition lost expected Phase85 support/de-dup anchors")

if new_term not in guard_condition:
    grace_pos = guard_condition.rfind(old_term)
    anchor_pos = guard_condition.rfind(anchor)
    if grace_pos < 0 or anchor_pos < 0 or grace_pos <= anchor_pos:
        raise SystemExit("Phase 187 could not locate final Phase133 grace after Phase150 reacquire anchor")
    guard_condition = guard_condition[:grace_pos] + new_term + guard_condition[grace_pos + len(old_term):]
    source = source[:guard_start] + guard_condition + source[guard_end:]

# Fail closed if the widened expression appears in Phase181 telemetry. The scalar telemetry argument
# must remain untouched; only the final replay condition may contain the widened expression.
telemetry_marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"
telemetry_pos = source.find(telemetry_marker)
if telemetry_pos >= 0:
    telemetry_slice = source[max(0, telemetry_pos - 800):telemetry_pos + 1800]
    if new_term in telemetry_slice:
        raise SystemExit("Phase 187 incorrectly rewrote Phase181 telemetry instead of the replay guard")

updated_replay_pos = source.find(replay_token)
updated_search_start = max(0, updated_replay_pos - 20000)
updated_enclosing = []
for match in re.finditer(r"\bif\s*\(", source[updated_search_start:updated_replay_pos]):
    absolute = updated_search_start + match.start()
    end = condition_end(absolute)
    if end > updated_replay_pos:
        condition = source[absolute:end]
        if replay_token in condition:
            updated_enclosing.append(condition)
if not updated_enclosing:
    raise SystemExit("Phase 187 lost enclosing replay condition after rewrite")
updated_guard = updated_enclosing[-1]
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
print("Phase 187: parses the enclosing final Phase85 replay condition and widens only its bounded de-dup grace")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
