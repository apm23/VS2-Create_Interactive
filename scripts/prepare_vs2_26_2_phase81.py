#!/usr/bin/env python3
from pathlib import Path

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
condition_anchor = '''            if (carryBaselineCaptured\n                && carryCarriageEntityId == carriage.getId()\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            boolean phase81PhysicalSupport = false;\n            double phase81VerticalGap = Double.NaN;\n            if (simplifiedColliderState.contains(";xz_inside_any=true")) {\n                int phase81GapIndex = simplifiedColliderState.lastIndexOf(";vertical_gap=");\n                if (phase81GapIndex >= 0) {\n                    String phase81GapText = simplifiedColliderState.substring(phase81GapIndex + 14);\n                    try {\n                        phase81VerticalGap = Double.parseDouble(phase81GapText);\n                        phase81PhysicalSupport = Double.isFinite(phase81VerticalGap)\n                            && Math.abs(phase81VerticalGap) <= 0.05;\n                    } catch (NumberFormatException ignored) {\n                    }\n                }\n            }\n            if (carryBaselineCaptured && carryReplayGuardSamples <= 40) {\n                LOGGER.info(\n                    "GATE_E_PHASE81_SUPPORT_CONTINUITY saved_carriage_id={} current_carriage_id={} same_carriage={} physical_support={} vertical_gap={} player_tick={} on_ground={} collision_eligible={} broadphase_overlap={}",\n                    carryCarriageEntityId, carriage.getId(), carryCarriageEntityId == carriage.getId(),\n                    phase81PhysicalSupport, phase81VerticalGap, player.tickCount,\n                    player.onGround(), collisionEligible, broadphaseOverlap);\n            }\n\n            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
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
print("Phase 81: relaxed Gate E replay identity only to a strict physical-support continuity guard across sibling Create carriage entities; harness-only")
