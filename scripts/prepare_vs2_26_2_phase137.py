#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #204 proved a concrete one-tick de-dup race: native Create carry was
# exact (drift_sq=0) on a supported carriage, then Phase85 replay ran on the immediately
# following tick before the next native-carry-health sample could settle, producing roughly
# 2x carriage motion. Production-world #206 narrowed the root cause further: Phase131's
# active-support health sample includes the previous tick's compatibility replay displacement,
# so replay makes native carry look unhealthy and thereby keeps itself enabled. Record the
# exact already-allowed replay displacement and discount it from the next health sample.
# Match generated Java structurally because Phase131 derives indentation from its insertion
# site; fixed whitespace anchors are not authoritative. This changes only replay de-dup
# accounting; no new vector, clamp, teleport, collision, train control, or VS2 physics path.
old_guard = '''!(productionSmoke && explicitCarryCompat && Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false")))'''
new_guard = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))))'''
if "vs2.phase134NativeCarryHealthyTick." not in source:
    if old_guard not in source:
        raise SystemExit("Phase 137 could not find adaptive native-carry replay suppression guard")
    source = source.replace(old_guard, new_guard, 1)

if 'System.setProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()' not in source:
    health_pattern = re.compile(
        r'(?m)^(?P<indent>[ \t]*)System\.setProperty\(phase134HealthyKey, Boolean\.toString\(phase134NativeCarryHealthy\)\);\n'
    )
    health_match = health_pattern.search(source)
    if health_match is None:
        raise SystemExit("Phase 137 could not find Phase131 health publication")
    indent = health_match.group("indent")
    health_set_with_tick = (
        f'{indent}System.setProperty(phase134HealthyKey, Boolean.toString(phase134NativeCarryHealthy));\n'
        f'{indent}if (phase134NativeCarryHealthy) {{\n'
        f'{indent}    System.setProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId(), Integer.toString(player.tickCount));\n'
        f'{indent}}}\n'
    )
    source = source[:health_match.start()] + health_set_with_tick + source[health_match.end():]

# Phase79/85 owns the existing Create-computed, collision-filtered replay and exposes the
# final allowedMovement. Persist only that already-applied displacement so the following
# health sample can distinguish native movement from compatibility movement.
if "vs2.phase137ReplayTick." not in source:
    replay_pattern = re.compile(
        r'(?m)^(?P<indent>[ \t]*)carryReplayPlayerTick = player\.tickCount;'
    )
    replay_matches = list(replay_pattern.finditer(source))
    if len(replay_matches) != 1:
        raise SystemExit(f"Phase 137 expected exactly one final carry replay assignment, found {len(replay_matches)}")
    replay_match = replay_matches[0]
    indent = replay_match.group("indent")
    replay_record = (
        f'{indent}carryReplayPlayerTick = player.tickCount;\n'
        f'{indent}System.setProperty("vs2.phase137ReplayTick." + carriage.getId(), Integer.toString(player.tickCount));\n'
        f'{indent}System.setProperty("vs2.phase137ReplayX." + carriage.getId(), Double.toString(allowedMovement.x));\n'
        f'{indent}System.setProperty("vs2.phase137ReplayY." + carriage.getId(), Double.toString(allowedMovement.y));\n'
        f'{indent}System.setProperty("vs2.phase137ReplayZ." + carriage.getId(), Double.toString(allowedMovement.z));'
    )
    source = source[:replay_match.start()] + replay_record + source[replay_match.end():]

if "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_DISCOUNT" not in source:
    drift_pattern = re.compile(
        r'(?m)^(?P<indent>[ \t]*)double phase134DriftX = phase134PlayerDx - phase134CarriageDx;\n'
        r'(?P=indent)double phase134DriftY = phase134PlayerDy - phase134CarriageDy;\n'
        r'(?P=indent)double phase134DriftZ = phase134PlayerDz - phase134CarriageDz;\n'
    )
    drift_match = drift_pattern.search(source)
    if drift_match is None:
        raise SystemExit("Phase 137 could not structurally find Phase131 native-health drift calculation")
    indent = drift_match.group("indent")
    drift_template = '''int phase137PreviousReplayTick = Integer.MIN_VALUE;
double phase137PreviousReplayX = 0.0;
double phase137PreviousReplayY = 0.0;
double phase137PreviousReplayZ = 0.0;
try {
    phase137PreviousReplayTick = Integer.parseInt(System.getProperty("vs2.phase137ReplayTick." + carriage.getId(), "-2147483648"));
    phase137PreviousReplayX = Double.parseDouble(System.getProperty("vs2.phase137ReplayX." + carriage.getId(), "0.0"));
    phase137PreviousReplayY = Double.parseDouble(System.getProperty("vs2.phase137ReplayY." + carriage.getId(), "0.0"));
    phase137PreviousReplayZ = Double.parseDouble(System.getProperty("vs2.phase137ReplayZ." + carriage.getId(), "0.0"));
} catch (NumberFormatException ignored) {
    phase137PreviousReplayTick = Integer.MIN_VALUE;
}
boolean phase137DiscountPreviousReplay = phase137PreviousReplayTick == phase134PreviousTick;
double phase134NativePlayerDx = phase134PlayerDx - (phase137DiscountPreviousReplay ? phase137PreviousReplayX : 0.0);
double phase134NativePlayerDy = phase134PlayerDy - (phase137DiscountPreviousReplay ? phase137PreviousReplayY : 0.0);
double phase134NativePlayerDz = phase134PlayerDz - (phase137DiscountPreviousReplay ? phase137PreviousReplayZ : 0.0);
double phase134DriftX = phase134NativePlayerDx - phase134CarriageDx;
double phase134DriftY = phase134NativePlayerDy - phase134CarriageDy;
double phase134DriftZ = phase134NativePlayerDz - phase134CarriageDz;
if (phase137DiscountPreviousReplay) {
    LOGGER.info(
        "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_DISCOUNT player_tick={} carriage_id={} previous_sample_tick={} replay={},{},{} raw_player_delta={},{},{} native_adjusted_player_delta={},{},{} read_only=true",
        player.tickCount, carriage.getId(), phase134PreviousTick,
        phase137PreviousReplayX, phase137PreviousReplayY, phase137PreviousReplayZ,
        phase134PlayerDx, phase134PlayerDy, phase134PlayerDz,
        phase134NativePlayerDx, phase134NativePlayerDy, phase134NativePlayerDz);
}
'''
    drift_replacement = ''.join(
        (indent + line + '\n') if line else '\n'
        for line in drift_template.splitlines()
    )
    source = source[:drift_match.start()] + drift_replacement + source[drift_match.end():]

required = [
    "vs2.phase134NativeCarryHealthyTick.",
    "Integer.toString(player.tickCount - 1).equals",
    "if (phase134NativeCarryHealthy)",
    "vs2.phase137ReplayTick.",
    "vs2.phase137ReplayX.",
    "phase137DiscountPreviousReplay",
    "phase134NativePlayerDx",
    "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_DISCOUNT",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE134_ACTIVE_SUPPORT_CARRY_BALANCE",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 137 lost replay-aware native-carry de-dup anchors: " + ", ".join(missing))

# This phase records the already-existing replay and corrects its health accounting only.
if 'drift_replacement' in locals():
    for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
        if forbidden in drift_replacement:
            raise SystemExit("Phase 137 health accounting found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 137: structurally discounts prior compatibility replay from native Create carry health before de-dup suppression")
