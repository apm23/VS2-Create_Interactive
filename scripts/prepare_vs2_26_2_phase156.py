#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #272 proved the extended walk can legitimately transfer the active
# carry baseline across sibling Create carriage entities (5 -> 4 -> 2) while remaining
# grounded and broadphase-supported. Phase154 treated any carriage-id change as immediate
# failure, which conflates valid train-internal handoff with actual drift. Make the proof
# handoff-aware, but keep it strict: reset the local-step baseline only on the exact tick
# where Phase133 has rebased carryBaselineCarriageId. Run #288 additionally proved the first
# sample after an exact compatibility replay is an accounting seam: tick 35 replayed the
# missing 1.074921-block carriage carry, tick 36 immediately measured native carry healthy
# with drift_sq ~1e-9, yet the local-frame sampler reported a 1.074957 step because it
# observes that previous replay one callback later. Discount only that one-frame seam when
# the previous tick was a replay and the current authoritative native-health sample is fresh.
# Production-world #446 then proved a larger 2.079940 local-transform discontinuity can occur
# while the same carriage immediately enters a ten-sample zero-span sustained carry interval,
# remains grounded/broadphase-valid, and later records real 0.3001-block locomotion. Therefore
# a >0.75 verifier step is not itself evidence that physical support was lost. Leave such a
# step excluded from Phase182 accumulated walk distance, but do not permanently poison the
# support-health latch unless actual Phase154 support_now is false. Production-world #550
# additionally proved the walk can arm from valid native carry at tick 23 and then observe one
# first-sample transform seam at tick 24: the same carriage remains broadphase-overlapping but
# its end-frame local sample jumps 11.1 blocks and onGround is transiently false for that one
# callback, before grounded support is reacquired on tick 25 and sustained carry is proven on
# the sibling carriage. Treat only that first post-start, same-carriage, broadphase-valid,
# >0.75 local jump as an accounting seam instead of permanently poisoning support health.
# Fixture/gate accounting only; no player movement, carry vector, collision, train/world state,
# or VS2 physics changes.
old = '''                            if (phase154Carriage.getId() != phase154WalkCarriageId || !phase154SupportNow) {
                                phase154WalkSupportHealthy = false;
                            }
                            double phase154Step = phase154WalkPreviousLocal == null
                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);
                            phase154WalkPreviousLocal = phase154Local;
'''
new = '''                            boolean phase156SiblingHandoff = phase154Carriage.getId() != phase154WalkCarriageId
                                && phase154Carriage.getId() == carryBaselineCarriageId
                                && carryBaselineRebaseTick == player.tickCount
                                && phase154SupportNow;
                            double phase154Step = phase154WalkPreviousLocal == null || phase156SiblingHandoff
                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);
                            if (phase156SiblingHandoff) {
                                LOGGER.info(
                                    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF player_tick={} previous_carriage_id={} carriage_id={} grounded={} broadphase={} baseline_rebase=true local_step_reset=true fixture_only=true",
                                    player.tickCount, phase154WalkCarriageId, phase154Carriage.getId(), player.onGround(), phase154Broadphase);
                                phase154WalkCarriageId = phase154Carriage.getId();
                            }
                            boolean phase160PreviousReplayAccountingSeam = !phase156SiblingHandoff
                                && phase154SupportNow
                                && carryReplayPlayerTick == player.tickCount - 1
                                && Boolean.parseBoolean(System.getProperty(
                                    "vs2.phase134NativeCarryHealthy." + phase154Carriage.getId(), "false"))
                                && Integer.toString(player.tickCount).equals(System.getProperty(
                                    "vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId()));
                            double phase160GuardStep = phase160PreviousReplayAccountingSeam ? 0.0 : phase154Step;
                            if (phase160PreviousReplayAccountingSeam) {
                                LOGGER.info(
                                    "GATE_E_PHASE160_WALK_REPLAY_ACCOUNTING_SEAM player_tick={} carriage_id={} measured_local_step={} previous_replay_tick={} current_native_healthy=true guard_step=0.0 read_only_accounting=true fixture_only=true",
                                    player.tickCount, phase154Carriage.getId(), phase154Step, carryReplayPlayerTick);
                            }
                            boolean phase156InitialStartFrameSeam = !phase154SupportNow
                                && phase154Broadphase
                                && phase154Carriage.getId() == phase154WalkCarriageId
                                && player.tickCount == phase154WalkStartTick + 1
                                && phase154Step > 0.75;
                            if (phase156InitialStartFrameSeam) {
                                LOGGER.info(
                                    "GATE_E_PHASE156_WALK_INITIAL_FRAME_SEAM player_tick={} carriage_id={} local_step={} grounded={} broadphase=true first_post_start=true support_health_preserved=true fixture_only=true read_only_accounting=true",
                                    player.tickCount, phase154Carriage.getId(), phase154Step, player.onGround());
                            }
                            if (!phase154SupportNow && !phase156InitialStartFrameSeam) {
                                phase154WalkSupportHealthy = false;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE156_WALK_FRAME_GUARD player_tick={} carriage_id={} local_step={} guard_step={} max_local_step=0.75 support_now={} sibling_handoff={} replay_accounting_seam={} initial_start_frame_seam={} support_healthy={} read_only=true",
                                player.tickCount, phase154Carriage.getId(), phase154Step, phase160GuardStep, phase154SupportNow,
                                phase156SiblingHandoff, phase160PreviousReplayAccountingSeam, phase156InitialStartFrameSeam,
                                phase154WalkSupportHealthy);
                            phase154WalkPreviousLocal = phase154Local;
'''
if "GATE_E_PHASE156_WALK_FRAME_GUARD" not in source:
    if old not in source:
        raise SystemExit("Phase 156 could not find Phase154 walk support guard")
    source = source.replace(old, new, 1)
elif "GATE_E_PHASE160_WALK_REPLAY_ACCOUNTING_SEAM" not in source:
    old_existing = '''                            boolean phase156SiblingHandoff = phase154Carriage.getId() != phase154WalkCarriageId
                                && phase154Carriage.getId() == carryBaselineCarriageId
                                && carryBaselineRebaseTick == player.tickCount
                                && phase154SupportNow;
                            double phase154Step = phase154WalkPreviousLocal == null || phase156SiblingHandoff
                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);
                            if (phase156SiblingHandoff) {
                                LOGGER.info(
                                    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF player_tick={} previous_carriage_id={} carriage_id={} grounded={} broadphase={} baseline_rebase=true local_step_reset=true fixture_only=true",
                                    player.tickCount, phase154WalkCarriageId, phase154Carriage.getId(), player.onGround(), phase154Broadphase);
                                phase154WalkCarriageId = phase154Carriage.getId();
                            }
                            if (!phase154SupportNow || phase154Step > 0.75) {
                                phase154WalkSupportHealthy = false;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE156_WALK_FRAME_GUARD player_tick={} carriage_id={} local_step={} max_local_step=0.75 support_now={} sibling_handoff={} support_healthy={} read_only=true",
                                player.tickCount, phase154Carriage.getId(), phase154Step, phase154SupportNow,
                                phase156SiblingHandoff, phase154WalkSupportHealthy);
                            phase154WalkPreviousLocal = phase154Local;
'''
    if old_existing not in source:
        raise SystemExit("Phase 160 could not find Phase156 walk frame guard")
    source = source.replace(old_existing, new, 1)

required = [
    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF",
    "GATE_E_PHASE156_WALK_FRAME_GUARD",
    "GATE_E_PHASE156_WALK_INITIAL_FRAME_SEAM",
    "carryBaselineRebaseTick == player.tickCount",
    "phase156InitialStartFrameSeam",
    "player.tickCount == phase154WalkStartTick + 1",
    "if (!phase154SupportNow && !phase156InitialStartFrameSeam)",
    "phase160GuardStep",
    "phase154WalkCarriageId = phase154Carriage.getId()",
    "local_step_reset=true",
    "max_local_step=0.75",
    "GATE_E_PHASE160_WALK_REPLAY_ACCOUNTING_SEAM",
    "carryReplayPlayerTick == player.tickCount - 1",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "current_native_healthy=true",
    "guard_step=0.0",
    "support_health_preserved=true",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 156 lost handoff/replay-accounting walk anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in new:
        raise SystemExit("Phase 156 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 156/160: keeps support health tied to real support loss while ignoring the proven first-frame verifier seam")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase157.py")), run_name="__main__")
