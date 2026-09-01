#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #553 proved the old Phase190 support-only widening cancels the only native
# Create carry available at the route/frame handoff. At tick 34 the tracked active carriage 4 had
# neither applied native motion this tick nor been native-healthy on tick 33, yet carriage 2's
# genuine -7.9393509626 Create contact motion was zeroed solely because the old baseline had been
# supported on the previous tick. The player then missed the moving frame and fell out of support.
#
# Keep Phase172's narrower de-dup rule: suppress a sibling only after the active carriage already
# applied this tick, or when that active carriage was genuinely native-healthy on the previous tick.
# Previous support alone is not authority to discard a fresh Create-native carrier. This removes a
# fixture-only cancellation; it does not synthesize/clamp movement, replay carry, teleport/setPos,
# mutate the train/world, or alter VS2 physics.

expected = '''            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling
                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick);
'''
if contact_source.count(expected) != 1:
    raise SystemExit("Phase 190 expected the native-health-based Phase172 sibling de-dup predicate")

for forbidden in [
    "phase190ActiveSupportedPreviousTick",
    "GATE_E_PHASE190_SUPPORTED_REPLAY_SIBLING_CARRY_SUPPRESSED",
    "|| phase190ActiveSupportedPreviousTick",
]:
    if forbidden in contact_source:
        raise SystemExit("Phase 190 must not suppress a native sibling from previous support alone: " + forbidden)

required = [
    "phase172ActiveAlreadyAppliedThisTick",
    "phase172ActiveHealthyPreviousTick",
    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED",
    "cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO)",
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
]
missing = [token for token in required if token not in contact_source]
if missing:
    raise SystemExit("Phase 190 lost native sibling de-dup anchors: " + ", ".join(missing))

print("Phase 190: preserves native sibling carry unless the active frame has genuine duplicate-carry evidence")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase191.py")), run_name="__main__")
