#!/usr/bin/env python3
from pathlib import Path

script = Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_wall_fixture_window.py")
source = script.read_text(encoding="utf-8")

marker = "M1_CURRENT_COORDINATE_AGNOSTIC_WALL_FIXTURE_COMPOSER"
if marker not in source:
    start = source.index("replacements = [")
    end = source.index("\nfixture_input.write_text", start)
    new_block = '''# M1_CURRENT_COORDINATE_AGNOSTIC_WALL_FIXTURE_COMPOSER
replacements = [
    (
        'after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+9, request_tick-1) and s[5] and s[6] and s[7]]',
        'after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+14, request_tick-1) and s[5] and s[6] and s[7]]',
    ),
    (
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)',
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)',
    ),
    (
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02\\nmaterial_approach = start_z-min_z >= 0.015',
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) >= 0.02\\nmaterial_approach = max_z-start_z >= 0.015',
    ),
    (
        'if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):',
        'if stable_plateau and (max(candidate_z)-start_z>=0.015 or strafe_requested_toward_wall):',
    ),
]
for old, new in replacements:
    old_count = verifier_source.count(old)
    new_count = verifier_source.count(new)
    if old_count == 1 and new_count == 0:
        verifier_source = verifier_source.replace(old, new, 1)
    elif old_count == 0 and new_count == 1:
        # An earlier composer already produced the exact target boundary. Preserve it.
        pass
    else:
        raise SystemExit(
            "M1 wall fixture lost both legacy and target verifier boundaries: " + old[:80]
        )'''
    source = source[:start] + new_block + source[end:]
    print("M1 wall fixture source compatibility: made coordinate-agnostic window/direction composition idempotent")
else:
    print("M1 wall fixture source compatibility already applied")

# Phase205 is intentionally composed before this wall-fixture pass executes. It adds a
# same-tick pre-collision reanchor guard to Phase83's grounded support gap so the old
# END_CLIENT_TICK bridge cannot repeat the frame transform that already ran before Create OBB.
# Keep the Phase83 owner/lease hardening below intact, but teach its source matcher the exact
# Phase205-composed shape. This changes only composer expectations; it does not remove either
# Phase205 de-duplication or Phase83 sibling-owner arbitration.
phase205_marker = "M1_PHASE205_COMPOSITION_AWARE_WALL_FIXTURE"
if phase205_marker not in source:
    old_gap_old = """phase83_gap_old = '''            boolean phase83GroundedSupportGap = player.onGround()\n                && phase81PhysicalSupport\n                && phase83CurrentEnvelopeEligible\n                && !phase83NativeAppliedThisTick;\n            boolean phase83NativeFrameEligible = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);\n            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);'''"""
    composed_gap_old = """# M1_PHASE205_COMPOSITION_AWARE_WALL_FIXTURE\nphase83_gap_old = '''            boolean phase205PreCollisionReanchoredThisTick = Integer.toString(player.tickCount).equals(\n                System.getProperty(\"vs2.phase205PreCollisionReanchorTick.\" + carriage.getId()));\n            boolean phase83GroundedSupportGap = player.onGround()\n                && phase81PhysicalSupport\n                && phase83CurrentEnvelopeEligible\n                && !phase83NativeAppliedThisTick\n                && !phase205PreCollisionReanchoredThisTick;\n            boolean phase83NativeFrameEligible = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);\n            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);'''"""
    if source.count(old_gap_old) != 1:
        raise SystemExit("M1 wall fixture Phase205 compatibility expected one legacy Phase83 old matcher")
    source = source.replace(old_gap_old, composed_gap_old, 1)

    old_gap_new = """phase83_gap_new = '''            String phase83ActiveNativeOwner = System.getProperty(\n                \"vs2.phase170NativeContactApplicationCarriageId\");\n            boolean phase83GroundedSupportGap = player.onGround()\n                && phase81PhysicalSupport\n                && phase83CurrentEnvelopeEligible\n                && !phase83NativeAppliedThisTick;\n            boolean phase83GroundedNativeBaselineLease = player.onGround()\n                && phase83ExactBaselineCarriage\n                && Integer.toString(carriage.getId()).equals(phase83ActiveNativeOwner)\n                && (createRegisteredContact || (phase83NativeApplicationAge >= 1 && phase83NativeApplicationAge <= 2))\n                && phase83CurrentEnvelopeEligible\n                && !phase83NativeAppliedThisTick;\n            boolean phase83NativeFrameEligible = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83GroundedNativeBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);\n            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83GroundedNativeBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);'''"""
    composed_gap_new = """phase83_gap_new = '''            boolean phase205PreCollisionReanchoredThisTick = Integer.toString(player.tickCount).equals(\n                System.getProperty(\"vs2.phase205PreCollisionReanchorTick.\" + carriage.getId()));\n            String phase83ActiveNativeOwner = System.getProperty(\n                \"vs2.phase170NativeContactApplicationCarriageId\");\n            boolean phase83GroundedSupportGap = player.onGround()\n                && phase81PhysicalSupport\n                && phase83CurrentEnvelopeEligible\n                && !phase83NativeAppliedThisTick\n                && !phase205PreCollisionReanchoredThisTick;\n            boolean phase83GroundedNativeBaselineLease = player.onGround()\n                && phase83ExactBaselineCarriage\n                && Integer.toString(carriage.getId()).equals(phase83ActiveNativeOwner)\n                && (createRegisteredContact || (phase83NativeApplicationAge >= 1 && phase83NativeApplicationAge <= 2))\n                && phase83CurrentEnvelopeEligible\n                && !phase83NativeAppliedThisTick\n                && !phase205PreCollisionReanchoredThisTick;\n            boolean phase83NativeFrameEligible = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83GroundedNativeBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);\n            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick\n                && (phase83GroundedSupportGap || phase83GroundedNativeBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);'''"""
    if source.count(old_gap_new) != 1:
        raise SystemExit("M1 wall fixture Phase205 compatibility expected one legacy Phase83 replacement")
    source = source.replace(old_gap_new, composed_gap_new, 1)
    script.write_text(source, encoding="utf-8")
    print("M1 wall fixture source compatibility: retained Phase205 pre-collision de-dup across Phase83 owner/lease composition")
elif "!phase205PreCollisionReanchoredThisTick" not in source:
    raise SystemExit("M1 wall fixture Phase205 compatibility marker exists without de-dup predicate")
else:
    print("M1 wall fixture Phase205 source compatibility already applied")
