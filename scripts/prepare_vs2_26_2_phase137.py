#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #204 proved a concrete one-tick de-dup race: native Create carry was
# exact (drift_sq=0) on a supported carriage, then Phase85 replay ran on the immediately
# following tick before the next native-carry-health sample could settle, producing roughly
# 2x carriage motion. Production-world #206/#208 narrowed the accounting problem further:
# a previous compatibility replay can either be duplicate displacement (discounting it makes
# drift smaller) or necessary compensation (the raw player delta already matches carriage
# motion, so discounting it makes drift worse). Select whichever observation has the smaller
# drift and accept a two-tick sampled interval when its net player/carriage delta is exact.
# This only changes replay de-dup health accounting; no new carry vector, teleport, collision,
# train control, world mutation, or VS2 physics path is introduced.
old_guard = '''!(productionSmoke && explicitCarryCompat && Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false")))'''
new_guard = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))))'''
if "vs2.phase134NativeCarryHealthyTick." not in source:
    if old_guard not in source:
        raise SystemExit("Phase 137 could not find adaptive native-carry replay suppression guard")
    source = source.replace(old_guard, new_guard, 1)

# Run #208 produced exact net carry over a two-tick observation at carriage 4 tick 31:
# raw player_delta == carriage_delta, while unconditional replay discount manufactured
# drift ~= the prior replay vector and kept replay enabled. A two-tick gap is therefore a
# valid health observation when the net supported movement is already exact.
old_health = '''boolean phase134NativeCarryHealthy = phase134TickGap == 1 && phase134DriftSq <= 0.01 && player.onGround();'''
new_health = '''boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && phase134DriftSq <= 0.01 && player.onGround();'''
if old_health in source:
    source = source.replace(old_health, new_health, 1)
elif "phase134TickGap <= 2" not in source:
    raise SystemExit("Phase 137 could not find Phase131 native-carry health predicate")

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

if "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_SELECTION" not in source:
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
boolean phase137PreviousReplayInSample = phase137PreviousReplayTick == phase134PreviousTick;
double phase137RawDriftX = phase134PlayerDx - phase134CarriageDx;
double phase137RawDriftY = phase134PlayerDy - phase134CarriageDy;
double phase137RawDriftZ = phase134PlayerDz - phase134CarriageDz;
double phase137RawDriftSq = phase137RawDriftX * phase137RawDriftX
    + phase137RawDriftY * phase137RawDriftY + phase137RawDriftZ * phase137RawDriftZ;
double phase137DiscountedPlayerDx = phase134PlayerDx - (phase137PreviousReplayInSample ? phase137PreviousReplayX : 0.0);
double phase137DiscountedPlayerDy = phase134PlayerDy - (phase137PreviousReplayInSample ? phase137PreviousReplayY : 0.0);
double phase137DiscountedPlayerDz = phase134PlayerDz - (phase137PreviousReplayInSample ? phase137PreviousReplayZ : 0.0);
double phase137DiscountedDriftX = phase137DiscountedPlayerDx - phase134CarriageDx;
double phase137DiscountedDriftY = phase137DiscountedPlayerDy - phase134CarriageDy;
double phase137DiscountedDriftZ = phase137DiscountedPlayerDz - phase134CarriageDz;
double phase137DiscountedDriftSq = phase137DiscountedDriftX * phase137DiscountedDriftX
    + phase137DiscountedDriftY * phase137DiscountedDriftY + phase137DiscountedDriftZ * phase137DiscountedDriftZ;
boolean phase137UseReplayDiscount = phase137PreviousReplayInSample
    && phase137DiscountedDriftSq < phase137RawDriftSq;
double phase134NativePlayerDx = phase137UseReplayDiscount ? phase137DiscountedPlayerDx : phase134PlayerDx;
double phase134NativePlayerDy = phase137UseReplayDiscount ? phase137DiscountedPlayerDy : phase134PlayerDy;
double phase134NativePlayerDz = phase137UseReplayDiscount ? phase137DiscountedPlayerDz : phase134PlayerDz;
double phase134DriftX = phase134NativePlayerDx - phase134CarriageDx;
double phase134DriftY = phase134NativePlayerDy - phase134CarriageDy;
double phase134DriftZ = phase134NativePlayerDz - phase134CarriageDz;
if (phase137PreviousReplayInSample) {
    LOGGER.info(
        "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_SELECTION player_tick={} carriage_id={} previous_sample_tick={} replay={},{},{} raw_drift_sq={} discounted_drift_sq={} selected={} native_adjusted_player_delta={},{},{} read_only=true",
        player.tickCount, carriage.getId(), phase134PreviousTick,
        phase137PreviousReplayX, phase137PreviousReplayY, phase137PreviousReplayZ,
        phase137RawDriftSq, phase137DiscountedDriftSq,
        phase137UseReplayDiscount ? "discounted" : "raw",
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
    "phase134TickGap <= 2",
    "if (phase134NativeCarryHealthy)",
    "vs2.phase137ReplayTick.",
    "vs2.phase137ReplayX.",
    "phase137PreviousReplayInSample",
    "phase137RawDriftSq",
    "phase137DiscountedDriftSq",
    "phase137UseReplayDiscount",
    "phase134NativePlayerDx",
    "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_SELECTION",
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
print("Phase 137: selects raw vs replay-discounted native carry health and accepts exact two-tick samples")
