#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #204 proved a concrete one-tick de-dup race: native Create carry was
# exact (drift_sq=0) on a supported carriage, then Phase85 replay ran on the immediately
# following tick before the next native-carry-health sample could settle, producing roughly
# 2x carriage motion. Production-world #206 narrowed the root cause further: Phase134's
# health sample includes the previous tick's compatibility replay displacement, so replay
# makes native carry look unhealthy and thereby keeps itself enabled. Record the exact
# already-allowed replay displacement and discount it from the next Phase134 health sample.
# This changes only replay de-dup accounting; no new vector, clamp, teleport, collision,
# train control, or VS2 physics behavior is introduced.
old_guard = '''!(productionSmoke && explicitCarryCompat && Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false")))'''
new_guard = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))))'''
if "vs2.phase134NativeCarryHealthyTick." not in source:
    if old_guard not in source:
        raise SystemExit("Phase 137 could not find adaptive native-carry replay suppression guard")
    source = source.replace(old_guard, new_guard, 1)

health_set = '''        System.setProperty(phase134HealthyKey, Boolean.toString(phase134NativeCarryHealthy));
'''
health_set_with_tick = health_set + '''        if (phase134NativeCarryHealthy) {
            System.setProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId(), Integer.toString(player.tickCount));
        }
'''
if 'System.setProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()' not in source:
    if health_set not in source:
        raise SystemExit("Phase 137 could not find Phase134 health publication")
    source = source.replace(health_set, health_set_with_tick, 1)

# Phase79/85 owns the existing Create-computed, collision-filtered replay and exposes the
# final allowedMovement. Persist only that already-applied displacement so the following
# health sample can distinguish native movement from compatibility movement.
if "vs2.phase137ReplayTick." not in source:
    replay_assignment = '''                                carryReplayPlayerTick = player.tickCount;
'''
    if source.count(replay_assignment) != 1:
        raise SystemExit("Phase 137 expected exactly one final carry replay assignment")
    replay_record = replay_assignment + '''                                System.setProperty("vs2.phase137ReplayTick." + carriage.getId(), Integer.toString(player.tickCount));
                                System.setProperty("vs2.phase137ReplayX." + carriage.getId(), Double.toString(allowedMovement.x));
                                System.setProperty("vs2.phase137ReplayY." + carriage.getId(), Double.toString(allowedMovement.y));
                                System.setProperty("vs2.phase137ReplayZ." + carriage.getId(), Double.toString(allowedMovement.z));
'''
    source = source.replace(replay_assignment, replay_record, 1)

if "GATE_E_PHASE137_NATIVE_HEALTH_REPLAY_DISCOUNT" not in source:
    drift_anchor = '''        double phase134DriftX = phase134PlayerDx - phase134CarriageDx;
        double phase134DriftY = phase134PlayerDy - phase134CarriageDy;
        double phase134DriftZ = phase134PlayerDz - phase134CarriageDz;
'''
    if drift_anchor not in source:
        raise SystemExit("Phase 137 could not find Phase134 native-health drift calculation")
    drift_replacement = '''        int phase137PreviousReplayTick = Integer.MIN_VALUE;
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
    source = source.replace(drift_anchor, drift_replacement, 1)

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
for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in drift_replacement if 'drift_replacement' in locals() else False:
        raise SystemExit("Phase 137 health accounting found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 137: discounts prior compatibility replay from native Create carry health before de-dup suppression")
