#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #408 proved the additional Phase187 rewrite is a preparation-order blocker:
# Phase161 has already widened the known native de-dup guard with
# phase161SupportedLocomotionNativeLoss, but rewriting phase150SupportReacquired here changes the
# exact Phase150 guard shape that the deliberate late Phase132 pass still consumes. Keep Phase187
# non-mutating and verify the already-bounded Phase161 recovery is still present. This preserves
# Phase132's late composition pass and avoids adding any new carry vector or physics path.
replay_token = "carryReplayPlayerTick != player.tickCount"
phase161_term = "|| phase161SupportedLocomotionNativeLoss)"
phase150_term = "|| phase150SupportReacquired))"
telemetry_marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"

if source.count(replay_token) != 1:
    raise SystemExit(f"Phase 187 expected one final Phase85 replay-tick anchor, found {source.count(replay_token)}")
if phase161_term not in source:
    raise SystemExit("Phase 187 lost the existing bounded Phase161 native-loss bypass")
if phase150_term not in source:
    raise SystemExit("Phase 187 lost the Phase150 de-dup shape required by the late Phase132 composition pass")
if telemetry_marker not in source:
    raise SystemExit("Phase 187 lost Phase181 final replay telemetry")

replay_pos = source.index(replay_token)
phase161_pos = source.rfind(phase161_term, 0, replay_pos)
phase150_pos = source.rfind(phase150_term, 0, replay_pos)
if phase161_pos < 0 or phase150_pos < 0:
    raise SystemExit("Phase 187 bounded recovery/de-dup anchors are not local to the final replay predicate")
if replay_pos - min(phase161_pos, phase150_pos) > 7000:
    raise SystemExit("Phase 187 bounded recovery/de-dup anchors drifted away from the final replay predicate")

# Read-only structural phase: do not alter player/world/train/physics behavior here.
client_probe.write_text(source, encoding="utf-8")
print("Phase 187: preserves Phase161 bounded recovery and Phase150 shape for the late Phase132 composition pass; no gameplay mutation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase188.py")), run_name="__main__")
