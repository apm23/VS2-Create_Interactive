#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #581 proved the sibling-first boundary after fixture walk start. Production-world
# #686 now proves the same native ownership bug can happen before walking: at tick 19 carriage 5
# publishes the first exact Create-native application, then stale sibling carriage 7 applies its own
# ~8.95-block contact motion in the same LocalPlayer tick and throws the player off support before
# walk readiness can settle. The existing Phase190 guard cannot see that case because its active
# carriage identity is only established once the fixture walk starts.
#
# Reuse the exact native application tick/carriage already published by Phase170. Once one Create
# carriage has applied native contact motion in the current LocalPlayer tick, reject only a second
# different carriage's native return in that same tick. The first Create-native owner remains
# authoritative, and a sole next-tick sibling handoff is still admitted. This only rejects the extra
# duplicate return with ZERO; it does not synthesize movement, replay carry, teleport/setPos, mutate
# trains/world state, alter collision response, or alter VS2 physics.

expected = '''            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick);
'''
replacement = '''            String phase190NativeApplicationTick = System.getProperty("vs2.phase170NativeContactApplicationTick");
            String phase190NativeApplicationCarriageId = System.getProperty("vs2.phase170NativeContactApplicationCarriageId");
            boolean phase190OtherNativeAlreadyAppliedThisTick = Integer.toString(phase170Player.tickCount).equals(phase190NativeApplicationTick)
                && phase190NativeApplicationCarriageId != null
                && !Integer.toString(self.getId()).equals(phase190NativeApplicationCarriageId);
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
print("Phase 190: de-dups a second different Create-native carriage in the same player tick, including pre-walk")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase191.py")), run_name="__main__")
