#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 102 proved the genuine contact baseline is captured on carriage entity id=2,
# but once the moving train reaches the LocalPlayer the physically supporting
# carriage candidate is a sibling entity (id=4/5) with non-zero Create frame motion.
# Exact entity identity is therefore too strict for this multi-carriage smoke.
# Keep this harness-only: permit the existing Phase 79 Create-native carry replay
# only when the currently selected carriage has a simplified collider directly
# under the player's feet (XZ containment and <= 0.05 block vertical separation).
#
# Production-world #578 proved this original support parser was the upstream source of the
# later native-health starvation: the current Create collider exposed vertical_gap=0/0.0001
# while Phase81 still reported NaN because it passed the entire semicolon-delimited suffix to
# Double.parseDouble. Bound the value at the next semicolon here, at the source boundary, so
# Phase131/134 and later consumers reuse the same strict physical-support result.
condition_anchor = '''            if (carryBaselineCaptured\n                && carryCarriageEntityId == carriage.getId()\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            boolean phase81PhysicalSupport = false;\n            double phase81VerticalGap = Double.NaN;\n            if (simplifiedColliderState.contains(";xz_inside_any=true")) {\n                int phase81GapIndex = simplifiedColliderState.lastIndexOf(";vertical_gap=");\n                if (phase81GapIndex >= 0) {\n                    int phase81GapStart = phase81GapIndex + 14;\n                    int phase81GapEnd = simplifiedColliderState.indexOf(';', phase81GapStart);\n                    String phase81GapText = phase81GapEnd >= 0\n                        ? simplifiedColliderState.substring(phase81GapStart, phase81GapEnd)\n                        : simplifiedColliderState.substring(phase81GapStart);\n                    try {\n                        phase81VerticalGap = Double.parseDouble(phase81GapText);\n                        phase81PhysicalSupport = Double.isFinite(phase81VerticalGap)\n                            && Math.abs(phase81VerticalGap) <= 0.05;\n                    } catch (NumberFormatException ignored) {\n                    }\n                }\n            }\n            if (carryBaselineCaptured && carryReplayGuardSamples <= 40) {\n                LOGGER.info(\n                    "GATE_E_PHASE81_SUPPORT_CONTINUITY saved_carriage_id={} current_carriage_id={} same_carriage={} physical_support={} vertical_gap={} player_tick={} on_ground={} collision_eligible={} broadphase_overlap={}",\n                    carryCarriageEntityId, carriage.getId(), carryCarriageEntityId == carriage.getId(),\n                    phase81PhysicalSupport, phase81VerticalGap, player.tickCount,\n                    player.onGround(), collisionEligible, broadphaseOverlap);\n            }\n\n            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "GATE_E_PHASE81_SUPPORT_CONTINUITY" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 81 could not find Phase 79 replay identity guard after Phase 80")
    source = source.replace(condition_anchor, condition_replacement, 1)

# Give the functional marker a Phase 81 name so the next smoke can distinguish
# sibling-support replay from the original exact-id Phase 79 experiment.
source = source.replace(
    '"GATE_E_PHASE79_CARRY_REPLAY carriage_id={} requested={},{},{} allowed={},{},{} before={},{},{} after={},{},{}"',
    '"GATE_E_PHASE81_CARRY_REPLAY carriage_id={} requested={},{},{} allowed={},{},{} before={},{},{} after={},{},{}"',
    1,
)
source = source.replace(
    '"GATE_E_PHASE79_CARRY_REPLAY_ERROR type={}"',
    '"GATE_E_PHASE81_CARRY_REPLAY_ERROR type={}"',
    1,
)

client_probe.write_text(source, encoding="utf-8")
print("Phase 81: bounds strict support gap parsing at the original replay/native-health support boundary; harness-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase82.py")), run_name="__main__")
