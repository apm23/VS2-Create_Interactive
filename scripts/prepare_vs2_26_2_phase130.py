#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run #142 proved the carry gate is correctly failing because Phase81 physical support
# turns false while broadphase/onGround remain true. The Phase81 vertical gap becomes NaN,
# which only tells us its simplified-collider state stopped exposing xz_inside_any/gap.
# Expose that already-computed source string beside the existing support telemetry,
# read-only, before changing any carry/collision behavior. Later cumulative phases can
# rewrite the enclosing guard, so locate the support log structurally rather than pinning
# its exact if-condition text.
if "GATE_E_PHASE131_SUPPORT_SOURCE" not in source:
    marker = '"GATE_E_PHASE81_SUPPORT_CONTINUITY'
    marker_pos = source.find(marker)
    if marker_pos < 0:
        raise SystemExit("Phase 130 could not find Phase81 support log marker")

    search_start = max(0, marker_pos - 4000)
    prefix = source[search_start:marker_pos]
    candidates = list(re.finditer(r'(?m)^(?P<indent>[ \t]*)if \(', prefix))
    support_if_pos = None
    support_indent = None
    for candidate in reversed(candidates):
        absolute = search_start + candidate.start()
        segment = source[absolute:marker_pos]
        if "carryReplayGuardSamples" in segment and "LOGGER.info" in segment:
            support_if_pos = absolute
            support_indent = candidate.group("indent")
            break
    if support_if_pos is None or support_indent is None:
        raise SystemExit("Phase 130 could not locate structural Phase81 support log guard")

    probe = (
        f'{support_indent}if (productionSmokeFixture && fixtureContactAcquireTicks >= 12\n'
        f'{support_indent}        && player.tickCount >= 14 && player.tickCount <= 40) {{\n'
        f'{support_indent}    LOGGER.info(\n'
        f'{support_indent}        "GATE_E_PHASE131_SUPPORT_SOURCE player_tick={{}} carriage_id={{}} physical_support={{}} vertical_gap={{}} simplified_state={{}} read_only=true",\n'
        f'{support_indent}        player.tickCount, carriage.getId(), phase81PhysicalSupport, phase81VerticalGap, simplifiedColliderState);\n'
        f'{support_indent}}}\n\n'
    )
    source = source[:support_if_pos] + probe + source[support_if_pos:]

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
print("Phase 130: exposes Phase81 simplified-collider support source read-only with structural anchoring; production carry unchanged")
