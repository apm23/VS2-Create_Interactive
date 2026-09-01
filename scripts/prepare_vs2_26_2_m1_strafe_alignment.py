#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
verifier = Path(__file__).resolve().parent / "prepare_vs2_26_2_m1_jump_proof.py"
source = fixture_input.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")
verifier_source = verifier.read_text(encoding="utf-8")

# Production-world #610 proved yaw +90 sends ordinary right-strafe from local Z=-1.899
# across the negative edge of the verified floor: Entity.move reaches local Z=-2.049 and
# onGround immediately becomes false. Aim the same vanilla right-strafe toward positive local Z,
# across the supported carriage interior instead of off its finite floor edge. Test orientation
# only; no player position/velocity, collision, carry, train, or world state is synthesized.
anchor = '''        client.options.keyLeft.setDown(false);\n        client.options.keyRight.setDown(strafeWindow);'''
replacement = '''        client.options.keyLeft.setDown(false);\n        if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE) {\n            self.setYRot(-90.0F);\n        }\n        client.options.keyRight.setDown(strafeWindow);'''
if source.count(anchor) != 2:
    raise SystemExit("M1 strafe alignment expected two fixture KeyMapping sites")
source = source.replace(anchor, replacement)

# Stop the bounded forward pulse once the existing walk proof is authoritative.
pulse_anchor = 'boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3;'
pulse_replacement = 'boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
if source.count(pulse_anchor) != 2:
    raise SystemExit("M1 forward-stop expected two LocalPlayer pulse boundaries")
source = source.replace(pulse_anchor, pulse_replacement)
walk_window_anchor = 'boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3;'
walk_window_replacement = 'boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
if source.count(walk_window_anchor) != 1:
    raise SystemExit("M1 forward-stop expected one headless pulse boundary")
source = source.replace(walk_window_anchor, walk_window_replacement, 1)

# Require the already-proven two settled native frames before fixture locomotion starts.
immediate_anchor = '''                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh;'''
immediate_replacement = '''                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh
                            && phase185WalkReadyTicks >= 2;'''
if probe_source.count(immediate_anchor) != 1:
    raise SystemExit("M1 settled-start expected one Phase194 immediate native-ready boundary")
probe_source = probe_source.replace(immediate_anchor, immediate_replacement, 1)

# Bound native right-strafe to the wall-impact proof window, then release before jump. The current
# production world can hand Create contact from the pre-strafe carriage to an authoritative sibling
# two ticks after the strafe request. Leave two additional grounded ticks so the existing three-frame
# solid-wall proof can observe that native handoff before jump begins; this changes fixture input
# timing only and does not move the player or synthesize collision/carry.
strafe_window_anchor = 'return strafeElapsed >= 0 && strafeElapsed <= 8;'
strafe_window_replacement = 'return strafeElapsed >= 0 && strafeElapsed <= 3;'
if source.count(strafe_window_anchor) != 1:
    raise SystemExit("M1 wall-bound expected one extended strafe window")
source = source.replace(strafe_window_anchor, strafe_window_replacement, 1)
jump_delay_anchor = 'self.tickCount >= vs2$strafeStartTick + 9'
jump_delay_replacement = 'self.tickCount >= vs2$strafeStartTick + 6'
if source.count(jump_delay_anchor) != 1:
    raise SystemExit("M1 wall-bound expected one post-strafe jump delay")
source = source.replace(jump_delay_anchor, jump_delay_replacement, 1)

# Production-world #609 proved the old jump-floor predicate was tied to stale walk-start Y.
# Walk began on carriage 10 at local Y=0.65625, then native sibling/frame handoffs moved the
# same supported player onto a valid carriage floor at local Y=1.00010. Backward and strafe both
# executed natively, but the immutable walk-start-Y comparison could therefore never arm jump.
# Gate on the live active carriage instead: grounded broadphase contact, same authoritative
# baseline, and two consecutive locally-settled samples. The existing jump admission still also
# requires a tick-fresh/recent native Create contact. This is fixture acceptance only; it writes
# no position, velocity, gravity, collision response, train state, or world state.
floor_probe_anchor = '''                        boolean phase154PreWalkBroadphase = phase154PreWalkCarriage.getBoundingBox().inflate(2.0)
                            .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                        LOGGER.info('''
floor_probe_replacement = '''                        boolean phase154PreWalkBroadphase = phase154PreWalkCarriage.getBoundingBox().inflate(2.0)
                            .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                        boolean m1JumpFloorSupportNow = phase154PreWalkPreviousLocal != null
                            && phase154PreWalkPreviousTick + 1 == player.tickCount
                            && phase154PreWalkStep <= 0.01
                            && phase154PreWalkBroadphase
                            && player.onGround()
                            && phase154PreWalkCarriage.getId() == carryBaselineCarriageId;
                        System.setProperty("vs2.productionFixtureJumpFloorSupportNow", Boolean.toString(m1JumpFloorSupportNow));
                        System.setProperty("vs2.productionFixtureJumpFloorSupportTick", Integer.toString(player.tickCount));
                        LOGGER.info('''
if probe_source.count(floor_probe_anchor) != 1:
    raise SystemExit("M1 jump floor gate expected one Phase154 live carriage boundary")
probe_source = probe_source.replace(floor_probe_anchor, floor_probe_replacement, 1)

# Production-world #635 proved that the previous "live" jump-floor publisher was still scoped to
# GATE_E_PHASE154_PRE_WALK_TRACE, which stops as soon as walk_started becomes true. The walk then
# completed at tick 40 and reverse/strafe ran at ticks 41/42, but JumpFloorSupportTick remained a
# pre-walk value forever, so the native jump could never be requested even after grounded native
# contact recovered. Refresh the same acceptance property from the already-existing carriage-local
# continuity sampler, which runs through the whole M1 window. This is fixture accounting only: it
# observes the current authoritative baseline carriage and never changes player/train/physics state.
continuity_local_anchor = '''                    String localFeet = "unresolved";
                    try {'''
continuity_local_replacement = '''                    String localFeet = "unresolved";
                    net.minecraft.world.phys.Vec3 m1JumpContinuityLocal = null;
                    try {'''
if probe_source.count(continuity_local_anchor) != 1:
    raise SystemExit("M1 live jump support expected one continuity local-value anchor")
probe_source = probe_source.replace(continuity_local_anchor, continuity_local_replacement, 1)

continuity_value_anchor = '''                        Object localValue = toLocal.invoke(localFrameCarriage, player.position(), 0.0f);
                        localFeet = String.valueOf(localValue);'''
continuity_value_replacement = '''                        Object localValue = toLocal.invoke(localFrameCarriage, player.position(), 0.0f);
                        localFeet = String.valueOf(localValue);
                        if (localValue instanceof net.minecraft.world.phys.Vec3) {
                            m1JumpContinuityLocal = (net.minecraft.world.phys.Vec3) localValue;
                        }'''
if probe_source.count(continuity_value_anchor) != 1:
    raise SystemExit("M1 live jump support expected one continuity transform anchor")
probe_source = probe_source.replace(continuity_value_anchor, continuity_value_replacement, 1)

# Anchor immediately after the continuity broadphase calculation rather than on the later
# baselineFrame declaration: later preparation phases legitimately insert bookkeeping between
# those statements. Recompute same-baseline identity locally so this fixture acceptance stays
# composition-stable without changing runtime movement or collision behavior.
continuity_publish_anchor = '''                    boolean broadphase = localFrameCarriage.getBoundingBox().inflate(2.0)
                        .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());'''
continuity_publish_replacement = continuity_publish_anchor + '''
                    boolean m1ContinuitySettledSupport = false;
                    if (m1JumpContinuityLocal != null) {
                        String m1PrevTickRaw = System.getProperty("vs2.m1JumpContinuityTick");
                        String m1PrevCarriageRaw = System.getProperty("vs2.m1JumpContinuityCarriage");
                        String m1PrevXRaw = System.getProperty("vs2.m1JumpContinuityX");
                        String m1PrevYRaw = System.getProperty("vs2.m1JumpContinuityY");
                        String m1PrevZRaw = System.getProperty("vs2.m1JumpContinuityZ");
                        try {
                            int m1PrevTick = Integer.parseInt(m1PrevTickRaw == null ? "-2147483648" : m1PrevTickRaw);
                            int m1PrevCarriage = Integer.parseInt(m1PrevCarriageRaw == null ? "-2147483648" : m1PrevCarriageRaw);
                            double m1PrevX = Double.parseDouble(m1PrevXRaw == null ? "NaN" : m1PrevXRaw);
                            double m1PrevY = Double.parseDouble(m1PrevYRaw == null ? "NaN" : m1PrevYRaw);
                            double m1PrevZ = Double.parseDouble(m1PrevZRaw == null ? "NaN" : m1PrevZRaw);
                            double m1Dx = m1JumpContinuityLocal.x - m1PrevX;
                            double m1Dy = m1JumpContinuityLocal.y - m1PrevY;
                            double m1Dz = m1JumpContinuityLocal.z - m1PrevZ;
                            double m1StepSq = m1Dx * m1Dx + m1Dy * m1Dy + m1Dz * m1Dz;
                            m1ContinuitySettledSupport = m1PrevTick + 1 == player.tickCount
                                && m1PrevCarriage == localFrameCarriage.getId()
                                && m1StepSq <= 0.0001
                                && broadphase && player.onGround()
                                && localFrameCarriage.getId() == carryBaselineCarriageId;
                        } catch (NumberFormatException ignored) {
                            m1ContinuitySettledSupport = false;
                        }
                        System.setProperty("vs2.m1JumpContinuityTick", Integer.toString(player.tickCount));
                        System.setProperty("vs2.m1JumpContinuityCarriage", Integer.toString(localFrameCarriage.getId()));
                        System.setProperty("vs2.m1JumpContinuityX", Double.toString(m1JumpContinuityLocal.x));
                        System.setProperty("vs2.m1JumpContinuityY", Double.toString(m1JumpContinuityLocal.y));
                        System.setProperty("vs2.m1JumpContinuityZ", Double.toString(m1JumpContinuityLocal.z));
                    }
                    System.setProperty("vs2.productionFixtureJumpFloorSupportNow", Boolean.toString(m1ContinuitySettledSupport));
                    System.setProperty("vs2.productionFixtureJumpFloorSupportTick", Integer.toString(player.tickCount));'''
if probe_source.count(continuity_publish_anchor) != 1:
    raise SystemExit("M1 live jump support expected one continuity broadphase anchor")
probe_source = probe_source.replace(continuity_publish_anchor, continuity_publish_replacement, 1)

jump_floor_gate_anchor = '''            && self.onGround()
            && (Integer.toString(self.tickCount).equals(System.getProperty("vs2.phase170NativeContactApplicationTick"))'''
jump_floor_gate_replacement = '''            && self.onGround()
            && Boolean.getBoolean("vs2.productionFixtureJumpFloorSupportNow")
            && (Integer.toString(self.tickCount).equals(System.getProperty("vs2.productionFixtureJumpFloorSupportTick"))
                || Integer.toString(self.tickCount - 1).equals(System.getProperty("vs2.productionFixtureJumpFloorSupportTick")))
            && (Integer.toString(self.tickCount).equals(System.getProperty("vs2.phase170NativeContactApplicationTick"))'''
if source.count(jump_floor_gate_anchor) != 1:
    raise SystemExit("M1 jump floor gate expected one post-strafe admission boundary")
source = source.replace(jump_floor_gate_anchor, jump_floor_gate_replacement, 1)

# Create can legitimately retain onGround during a vertical arc; landing proof follows native
# falling state and settled vertical speed rather than requiring an airborne onGround edge.
landing_anchor = 'if (vs2$jumpFallingSeen && self.onGround() && Math.abs(deltaY) < 0.005 && self.tickCount > vs2$jumpStartTick) {'
if source.count(landing_anchor) != 1:
    raise SystemExit("M1 landing proof expected the falling/onGround settle boundary")

# Once a native jump has been armed, do not terminate its observer because contact age changes.
jump_observer_gate_anchor = '''        boolean jumpArmReady = vs2$jumpArmReady(self);\n        if (!jumpArmReady || vs2$jumpLandedLogged) {'''
jump_observer_gate_replacement = '''        boolean jumpArmReady = vs2$jumpArmReady(self);\n        if ((vs2$jumpStartTick == Integer.MIN_VALUE && !jumpArmReady) || vs2$jumpLandedLogged) {'''
if source.count(jump_observer_gate_anchor) != 1:
    raise SystemExit("M1 jump observer expected one pre-jump admission gate")
source = source.replace(jump_observer_gate_anchor, jump_observer_gate_replacement, 1)

# Hold the ordinary vanilla jump KeyMapping for request tick plus one sampling tick.
jump_pulse_anchor = 'boolean jumpPulse = vs2$jumpStartTick != Integer.MIN_VALUE && self.tickCount == vs2$jumpStartTick;'
jump_pulse_replacement = 'boolean jumpPulse = vs2$jumpStartTick != Integer.MIN_VALUE && self.tickCount >= vs2$jumpStartTick && self.tickCount <= vs2$jumpStartTick + 1;'
if source.count(jump_pulse_anchor) < 1:
    raise SystemExit("M1 jump pulse expected at least one vanilla KeyMapping boundary")
source = source.replace(jump_pulse_anchor, jump_pulse_replacement)

# Production-world #611 proved the supported +Z strafe reaches the opposite real side wall and
# then completes the native jump/landing sequence. The standalone verifier still hard-coded the
# old -Z wall used by the unsafe edge-facing fixture. Rebase only that read-only verifier contract
# to the +Z occupied side; gameplay code and collision response remain untouched.
verifier_replacements = [
    (
        'wall_geometry_seen = any(re.search(r"(?:^|\\|)-?\\d+, [123], -2(?:\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
        'wall_geometry_seen = any(re.search(r"(?:^|\\|)-?\\d+, [123], 2(?:\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
    ),
    (
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")',
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=2")',
    ),
    (
        'start_z=before[-1][4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)\nif min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
        'start_z=before[-1][4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)\nif max_z>=2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
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
for old, new in verifier_replacements:
    if verifier_source.count(old) != 1:
        raise SystemExit("M1 +Z wall verifier expected one exact legacy boundary: " + old[:72])
    verifier_source = verifier_source.replace(old, new, 1)

# The current production smoke proves a legitimate Create-native sibling handoff can occur after
# the strafe request, once the transient frame seam has passed. The verifier previously looked for
# that rebase only on the exact request tick and then required its supported streak to begin there,
# rejecting the native wall samples that begin on the authoritative sibling at the later rebase.
# Follow the first identity-only native-contact-owner rebase inside the bounded strafe window and
# start the unchanged three-frame solid-wall streak there. Verifier bookkeeping only.
wall_handoff_anchor = '''pre_wall_carriage=before[-1][1]
rebase_match=re.search(
    rf"GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE[^\\n]*previous_carriage_id={pre_wall_carriage}[^\\n]*carriage_id=(\\d+)[^\\n]*player_tick={strafe_request_tick}[^\\n]*native_contact_owner=true[^\\n]*identity_only=true",
    text)
wall_carriage=int(rebase_match.group(1)) if rebase_match is not None else pre_wall_carriage
after=[]; expected_tick=strafe_request_tick
for sample in after_window:
    if sample[0]<expected_tick: continue
    if sample[0]!=expected_tick or sample[1]!=wall_carriage: break
    after.append(sample); expected_tick+=1
if len(after)<3: raise SystemExit("M1 wall proof did not retain three consecutive samples on the Create-authoritative strafe carriage")'''
wall_handoff_replacement = '''pre_wall_carriage=before[-1][1]
rebase_pattern=re.compile(
    rf"GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE[^\\n]*previous_carriage_id={pre_wall_carriage}[^\\n]*carriage_id=(\\d+)[^\\n]*player_tick=(\\d+)[^\\n]*native_contact_owner=true[^\\n]*identity_only=true")
rebase_match=next((m for m in rebase_pattern.finditer(text) if strafe_request_tick <= int(m.group(2)) <= strafe_request_tick+7), None)
wall_carriage=int(rebase_match.group(1)) if rebase_match is not None else pre_wall_carriage
wall_start_tick=int(rebase_match.group(2)) if rebase_match is not None else strafe_request_tick
after=[]; expected_tick=wall_start_tick
for sample in after_window:
    if sample[0]<expected_tick: continue
    if sample[0]!=expected_tick or sample[1]!=wall_carriage: break
    after.append(sample); expected_tick+=1
if len(after)<3: raise SystemExit("M1 wall proof did not retain three consecutive samples on the Create-authoritative strafe carriage")'''
if verifier_source.count(wall_handoff_anchor) != 1:
    raise SystemExit("M1 wall handoff verifier expected one exact request-tick rebase boundary")
verifier_source = verifier_source.replace(wall_handoff_anchor, wall_handoff_replacement, 1)

required_source = [
    'if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE)',
    'self.setYRot(-90.0F)',
    'client.options.keyRight.setDown(strafeWindow)',
    '!Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")',
    'return strafeElapsed >= 0 && strafeElapsed <= 3;',
    'self.tickCount >= vs2$strafeStartTick + 6',
    'vs2$jumpFallingSeen && self.onGround() && Math.abs(deltaY) < 0.005',
    '(vs2$jumpStartTick == Integer.MIN_VALUE && !jumpArmReady) || vs2$jumpLandedLogged',
    'self.tickCount <= vs2$jumpStartTick + 1',
    'vs2.productionFixtureJumpFloorSupportNow',
    'vs2.productionFixtureJumpFloorSupportTick',
]
missing = [token for token in required_source if token not in source]
if missing:
    raise SystemExit("M1 fixture refinement lost anchors: " + ", ".join(missing))
required_probe = [
    'phase185WalkReadyTicks >= 2',
    'm1JumpFloorSupportNow',
    'phase154PreWalkPreviousTick + 1 == player.tickCount',
    'phase154PreWalkStep <= 0.01',
    'phase154PreWalkCarriage.getId() == carryBaselineCarriageId',
    'm1JumpContinuityLocal',
    'm1ContinuitySettledSupport',
    'vs2.m1JumpContinuityTick',
    'vs2.m1JumpContinuityCarriage',
    'm1StepSq <= 0.0001',
    'vs2.productionFixtureJumpFloorSupportNow',
    'vs2.productionFixtureJumpFloorSupportTick',
]
missing = [token for token in required_probe if token not in probe_source]
if missing:
    raise SystemExit("M1 live-frame jump gate lost anchors: " + ", ".join(missing))
required_verifier = [
    'local block z=2',
    'max_z=max(wall_z)',
    'float(strafe_move.group(3)) >= 0.02',
    'max(candidate_z)-start_z>=0.015',
    'wall_start_tick=int(rebase_match.group(2))',
]
missing = [token for token in required_verifier if token not in verifier_source]
if missing:
    raise SystemExit("M1 +Z wall verifier lost anchors: " + ", ".join(missing))
for forbidden in [
    'self.setPos(', 'self.setDeltaMovement(', 'self.move(', '.teleport(',
    'setBlock(', 'syncCarriage(', 'setVelocity(',
]:
    if forbidden in source:
        raise SystemExit("M1 fixture refinement found forbidden gameplay mutation: " + forbidden)
for forbidden in [
    'player.setPos(', 'player.setDeltaMovement(', 'player.move(', '.teleport(',
    'setBlock(', 'syncCarriage(', 'setVelocity(',
]:
    if forbidden in immediate_replacement + floor_probe_replacement + continuity_publish_replacement:
        raise SystemExit("M1 fixture gate found forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
verifier.write_text(verifier_source, encoding="utf-8")
print("M1 fixture refinement: follows native strafe sibling handoff through a three-frame wall proof before jump")