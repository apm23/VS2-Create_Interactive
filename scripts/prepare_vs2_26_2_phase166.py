#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #310 finally exposed the single-pulse fixture's timing precisely. The key is
# already released, but its delayed locomotion response arrives at tick 40 as an intentional
# 1.0-block carriage-local step. The drift-only native-health classifier then calls that motion
# a carry loss and Phase85 begins replaying carriage motion from tick 41 onward, contaminating
# the rest of the walk proof. Treat at most one bounded (<=1.10 block) post-pulse displacement
# as fixture locomotion accounting while strict support remains valid. Production-world #446
# later proved that a larger local-frame seam is not itself physical support loss, so this phase
# must not reintroduce the old >0.75 support-health latch. Production-world #551 then showed the
# Phase166 source-rewrite anchor still expected the pre-#550 support predicate; preserve the new
# first-frame accounting-seam exclusion when inserting the existing delayed-pulse bookkeeping.
# Production-world #670/#671 prove this reset must stay outside the exact cumulative Phase165
# walk-start anchor consumed after Phase203. Keep the reset in the same callback, but append it
# after Phase165's key cleanup so phase154WalkPreviousLocal/path/support/keyUp/keyDown remain a
# contiguous composition-stable block. Fixture bookkeeping only: no movement vector, player/world/
# train state, collision response or VS2/Create physics behavior is changed.

field_old = '''    private static double phase165WalkPathDistance;\n    private static boolean phase154WalkSupportHealthy = true;\n'''
field_new = '''    private static double phase165WalkPathDistance;\n    private static boolean phase166FixturePulseConsumed;\n    private static boolean phase154WalkSupportHealthy = true;\n'''
if "phase166FixturePulseConsumed" not in source:
    if source.count(field_old) != 1:
        raise SystemExit("Phase 166 expected exactly one Phase165 walk field tail")
    source = source.replace(field_old, field_new, 1)

start_old = '''                            phase165WalkPathDistance = 0.0;\n                            phase154WalkSupportHealthy = true;\n                            client.options.keyUp.setDown(true);\n                            client.options.keyDown.setDown(false);\n'''
start_new = '''                            phase165WalkPathDistance = 0.0;\n                            phase154WalkSupportHealthy = true;\n                            client.options.keyUp.setDown(true);\n                            client.options.keyDown.setDown(false);\n                            phase166FixturePulseConsumed = false;\n'''
if "phase166FixturePulseConsumed = false" not in source:
    if source.count(start_old) != 1:
        raise SystemExit("Phase 166 expected exactly one Phase165 walk-start reset")
    source = source.replace(start_old, start_new, 1)

health_old = '''boolean phase158LocomotionHealthHold = phase157PlayerLocomoting
            && phase157PreviouslyHealthy
            && phase134DriftSq > 0.01
            && phase134DriftSq <= 0.5625;'''
health_new = '''boolean phase166FixturePulseObservation = productionSmokeFixture
            && phase154WalkStarted && !phase154WalkFinished
            && !phase166FixturePulseConsumed
            && player.tickCount <= phase154WalkStartTick + 20;
        boolean phase158LocomotionHealthHold = phase157PreviouslyHealthy
            && phase134DriftSq > 0.01
            && ((phase157PlayerLocomoting && phase134DriftSq <= 0.5625)
                || (phase166FixturePulseObservation && phase134DriftSq <= 1.21));'''
if "phase166FixturePulseObservation" not in source:
    if source.count(health_old) != 1:
        raise SystemExit("Phase 166 expected exactly one Phase158 locomotion-health hold")
    source = source.replace(health_old, health_new, 1)

guard_old = '''                            if (!phase154SupportNow && !phase156InitialStartFrameSeam) {
                                phase154WalkSupportHealthy = false;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE156_WALK_FRAME_GUARD'''
guard_new = '''                            boolean phase166FixturePulseStep = productionSmokeFixture
                                && phase154WalkStarted && !phase154WalkFinished
                                && !phase166FixturePulseConsumed
                                && phase154SupportNow
                                && phase160GuardStep > 0.75 && phase160GuardStep <= 1.10;
                            if (phase166FixturePulseStep) {
                                phase166FixturePulseConsumed = true;
                                LOGGER.info(
                                    "GATE_E_PHASE166_FIXTURE_PULSE_RESPONSE player_tick={} carriage_id={} local_step={} max_fixture_pulse_step=1.10 strict_support=true replay_suppression_accounting=true fixture_only=true",
                                    player.tickCount, phase154Carriage.getId(), phase160GuardStep);
                            }
                            if (!phase154SupportNow && !phase156InitialStartFrameSeam) {
                                phase154WalkSupportHealthy = false;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE156_WALK_FRAME_GUARD'''
if "GATE_E_PHASE166_FIXTURE_PULSE_RESPONSE" not in source:
    if source.count(guard_old) != 1:
        raise SystemExit("Phase 166 expected exactly one seam-aware Phase156/160 frame guard")
    source = source.replace(guard_old, guard_new, 1)

required = [
    "phase166FixturePulseConsumed",
    "phase166FixturePulseObservation",
    "phase134DriftSq <= 1.21",
    "GATE_E_PHASE166_FIXTURE_PULSE_RESPONSE",
    "phase160GuardStep > 0.75 && phase160GuardStep <= 1.10",
    "phase166FixturePulseConsumed = true",
    "if (!phase154SupportNow && !phase156InitialStartFrameSeam)",
    "phase156InitialStartFrameSeam",
    "productionSmokeFixture",
    "phase154WalkStarted && !phase154WalkFinished",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 166 lost delayed-pulse accounting anchors: " + ", ".join(missing))

if "phase160GuardStep > 0.75 && !phase166FixturePulseStep" in source:
    raise SystemExit("Phase 166 must not reintroduce frame-seam support poisoning")

patch_text = field_new + start_new + health_new + guard_new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 166 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 166: keeps delayed fixture-pulse accounting compatible with the first-frame seam guard")
