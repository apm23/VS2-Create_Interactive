#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #581 proved the remaining sibling-first boundary directly. The tracked active
# carriage 7 was exact-native at tick 36. At tick 37 sibling carriage 5 then returned -4.8346 before
# active carriage 7 returned its exact +2.0521 frame motion. Phase172 allowed the sibling because
# Phase134's drift classifier had already turned false from intentional walk input, even though the
# exact previous-tick native owner was still carriage 7. The player consequently moved ~4.89 blocks
# backward in carriage-local space in one tick. Reuse the already-published exact native owner/tick
# at this same Create boundary: previous-tick active native ownership is genuine duplicate-carry
# evidence and is independent of intentional player locomotion. This only rejects the extra sibling
# return with ZERO; it does not synthesize movement, replay carry, teleport/setPos, mutate trains or
# world state, or alter VS2 physics.

expected = '''            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick);
'''
replacement = '''            boolean phase190ActiveNativePreviousTick = phase172FixtureWalkActive
                && Integer.toString(phase170Player.tickCount - 1).equals(System.getProperty("vs2.phase170NativeContactApplicationTick"))
                && phase172ActiveCarriageId.equals(System.getProperty("vs2.phase170NativeContactApplicationCarriageId"));
            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick || phase190ActiveNativePreviousTick);
'''
if "phase190ActiveNativePreviousTick" not in contact_source:
    if contact_source.count(expected) != 1:
        raise SystemExit("Phase 190 expected the native-health-based Phase172 sibling de-dup predicate")
    contact_source = contact_source.replace(expected, replacement, 1)

log_old = '''                    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} active_already_applied={} active_healthy_previous_tick={} sibling_first_guard={} fixture_only=true hypothesis_guard=true",
                    phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion,
                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick,
                    !phase172ActiveAlreadyAppliedThisTick && phase172ActiveHealthyPreviousTick);'''
log_new = '''                    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} active_already_applied={} active_healthy_previous_tick={} active_native_previous_tick={} sibling_first_guard={} fixture_only=true hypothesis_guard=true",
                    phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion,
                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick, phase190ActiveNativePreviousTick,
                    !phase172ActiveAlreadyAppliedThisTick && (phase172ActiveHealthyPreviousTick || phase190ActiveNativePreviousTick));'''
if "active_native_previous_tick={}" not in contact_source:
    if contact_source.count(log_old) != 1:
        raise SystemExit("Phase 190 expected exactly one Phase172 sibling suppression log")
    contact_source = contact_source.replace(log_old, log_new, 1)

required = [
    "phase172ActiveAlreadyAppliedThisTick",
    "phase172ActiveHealthyPreviousTick",
    "phase190ActiveNativePreviousTick",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
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
print("Phase 190: de-dups sibling-first native carry from the exact previous-tick active native owner")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase191.py")), run_name="__main__")
