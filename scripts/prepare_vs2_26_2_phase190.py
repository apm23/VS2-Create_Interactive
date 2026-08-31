#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world run 33346982377 proved a sibling-first native carry at walk tick 30 while
# baseline carriage 8 had remained grounded, broadphase-overlapping, and strictly supported on
# tick 29 through the existing Create-filtered recovery replay. Phase172 only recognized a
# sibling-first duplicate when the active carriage was native-healthy on the previous tick, so
# carriage 7's -2.31458 native motion escaped and produced a 3.72816-block local discontinuity.
# Phase189 already publishes the bounded walk baseline support state each tick. Extend the
# fixture-only sibling suppression to the immediately following tick when that same active
# baseline was strictly supported, without synthesizing/clamping motion or changing production
# train/physics behavior outside the disposable production smoke fixture.

healthy_old = '''            boolean phase172ActiveHealthyPreviousTick = phase172FixtureWalkActive
                && java.lang.Boolean.parseBoolean(System.getProperty(
                    "vs2.phase134NativeCarryHealthy." + phase172ActiveCarriageId, "false"))
                && Integer.toString(phase170Player.tickCount - 1).equals(System.getProperty(
                    "vs2.phase134NativeCarryHealthyTick." + phase172ActiveCarriageId));
            boolean phase172NonActiveSibling = phase172FixtureWalkActive
'''
healthy_new = '''            boolean phase172ActiveHealthyPreviousTick = phase172FixtureWalkActive
                && java.lang.Boolean.parseBoolean(System.getProperty(
                    "vs2.phase134NativeCarryHealthy." + phase172ActiveCarriageId, "false"))
                && Integer.toString(phase170Player.tickCount - 1).equals(System.getProperty(
                    "vs2.phase134NativeCarryHealthyTick." + phase172ActiveCarriageId));
            boolean phase190ActiveSupportedPreviousTick = phase172FixtureWalkActive
                && Integer.toString(phase170Player.tickCount - 1).equals(System.getProperty("vs2.phase189BaselineSupportTick"))
                && java.lang.Boolean.parseBoolean(System.getProperty("vs2.phase189BaselineSupportHealthy", "false"))
                && phase172ActiveCarriageId.equals(System.getProperty("vs2.phase189BaselineSupportCarriageId"));
            boolean phase172NonActiveSibling = phase172FixtureWalkActive
'''
if "phase190ActiveSupportedPreviousTick" not in contact_source:
    if contact_source.count(healthy_old) != 1:
        raise SystemExit("Phase 190 expected exactly one Phase172 previous-health anchor")
    contact_source = contact_source.replace(healthy_old, healthy_new, 1)

condition_old = '''            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick);
'''
condition_new = '''            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick
                    || phase190ActiveSupportedPreviousTick);
'''
if "|| phase190ActiveSupportedPreviousTick" not in contact_source:
    if contact_source.count(condition_old) != 1:
        raise SystemExit("Phase 190 expected exactly one Phase172 sibling suppression predicate")
    contact_source = contact_source.replace(condition_old, condition_new, 1)

log_old = '''                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick,
                    !phase172ActiveAlreadyAppliedThisTick && phase172ActiveHealthyPreviousTick);
'''
log_new = '''                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick,
                    !phase172ActiveAlreadyAppliedThisTick && (phase172ActiveHealthyPreviousTick || phase190ActiveSupportedPreviousTick));
                if (phase190ActiveSupportedPreviousTick && !phase172ActiveHealthyPreviousTick) {
                    LOGGER.info(
                        "GATE_E_PHASE190_SUPPORTED_REPLAY_SIBLING_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} previous_baseline_support=true fixture_only=true bounded_one_tick=true",
                        phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion);
                }
'''
if "GATE_E_PHASE190_SUPPORTED_REPLAY_SIBLING_CARRY_SUPPRESSED" not in contact_source:
    if contact_source.count(log_old) != 1:
        raise SystemExit("Phase 190 expected exactly one Phase172 suppression log tail")
    contact_source = contact_source.replace(log_old, log_new, 1)

required = [
    "phase190ActiveSupportedPreviousTick",
    "vs2.phase189BaselineSupportTick",
    "vs2.phase189BaselineSupportHealthy",
    "vs2.phase189BaselineSupportCarriageId",
    "|| phase190ActiveSupportedPreviousTick",
    "GATE_E_PHASE190_SUPPORTED_REPLAY_SIBLING_CARRY_SUPPRESSED",
    "cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO)",
    "fixture_only=true",
    "bounded_one_tick=true",
]
missing = [token for token in required if token not in contact_source]
if missing:
    raise SystemExit("Phase 190 lost supported-replay sibling suppression anchors: " + ", ".join(missing))

# This phase only broadens the existing fixture-only cancellation predicate. It must not move the
# player directly or mutate trains, blocks/world state, inventory, or VS2 physics.
inserted = healthy_new + condition_new + log_new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 190 introduced forbidden gameplay mutation token: " + forbidden)

contact_trace.write_text(contact_source, encoding="utf-8")
print("Phase 190: suppresses one-tick sibling native carry after strict active-baseline support survived via existing recovery replay")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase191.py")), run_name="__main__")
