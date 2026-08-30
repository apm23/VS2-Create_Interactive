#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run #142 proved the carry gate is correctly failing because Phase81 physical support
# turns false while broadphase/onGround remain true. The Phase81 vertical gap becomes NaN,
# which only tells us its simplified-collider state stopped exposing xz_inside_any/gap.
# Expose that already-computed source string beside the existing guard, read-only, before
# changing any carry/collision behavior.
anchor = '''            if (carryBaselineCaptured && carryReplayGuardSamples <= 40) {\n                LOGGER.info(\n                    "GATE_E_PHASE81_SUPPORT_CONTINUITY saved_carriage_id={} current_carriage_id={} same_carriage={} physical_support={} vertical_gap={} player_tick={} on_ground={} collision_eligible={} broadphase_overlap={}",'''
replacement = '''            if (productionSmokeFixture && fixtureContactAcquireTicks >= 12\n                    && player.tickCount >= 14 && player.tickCount <= 40) {\n                LOGGER.info(\n                    "GATE_E_PHASE131_SUPPORT_SOURCE player_tick={} carriage_id={} physical_support={} vertical_gap={} simplified_state={} read_only=true",\n                    player.tickCount, carriage.getId(), phase81PhysicalSupport, phase81VerticalGap, simplifiedColliderState);\n            }\n\n''' + anchor

if "GATE_E_PHASE131_SUPPORT_SOURCE" not in source:
    if anchor not in source:
        raise SystemExit("Phase 130 could not find Phase81 support log anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_E_PHASE131_SUPPORT_SOURCE',
    'simplified_state={}',
    'phase81PhysicalSupport',
    'phase81VerticalGap',
    'simplifiedColliderState',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 130 lost physical-support source telemetry: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 130: exposes Phase81 simplified-collider support source read-only; production carry unchanged")
