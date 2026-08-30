#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #281 proves a fresh native-carry sample is necessary but not sufficient for
# sustained walking: carry is exact through tick 40, the fixture starts normal forward input at
# tick 41, then tick 42 jumps 43.37 blocks in carriage-local space and immediately loses
# broadphase/support. Phase157 currently preserves the previous healthy classification for any
# amount of locomotion drift, while the previous Phase158 revision also suppresses compatibility
# replay for the whole walk. Together those guards hide a genuine carry loss instead of letting
# the existing Create-filtered compatibility path recover it. Keep the fresh-native start gate,
# but only hold native health across plausible player-relative locomotion (the same 0.75-block
# per-tick bound already enforced by the walk proof). Larger drift is classified unhealthy so
# the existing compatibility selector may recover carry. No new movement vector, teleport,
# collision/world/train mutation, or VS2 physics change is introduced.

health_old = '''boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && player.onGround()
            && (phase134DriftSq <= 0.01 || (phase157PlayerLocomoting && phase157PreviouslyHealthy));
        if (phase157PlayerLocomoting && phase157PreviouslyHealthy && phase134DriftSq > 0.01) {
            LOGGER.info(
                "GATE_E_PHASE157_LOCOMOTION_HEALTH_HOLD player_tick={} carriage_id={} drift_sq={} previous_healthy=true locomoting=true replay_suppression_preserved=true read_only_accounting=true",
                player.tickCount, carriage.getId(), phase134DriftSq);
        }'''
health_new = '''boolean phase158LocomotionHealthHold = phase157PlayerLocomoting
            && phase157PreviouslyHealthy
            && phase134DriftSq > 0.01
            && phase134DriftSq <= 0.5625;
        boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && player.onGround()
            && (phase134DriftSq <= 0.01 || phase158LocomotionHealthHold);
        if (phase158LocomotionHealthHold) {
            LOGGER.info(
                "GATE_E_PHASE157_LOCOMOTION_HEALTH_HOLD player_tick={} carriage_id={} drift_sq={} previous_healthy=true locomoting=true replay_suppression_preserved=true bounded=true read_only_accounting=true",
                player.tickCount, carriage.getId(), phase134DriftSq);
        } else if (phase157PlayerLocomoting && phase157PreviouslyHealthy && phase134DriftSq > 0.5625) {
            LOGGER.info(
                "GATE_E_PHASE158_LOCOMOTION_HEALTH_REJECT player_tick={} carriage_id={} drift_sq={} previous_healthy=true locomoting=true native_carry_healthy=false compatibility_recovery_allowed=true read_only_accounting=true",
                player.tickCount, carriage.getId(), phase134DriftSq);
        }'''
if "GATE_E_PHASE158_LOCOMOTION_HEALTH_REJECT" not in source:
    if source.count(health_old) != 1:
        raise SystemExit("Phase 158 expected exactly one Phase157 locomotion-health block")
    source = source.replace(health_old, health_new, 1)

walk_start_old = '''                        if (!phase154WalkStarted && phase154SupportNow) {
                            phase154WalkStarted = true;'''
walk_start_new = '''                        boolean phase158FreshNativeCarry = Boolean.parseBoolean(System.getProperty(
                            "vs2.phase134NativeCarryHealthy." + phase154Carriage.getId(), "false"))
                            && (Integer.toString(player.tickCount).equals(System.getProperty(
                                    "vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId()))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty(
                                    "vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId())));
                        if (!phase154WalkStarted && phase154SupportNow && phase158FreshNativeCarry) {
                            LOGGER.info(
                                "GATE_E_PHASE158_WALK_NATIVE_READY player_tick={} carriage_id={} support_now=true native_carry_healthy=true fresh_sample=true fixture_only=true",
                                player.tickCount, phase154Carriage.getId());
                            phase154WalkStarted = true;'''
if "GATE_E_PHASE158_WALK_NATIVE_READY" not in source:
    if source.count(walk_start_old) != 1:
        raise SystemExit("Phase 158 expected exactly one Phase154 walk-start guard")
    source = source.replace(walk_start_old, walk_start_new, 1)

# Production-world #282 proves the bounded recovery itself is now reachable, but also exposes
# a distinct duplicate-replay edge at a legitimate sibling-carriage handoff. Tick 34 rebases
# the active baseline 7 -> 4 with strict support and native observation; tick 35 then applies
# a 4.004-block Create-filtered compatibility replay on that freshly rebased carriage, producing
# a 4.649-block carriage-local jump while the player is still grounded/broadphase-supported.
# Give native carry one complete post-rebase tick before compatibility replay may resume. This
# only suppresses duplicate replay on the rebase tick and its immediate successor; genuine loss
# can recover from the second post-rebase tick onward. No new movement vector or physics change.
replay_guard_old = '''carryBaselineCarriageId == carriage.getId()
                            && carryReplayPlayerTick != player.tickCount'''
replay_guard_new = '''carryBaselineCarriageId == carriage.getId()
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2)
                            && carryReplayPlayerTick != player.tickCount'''
if "player.tickCount - carryBaselineRebaseTick >= 2" not in source:
    if source.count(replay_guard_old) != 1:
        raise SystemExit("Phase 158 expected exactly one active-baseline carry replay predicate")
    source = source.replace(replay_guard_old, replay_guard_new, 1)

# Production-world #283 starts the bounded walk with exact native carry on carriage 2 and stays
# exact through ticks 36-38. At tick 39 the same Create carriage frame moves -13.180 blocks,
# the LocalPlayer remains grounded and broadphase-overlapping, but strict simplified support is
# lost before Phase85 can replay because Phase133's one-tick grace is keyed only to a previous
# compatibility replay. The previous tick nevertheless has an authoritative healthy native-carry
# sample. Treat exactly that first support-loss tick as the existing bounded replay grace. This
# does not invent or clamp a vector: Phase85 still uses Create's own contact motion passed through
# Create collision filtering. The grace cannot repeat because the healthy-sample tick must equal
# player.tickCount - 1, and the existing grace-consumption/rebase guards remain intact.
native_loss_grace_old = '''boolean phase133ReplayGrace = productionSmoke && explicitCarryCompat
            && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()
            && !phase81PhysicalSupport && player.onGround()
            && carryReplayPlayerTick == player.tickCount - 1
            && phase133LastGraceReplayTick != carryReplayPlayerTick;'''
native_loss_grace_new = '''boolean phase159PreviousNativeHealthy = Boolean.parseBoolean(System.getProperty(
            "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
            && Integer.toString(player.tickCount - 1).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()));
        boolean phase133ReplayGrace = productionSmoke && explicitCarryCompat
            && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()
            && !phase81PhysicalSupport && player.onGround() && broadphaseOverlap
            && (carryReplayPlayerTick == player.tickCount - 1 || phase159PreviousNativeHealthy)
            && phase133LastGraceReplayTick != player.tickCount;
        if (phase159PreviousNativeHealthy && phase133ReplayGrace) {
            LOGGER.info(
                "GATE_E_PHASE159_NATIVE_LOSS_REPLAY_GRACE carriage_id={} player_tick={} previous_native_tick={} strict_support=false broadphase=true grounded=true bounded_one_tick=true existing_create_filtered_replay=true",
                carriage.getId(), player.tickCount, player.tickCount - 1);
        }'''
if "GATE_E_PHASE159_NATIVE_LOSS_REPLAY_GRACE" not in source:
    if source.count(native_loss_grace_old) != 1:
        raise SystemExit("Phase 158 expected exactly one Phase133 replay-grace declaration")
    source = source.replace(native_loss_grace_old, native_loss_grace_new, 1)

required = [
    "phase150SupportReacquired",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "phase154Step > 0.75",
    "GATE_E_PHASE158_WALK_NATIVE_READY",
    "phase158FreshNativeCarry",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "phase154SupportNow && phase158FreshNativeCarry",
    "phase158LocomotionHealthHold",
    "phase134DriftSq <= 0.5625",
    "GATE_E_PHASE158_LOCOMOTION_HEALTH_REJECT",
    "compatibility_recovery_allowed=true",
    "carryBaselineRebaseTick == Integer.MIN_VALUE",
    "player.tickCount - carryBaselineRebaseTick >= 2",
    "phase159PreviousNativeHealthy",
    "GATE_E_PHASE159_NATIVE_LOSS_REPLAY_GRACE",
    "broadphaseOverlap",
    "existing_create_filtered_replay=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 158 lost bounded native-carry recovery anchors: " + ", ".join(missing))

if "productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished" in source:
    raise SystemExit("Phase 158 must not suppress compatibility recovery for the whole walk")

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if (forbidden in health_new or forbidden in walk_start_new or forbidden in replay_guard_new
            or forbidden in native_loss_grace_new):
        raise SystemExit("Phase 158 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 158: starts walk after fresh native carry, blocks duplicate handoff replay, and permits one Create-filtered replay on the first native-support loss tick")
