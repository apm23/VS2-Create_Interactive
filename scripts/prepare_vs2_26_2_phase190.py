#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #581 proved the sibling-first boundary after fixture walk start. Production-world
# #686 proved the same native ownership bug can happen before walking: one carriage publishes the
# first exact Create-native application, then a stale sibling applies another return in the same
# LocalPlayer tick. Production-world #706 exposed the inverse handoff boundary: after the tracked
# active carriage rebases from 8 to 10, stale carriage 8 can still publish first in tick 18 and the
# old same-tick de-dup then incorrectly rejects carriage 10 even though 10 is now the tracked active
# frame. Preserve pre-walk first-owner de-dup, but once walk ownership exists let the tracked active
# carriage win over a stale same-tick sibling. A later non-active sibling is still rejected.
#
# This only rejects an extra duplicate Create return with ZERO. It does not synthesize movement,
# replay carry, teleport/setPos, mutate trains/world state, alter collision response, or alter VS2
# physics.

expected = '''            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick);
'''
replacement = '''            String phase190NativeApplicationTick = System.getProperty("vs2.phase170NativeContactApplicationTick");
            String phase190NativeApplicationCarriageId = System.getProperty("vs2.phase170NativeContactApplicationCarriageId");
            boolean phase190CurrentActiveNativeOwner = phase172FixtureWalkActive
                && phase172ActiveCarriageId.equals(Integer.toString(self.getId()));
            boolean phase190OtherNativeAlreadyAppliedThisTick = Integer.toString(phase170Player.tickCount).equals(phase190NativeApplicationTick)
                && phase190NativeApplicationCarriageId != null
                && !Integer.toString(self.getId()).equals(phase190NativeApplicationCarriageId)
                && !phase190CurrentActiveNativeOwner;
            boolean phase190ActiveNativePreviousTick = phase172FixtureWalkActive
                && Integer.toString(phase170Player.tickCount - 1).equals(phase190NativeApplicationTick)
                && phase172ActiveCarriageId.equals(phase190NativeApplicationCarriageId);
            boolean phase172DuplicateSiblingNativeCarry = phase190OtherNativeAlreadyAppliedThisTick
                || (phase172NonActiveSibling
                    && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick || phase190ActiveNativePreviousTick));
'''
if "phase190OtherNativeAlreadyAppliedThisTick" not in contact_source:
    if contact_source.count(expected) != 1:
        raise SystemExit("Phase 190 expected the native-health-based Phase172 sibling de-dup predicate")
    contact_source = contact_source.replace(expected, replacement, 1)

log_old = '''                    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} active_already_applied={} active_healthy_previous_tick={} sibling_first_guard={} fixture_only=true hypothesis_guard=true",
                    phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion,
                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick,
                    !phase172ActiveAlreadyAppliedThisTick && phase172ActiveHealthyPreviousTick);'''
log_new = '''                    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} active_already_applied={} active_healthy_previous_tick={} active_native_previous_tick={} other_native_same_tick={} sibling_first_guard={} fixture_only=true hypothesis_guard=true",
                    phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion,
                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick, phase190ActiveNativePreviousTick,
                    phase190OtherNativeAlreadyAppliedThisTick,
                    phase190OtherNativeAlreadyAppliedThisTick || (!phase172ActiveAlreadyAppliedThisTick && (phase172ActiveHealthyPreviousTick || phase190ActiveNativePreviousTick)));'''
if "other_native_same_tick={}" not in contact_source:
    if contact_source.count(log_old) != 1:
        raise SystemExit("Phase 190 expected exactly one Phase172 sibling suppression log")
    contact_source = contact_source.replace(log_old, log_new, 1)

required = [
    "phase172ActiveAlreadyAppliedThisTick",
    "phase172ActiveHealthyPreviousTick",
    "phase190CurrentActiveNativeOwner",
    "phase190OtherNativeAlreadyAppliedThisTick",
    "phase190ActiveNativePreviousTick",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "other_native_same_tick={}",
    "active_native_previous_tick={}",
    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED",
    "cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO)",
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
]
missing = [token for token in required if token not in contact_source]
if missing:
    raise SystemExit("Phase 190 lost native sibling de-dup anchors: " + ", ".join(missing))

for forbidden in [
    "phase190ActiveSupportedPreviousTick",
    "GATE_E_PHASE190_SUPPORTED_REPLAY_SIBLING_CARRY_SUPPRESSED",
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in replacement:
        raise SystemExit("Phase 190 introduced forbidden gameplay mutation: " + forbidden)

contact_trace.write_text(contact_source, encoding="utf-8")
print("Phase 190: de-dups stale same-tick siblings while allowing the tracked active carriage to own a native handoff")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase191.py")), run_name="__main__")
