#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #362 proves the bounded walk starts on strict support + fresh native carry,
# remains grounded/broadphase-supported, then loses native contact application after tick 22.
# Phase161 publishes supported native-loss recovery eligibility at tick 23, yet the final
# Phase85 Create-filtered replay does not execute. Trace the final replay guard inputs at the
# exact guard site before changing any carry/gameplay behavior. Read-only fixture telemetry only.
marker = "GATE_E_PHASE181_FINAL_REPLAY_GUARD"
if marker not in source:
    token = "carryReplayPlayerTick != player.tickCount"
    positions = []
    start = 0
    while True:
        pos = source.find(token, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + len(token)
    if len(positions) != 1:
        raise SystemExit(f"Phase 181 expected exactly one final replay tick predicate, found {len(positions)}")

    token_pos = positions[0]
    if_pos = source.rfind("if (", 0, token_pos)
    if if_pos < 0:
        raise SystemExit("Phase 181 could not locate final Phase85 replay guard")
    line_start = source.rfind("\n", 0, if_pos) + 1
    indent = source[line_start:if_pos]

    probe = (
        f'{indent}if (productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE181_FINAL_REPLAY_GUARD carriage_id={{}} player_tick={{}} baseline_captured={{}} baseline_id={{}} strict_support={{}} collision_eligible={{}} broadphase={{}} grounded={{}} phase161_supported_loss={{}} phase133_grace={{}} support_reacquired={{}} replay_tick={{}} rebase_tick={{}} native_health={{}} native_health_tick={{}} native_application_tick={{}} native_application_carriage={{}} fixture_only=true read_only=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, carryBaselineCaptured, carryBaselineCarriageId, phase81PhysicalSupport,\n'
        f'{indent}        collisionEligible, broadphaseOverlap, player.onGround(), phase161SupportedLocomotionNativeLoss,\n'
        f'{indent}        phase133ReplayGrace, phase150SupportReacquired, carryReplayPlayerTick, carryBaselineRebaseTick,\n'
        f'{indent}        System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "missing"),\n'
        f'{indent}        System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId(), "missing"),\n'
        f'{indent}        System.getProperty("vs2.phase170NativeContactApplicationTick", "missing"),\n'
        f'{indent}        System.getProperty("vs2.phase170NativeContactApplicationCarriageId", "missing"));\n'
        f'{indent}}}\n'
    )
    source = source[:line_start] + probe + source[line_start:]

required = [
    marker,
    "phase161SupportedLocomotionNativeLoss",
    "phase133ReplayGrace",
    "phase150SupportReacquired",
    "carryReplayPlayerTick",
    "carryBaselineRebaseTick",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "fixture_only=true read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 181 lost final replay guard telemetry anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 181: traces final bounded carry replay guard after Run 362 recovery eligibility mismatch; read-only only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase182.py")), run_name="__main__")
