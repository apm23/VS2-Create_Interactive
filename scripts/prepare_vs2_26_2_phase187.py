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
# Runs #380-#405 proved generic `if (` discovery is brittle after cumulative telemetry/helper
# insertion. Phase132 already owns and validates the exact de-dup escape hatch below, including a
# required token for it. Rewrite that exact structural token instead of rediscovering the parent
# condition. This cannot bind to Phase181 LOGGER telemetry because the full Phase132 expression is
# absent there.
replay_token = "carryReplayPlayerTick != player.tickCount"
old_escape = "|| phase150SupportReacquired)) || phase133ReplayGrace)"
new_escape = "|| phase150SupportReacquired)) || (phase133ReplayGrace || phase161SupportedLocomotionNativeLoss))"

if source.count(replay_token) != 1:
    raise SystemExit(f"Phase 187 expected one final Phase85 replay-tick anchor, found {source.count(replay_token)}")

if new_escape not in source:
    escape_count = source.count(old_escape)
    if escape_count != 1:
        raise SystemExit(f"Phase 187 expected one Phase132 de-dup escape anchor, found {escape_count}")
    source = source.replace(old_escape, new_escape, 1)

if source.count(new_escape) != 1:
    raise SystemExit(f"Phase 187 expected one widened Phase132 de-dup escape, found {source.count(new_escape)}")

replay_pos = source.index(replay_token)
escape_pos = source.index(new_escape)
if escape_pos >= replay_pos or replay_pos - escape_pos > 6000:
    raise SystemExit("Phase 187 widened de-dup escape is not local to the final Phase85 replay predicate")

# Fail closed if the widened expression ever appears in Phase181 telemetry. The telemetry keeps its
# scalar phase133ReplayGrace argument; only Phase132's final de-dup escape is widened.
telemetry_marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"
telemetry_pos = source.find(telemetry_marker)
if telemetry_pos >= 0:
    telemetry_slice = source[max(0, telemetry_pos - 800):telemetry_pos + 1800]
    if new_escape in telemetry_slice or "(phase133ReplayGrace || phase161SupportedLocomotionNativeLoss)" in telemetry_slice:
        raise SystemExit("Phase 187 incorrectly widened Phase181 telemetry")

required = [
    "phase161SupportedLocomotionNativeLoss",
    new_escape,
    "phase150SupportReacquired",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE181_FINAL_REPLAY_GUARD",
    replay_token,
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 187 lost bounded handoff-recovery anchors: " + ", ".join(missing))

# Inspect only the exact rewritten predicate neighborhood. Phase187 composes an already-bounded
# predicate and must not add direct player/world/train/physics mutation.
term_pos = source.index(new_escape)
term_slice = source[max(0, term_pos - 1200):term_pos + len(new_escape) + 1200]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in term_slice:
        raise SystemExit("Phase 187 found forbidden direct gameplay mutation near de-dup predicate: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 187: widens Phase132's exact validated de-dup escape with bounded Phase161 recovery; no parent-condition rediscovery")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
