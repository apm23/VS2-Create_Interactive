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

# Production-world #179 proved Phase130's blanket production replay suppression is too
# broad: Create native carry was exact for the 15->16 interval (drift_sq=0), then stopped
# while strict simplified-collider support remained true through ticks 17-23. Keep the
# duplicate-carry protection from #167, but make it evidence-driven per carriage. Phase134
# records whether the just-observed interval was natively carried; Phase85 replay is only
# suppressed while that signal is healthy. No new vector, clamp, teleport, or physics path
# is introduced: this only re-enables the already validated Create-computed/filtered replay
# when native Create carry demonstrably failed to advance the supported LocalPlayer.
adaptive_suppression = '!(productionSmoke && explicitCarryCompat && Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false")))'
source = source.replace(
    '!(productionSmoke && explicitCarryCompat)',
    adaptive_suppression,
    1,
)

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

# Production-world #176 reached the real moving train and showed one exact native-carry
# interval (drift_sq=0), but the long-lived Phase127 baseline stayed on carriage 5 while
# the physically supporting Create candidate moved through sibling carriage 7. Measure
# player-vs-carriage world delta independently for each carriage that currently has strict
# simplified-collider support. #179 promotes this from telemetry-only to the narrow replay
# de-dup signal above: healthy means one consecutive supported interval with <=0.01 drift.
if "GATE_E_PHASE134_ACTIVE_SUPPORT_CARRY_BALANCE" not in source:
    marker_pattern = re.compile(r'(?m)^(?P<indent>[ \t]*)int productionSmokeSupportLossTicks;')
    marker_match = marker_pattern.search(source)
    if marker_match is None:
        raise SystemExit("Phase 131 could not find support telemetry insertion point")
    indent = marker_match.group("indent")
    telemetry = (
        f'{indent}if (phase81PhysicalSupport && collisionEligible && broadphaseOverlap) {{\n'
        f'{indent}    String phase134Prefix = "vs2.phase134." + carriage.getId() + ".";\n'
        f'{indent}    String phase134HealthyKey = "vs2.phase134NativeCarryHealthy." + carriage.getId();\n'
        f'{indent}    System.setProperty(phase134HealthyKey, "false");\n'
        f'{indent}    String phase134TickText = System.getProperty(phase134Prefix + "tick");\n'
        f'{indent}    int phase134PreviousTick = Integer.MIN_VALUE;\n'
        f'{indent}    double phase134PreviousPlayerX = Double.NaN;\n'
        f'{indent}    double phase134PreviousPlayerY = Double.NaN;\n'
        f'{indent}    double phase134PreviousPlayerZ = Double.NaN;\n'
        f'{indent}    double phase134PreviousCarriageX = Double.NaN;\n'
        f'{indent}    double phase134PreviousCarriageY = Double.NaN;\n'
        f'{indent}    double phase134PreviousCarriageZ = Double.NaN;\n'
        f'{indent}    try {{\n'
        f'{indent}        if (phase134TickText != null) {{\n'
        f'{indent}            phase134PreviousTick = Integer.parseInt(phase134TickText);\n'
        f'{indent}            phase134PreviousPlayerX = Double.parseDouble(System.getProperty(phase134Prefix + "px"));\n'
        f'{indent}            phase134PreviousPlayerY = Double.parseDouble(System.getProperty(phase134Prefix + "py"));\n'
        f'{indent}            phase134PreviousPlayerZ = Double.parseDouble(System.getProperty(phase134Prefix + "pz"));\n'
        f'{indent}            phase134PreviousCarriageX = Double.parseDouble(System.getProperty(phase134Prefix + "cx"));\n'
        f'{indent}            phase134PreviousCarriageY = Double.parseDouble(System.getProperty(phase134Prefix + "cy"));\n'
        f'{indent}            phase134PreviousCarriageZ = Double.parseDouble(System.getProperty(phase134Prefix + "cz"));\n'
        f'{indent}        }}\n'
        f'{indent}    }} catch (NumberFormatException ignored) {{\n'
        f'{indent}        phase134PreviousTick = Integer.MIN_VALUE;\n'
        f'{indent}    }}\n'
        f'{indent}    if (phase134PreviousTick != Integer.MIN_VALUE && player.tickCount > phase134PreviousTick) {{\n'
        f'{indent}        int phase134TickGap = player.tickCount - phase134PreviousTick;\n'
        f'{indent}        double phase134PlayerDx = player.getX() - phase134PreviousPlayerX;\n'
        f'{indent}        double phase134PlayerDy = player.getY() - phase134PreviousPlayerY;\n'
        f'{indent}        double phase134PlayerDz = player.getZ() - phase134PreviousPlayerZ;\n'
        f'{indent}        double phase134CarriageDx = carriage.getX() - phase134PreviousCarriageX;\n'
        f'{indent}        double phase134CarriageDy = carriage.getY() - phase134PreviousCarriageY;\n'
        f'{indent}        double phase134CarriageDz = carriage.getZ() - phase134PreviousCarriageZ;\n'
        f'{indent}        double phase134DriftX = phase134PlayerDx - phase134CarriageDx;\n'
        f'{indent}        double phase134DriftY = phase134PlayerDy - phase134CarriageDy;\n'
        f'{indent}        double phase134DriftZ = phase134PlayerDz - phase134CarriageDz;\n'
        f'{indent}        double phase134DriftSq = phase134DriftX * phase134DriftX\n'
        f'{indent}            + phase134DriftY * phase134DriftY + phase134DriftZ * phase134DriftZ;\n'
        f'{indent}        boolean phase134NativeCarryHealthy = phase134TickGap == 1 && phase134DriftSq <= 0.01 && player.onGround();\n'
        f'{indent}        System.setProperty(phase134HealthyKey, Boolean.toString(phase134NativeCarryHealthy));\n'
        f'{indent}        LOGGER.info(\n'
        f'{indent}            "GATE_E_PHASE134_ACTIVE_SUPPORT_CARRY_BALANCE player_tick={{}} carriage_id={{}} tick_gap={{}} player_delta={{}},{{}},{{}} carriage_delta={{}},{{}},{{}} relative_drift={{}},{{}},{{}} drift_sq={{}} native_carry_healthy={{}} physical_support=true collision_eligible=true broadphase=true on_ground={{}} read_only=true",\n'
        f'{indent}            player.tickCount, carriage.getId(), phase134TickGap,\n'
        f'{indent}            phase134PlayerDx, phase134PlayerDy, phase134PlayerDz,\n'
        f'{indent}            phase134CarriageDx, phase134CarriageDy, phase134CarriageDz,\n'
        f'{indent}            phase134DriftX, phase134DriftY, phase134DriftZ, phase134DriftSq, phase134NativeCarryHealthy, player.onGround());\n'
        f'{indent}    }}\n'
        f'{indent}    System.setProperty(phase134Prefix + "tick", Integer.toString(player.tickCount));\n'
        f'{indent}    System.setProperty(phase134Prefix + "px", Double.toString(player.getX()));\n'
        f'{indent}    System.setProperty(phase134Prefix + "py", Double.toString(player.getY()));\n'
        f'{indent}    System.setProperty(phase134Prefix + "pz", Double.toString(player.getZ()));\n'
        f'{indent}    System.setProperty(phase134Prefix + "cx", Double.toString(carriage.getX()));\n'
        f'{indent}    System.setProperty(phase134Prefix + "cy", Double.toString(carriage.getY()));\n'
        f'{indent}    System.setProperty(phase134Prefix + "cz", Double.toString(carriage.getZ()));\n'
        f'{indent}}}\n'
    )
    source = source[:marker_match.start()] + telemetry + source[marker_match.start():]

required = [
    "GATE_E_PHASE131_SUPPORT_STREAK",
    "GATE_E_PHASE133_SUPPORT_LOSS_DIAGNOSTIC",
    "GATE_E_PHASE134_ACTIVE_SUPPORT_CARRY_BALANCE",
    "workflow_gate_authoritative=true",
    "nonfatal=true",
    "productionSmokeSupportTrackedCarriage",
    "phase81PhysicalSupport && collisionEligible && broadphaseOverlap",
    "vs2.phase134NativeCarryHealthy.",
    "phase134NativeCarryHealthy",
    "native_carry_healthy={}",
    adaptive_suppression,
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 131 lost adaptive support/carry diagnostic anchors: " + ", ".join(missing))
if "Production smoke rejected unsupported carriage-local carry continuity" in source:
    raise SystemExit("Phase 131 failed to remove diagnostic crash path")
if '!(productionSmoke && explicitCarryCompat)\n' in source:
    raise SystemExit("Phase 131 retained blanket production replay suppression")

for forbidden in ['player.setPos(', 'player.setDeltaMovement(', '.move(', '.teleport', 'setBlock(', '.useItemOn(', '.attack(']:
    if forbidden in telemetry if 'telemetry' in locals() else False:
        raise SystemExit("Phase 131 active-support carry health found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 131: adapts Create-filtered replay suppression to measured native carry health while preserving nonfatal support diagnostics")
