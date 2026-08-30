#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

if "&& &&" in source:
    raise SystemExit("Phase 131 found duplicate conjunction after Phase130")
if "!(productionSmoke && explicitCarryCompat)" not in source:
    raise SystemExit("Phase 131 lost production carry replay suppression predicate")
if "carryReplayPlayerTick != player.tickCount" not in source:
    raise SystemExit("Phase 131 lost original replay tick predicate")

# Production-world #173 proved the support-loss exception is a CI harness blocker:
# it deliberately crashes the client before the workflow's independent sustained-carry
# parser can classify the same carriage-local telemetry. Keep the diagnostic fail-closed
# at workflow level, but never crash Minecraft from diagnostic code. Later generators
# preserve the logic while changing indentation, so locate the guard structurally.
if "GATE_E_PHASE133_SUPPORT_LOSS_DIAGNOSTIC" not in source:
    pattern = re.compile(
        r'(?P<indent>^[ \t]*)if \(productionSmokeSupportTrackedCarriage && productionSmokeSupportLossTicks >= 3\s*'
        r'&& broadphaseOverlap && player\.onGround\(\)\) \{\s*'
        r'throw new IllegalStateException\("Production smoke rejected unsupported carriage-local carry continuity after "\s*'
        r'\+ productionSmokeSupportLossTicks \+ " consecutive ticks"\);\s*'
        r'(?P=indent)\}',
        re.MULTILINE,
    )
    match = pattern.search(source)
    if match is None:
        raise SystemExit("Phase 131 could not find structural Phase130 support-loss exception block")
    indent = match.group("indent")
    replacement = (
        f'{indent}if (productionSmokeSupportTrackedCarriage && productionSmokeSupportLossTicks >= 3\n'
        f'{indent}        && broadphaseOverlap && player.onGround()) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE133_SUPPORT_LOSS_DIAGNOSTIC player_tick={{}} carriage_id={{}} consecutive_loss_ticks={{}} workflow_gate_authoritative=true nonfatal=true fixture_only=true",\n'
        f'{indent}        player.tickCount, carriage.getId(), productionSmokeSupportLossTicks);\n'
        f'{indent}}}'
    )
    source = source[:match.start()] + replacement + source[match.end():]

required = [
    "GATE_E_PHASE131_SUPPORT_STREAK",
    "GATE_E_PHASE133_SUPPORT_LOSS_DIAGNOSTIC",
    "workflow_gate_authoritative=true",
    "nonfatal=true",
    "productionSmokeSupportTrackedCarriage",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 131 lost support diagnostic anchors: " + ", ".join(missing))
if "Production smoke rejected unsupported carriage-local carry continuity" in source:
    raise SystemExit("Phase 131 failed to remove diagnostic crash path")

client_probe.write_text(source, encoding="utf-8")
print("Phase 131: validates Phase130 replay syntax and structurally keeps support-loss telemetry nonfatal so the workflow is the authoritative carry gate")
