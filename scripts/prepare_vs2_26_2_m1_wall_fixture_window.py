#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
verifier = Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_jump_proof.py")
source = fixture_input.read_text(encoding="utf-8")
client_source = client_probe.read_text(encoding="utf-8")
verifier_source = verifier.read_text(encoding="utf-8")

# Production-world #693 starts the disposable forward pulse at tick 17 after only two stationary
# supported samples (ticks 15-16), while the production carry gate intentionally requires five.
# That makes the standing-before-walk proof impossible before locomotion changes contact ownership.
# Production-world #695 then proves the three sampled sprint ticks (start+4..+6) are consumed one
# callback before material horizontal movement becomes visible: the first real local displacement is
# observed at start+7, exactly when the old follow-up sequencer took over and released sprint. Keep
# the vanilla forward+sprint KeyMappings alive through that observed movement callback, then allow
# follow-up inputs on start+8. Harness timing only; no position, velocity, carry, collision, gravity,
# train state, or world state is synthesized.
walk_pulse_old = 'boolean pulse = self.tickCount >= startTick + 1 && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
walk_pulse_new = 'boolean pulse = self.tickCount >= startTick + 4 && self.tickCount <= startTick + 7 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
if source.count(walk_pulse_old) != 2:
    raise SystemExit("M1 standing carry sequencing expected two delayed forward pulse boundaries")
source = source.replace(walk_pulse_old, walk_pulse_new)

# Keep follow-up backward/strafe/jump sequencing strictly after the extended native sprint window.
walk_seen_old = '''            if (self.tickCount >= startTick + 4) {
                vs2$walkConfirmedTick = startTick + 4;
                return true;
            }'''
walk_seen_new = '''            if (self.tickCount >= startTick + 8) {
                vs2$walkConfirmedTick = startTick + 8;
                return true;
            }'''
if source.count(walk_seen_old) != 1:
    raise SystemExit("M1 sprint sequencing expected one early follow-up fallback boundary")
source = source.replace(walk_seen_old, walk_seen_new, 1)

# The immediately preceding M1 input-timing composition pass already owns Phase200's native
# applyInput pulse and rewrites it to the observed start+1..+3 sampling window. Do not mutate the
# same boundary a second time here: just assert that the composed source contains the intended
# unguarded Phase200 predicate exactly once. This keeps this wall-fixture pass independent from the
# earlier input-timing implementation detail and avoids a prepare-time false failure.
phase200_expected = 'boolean pulse = self.tickCount >= startTick + 1 && self.tickCount <= startTick + 3;'
if source.count(phase200_expected) != 1:
    raise SystemExit("M1 sprint alignment expected composed Phase200 start+1..+3 pulse predicate")

# Production-world #684 starts native right-strafe near local Z=+1.02, while the occupied +Z side
# is at Z=+2. The current post-composition fixture points toward the much farther -Z wall and jumps
# six ticks after the request, so it never reaches any wall: the run only moves to about Z=+0.73
# before jump. Aim the disposable vanilla right KeyMapping at the nearby occupied +Z wall and keep
# it active long enough to reach a real collision plateau before jump. Harness input/view timing
# only: no position, velocity, collision response, carry vector, gravity, train, or world state.
yaw_old = '''        if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE) {
            self.setYRot(90.0F);
        }'''
yaw_new = '''        if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE) {
            self.setYRot(-90.0F);
        }'''
if source.count(yaw_old) != 2:
    raise SystemExit("M1 wall fixture expected two final negative-Z orientation sites")
source = source.replace(yaw_old, yaw_new)

window_old = 'return strafeElapsed >= 0 && strafeElapsed <= 3;'
window_new = 'return strafeElapsed >= 0 && strafeElapsed <= 12;'
if source.count(window_old) != 1:
    raise SystemExit("M1 wall fixture expected one short strafe window")
source = source.replace(window_old, window_new, 1)

jump_old = 'self.tickCount >= vs2$strafeStartTick + 6'
jump_new = 'self.tickCount >= vs2$strafeStartTick + 15'
if source.count(jump_old) != 1:
    raise SystemExit("M1 wall fixture expected one short post-strafe jump delay")
source = source.replace(jump_old, jump_new, 1)

# Production-world #689 proves the grounded reference-frame bridge selected the stale baseline
# carriage through a sibling handoff. At tick 34 the player has strict physical support on carriage
# 5 and no same-tick Create native application, while baseline carriage 7 moved ~26.88 blocks away.
# Phase83 already computes the current supported Create candidate as phase83GroundedSupportGap.
# Let that validated current support own the existing VS2 previous->current frame bridge for only the
# native-gap tick. Same-tick native Create application still disables the bridge, so no synthetic
# carry, velocity, collision response, gravity, teleport, or extra world/train state is introduced.
#
# Production-world #691 proves physical support alone is not enough to choose a sibling: at tick 24
# the loop saw strict support on carriage 4 even though carriage 5 was the last Create-native owner
# through tick 23 and remained the walk/baseline carriage. Bridging carriage 4 applied the wrong
# authoritative frame and produced a ~15.37-block local discontinuity. Admit a non-baseline sibling
# only when its id matches Phase170's last native Create owner. This is ownership selection only;
# the carried transform remains Create previous->current through VS2 EntityDragger.
phase83_old = '''            if (Boolean.getBoolean("vs2.createCarryCompat")
                && phase83ExactBaselineCarriage
                && phase83NativeFrameEligible'''
phase83_new = '''            String phase83ActiveNativeOwner = System.getProperty(
                "vs2.phase170NativeContactApplicationCarriageId");
            boolean phase83GroundedNativeOwnerGap = phase83GroundedSupportGap
                && Integer.toString(carriage.getId()).equals(phase83ActiveNativeOwner);
            if (Boolean.getBoolean("vs2.createCarryCompat")
                && (phase83ExactBaselineCarriage || phase83GroundedNativeOwnerGap)
                && phase83NativeFrameEligible'''
if client_source.count(phase83_old) != 1:
    raise SystemExit("M1 grounded sibling bridge expected one Phase83 exact-baseline gate")
client_source = client_source.replace(phase83_old, phase83_new, 1)

# Production-world #690 proves the complementary same-carriage boundary. Carriage 10 has strict
# grounded support and uses the existing authoritative Create-frame -> VS2 EntityDragger bridge at
# tick 24, then the simplified-support sampler transiently reports false at tick 25 while the exact
# baseline carriage is still broadphase-valid and the player remains grounded. With no same-tick
# native Create application, Phase83 currently drops the frame for exactly that sampling gap and the
# player loses the full ~7.11-block carriage step. Lease only the immediately preceding supported
# baseline for one grounded tick. This is still the same previous->current Create frame transform;
# it adds no velocity, gravity, collision response, teleport, or train/world state.
phase83_gap_old = '''            boolean phase83GroundedSupportGap = player.onGround()
                && phase81PhysicalSupport
                && phase83CurrentEnvelopeEligible
                && !phase83NativeAppliedThisTick;
            boolean phase83NativeFrameEligible = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);
            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);'''
phase83_gap_new = '''            boolean phase83GroundedSupportGap = player.onGround()
                && phase81PhysicalSupport
                && phase83CurrentEnvelopeEligible
                && !phase83NativeAppliedThisTick;
            boolean phase83GroundedSupportedBaselineLease = player.onGround()
                && phase83ExactBaselineCarriage
                && phase83SupportedBaselineAge == 1
                && phase83CurrentEnvelopeEligible
                && !phase83NativeAppliedThisTick;
            boolean phase83NativeFrameEligible = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83GroundedSupportedBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);
            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83GroundedSupportedBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);'''
if client_source.count(phase83_gap_old) != 1:
    raise SystemExit("M1 grounded support-gap bridge expected one Phase83 eligibility block")
client_source = client_source.replace(phase83_gap_old, phase83_gap_new, 1)

phase83_final_old = '''                && phase83ExternalFrameLease
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease)) {'''
phase83_final_new = '''                && phase83ExternalFrameLease
                && (phase83GroundedSupportGap || phase83GroundedSupportedBaselineLease || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease)) {'''
if client_source.count(phase83_final_old) != 1:
    raise SystemExit("M1 grounded support-gap bridge expected one Phase83 final lease gate")
client_source = client_source.replace(phase83_final_old, phase83_final_new, 1)

# Keep the read-only proof aligned with the actual occupied side and the expanded pre-jump window.
replacements = [
    (
        'wall_geometry_seen = any(re.search(r"(?:^|\\|)-?\\d+, [123], -2(?:\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
        'wall_geometry_seen = any(re.search(r"(?:^|\\|)-?\\d+, [123], 2(?:\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
    ),
    (
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")',
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=2")',
    ),
    (
        'after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+9, request_tick-1) and s[5] and s[6] and s[7]]',
        'after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+14, request_tick-1) and s[5] and s[6] and s[7]]',
    ),
    (
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)\nif min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)\nif max_z>=2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
    ),
    (
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02\nmaterial_approach = start_z-min_z >= 0.015',
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) >= 0.02\nmaterial_approach = max_z-start_z >= 0.015',
    ),
    (
        'if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):',
        'if stable_plateau and (max(candidate_z)-start_z>=0.015 or strafe_requested_toward_wall):',
    ),
]
for old, new in replacements:
    if verifier_source.count(old) != 1:
        raise SystemExit("M1 wall fixture lost expected verifier boundary: " + old[:80])
    verifier_source = verifier_source.replace(old, new, 1)

fixture_input.write_text(source, encoding="utf-8")
client_probe.write_text(client_source, encoding="utf-8")
verifier.write_text(verifier_source, encoding="utf-8")
print("M1 wall fixture: trusts composed Phase200 sprint timing, lets standing proof finish, preserves bounded wall timing, restricts sibling frame bridging to the last Create-native owner, and leases one supported baseline frame through a single grounded sampling gap")