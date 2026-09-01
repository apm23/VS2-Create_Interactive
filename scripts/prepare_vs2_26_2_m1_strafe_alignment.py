#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = fixture_input.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")

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

# Require three settled native frames before fixture locomotion starts.
immediate_anchor = '''                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh;'''
immediate_replacement = '''                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate
                            && phase194NativeAuthoritativeSupport
                            && phase185NativeApplicationFresh
                            && phase185WalkReadyTicks >= 3;'''
if probe_source.count(immediate_anchor) != 1:
    raise SystemExit("M1 settled-start expected one Phase194 immediate native-ready boundary")
probe_source = probe_source.replace(immediate_anchor, immediate_replacement, 1)

# Bound native right-strafe to the wall-impact proof window, then release before jump.
strafe_window_anchor = 'return strafeElapsed >= 0 && strafeElapsed <= 8;'
strafe_window_replacement = 'return strafeElapsed >= 0 && strafeElapsed <= 3;'
if source.count(strafe_window_anchor) != 1:
    raise SystemExit("M1 wall-bound expected one extended strafe window")
source = source.replace(strafe_window_anchor, strafe_window_replacement, 1)
jump_delay_anchor = 'self.tickCount >= vs2$strafeStartTick + 9'
jump_delay_replacement = 'self.tickCount >= vs2$strafeStartTick + 4'
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

required_source = [
    'if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE)',
    'self.setYRot(-90.0F)',
    'client.options.keyRight.setDown(strafeWindow)',
    '!Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")',
    'return strafeElapsed >= 0 && strafeElapsed <= 3;',
    'self.tickCount >= vs2$strafeStartTick + 4',
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
    'phase185WalkReadyTicks >= 3',
    'm1JumpFloorSupportNow',
    'phase154PreWalkPreviousTick + 1 == player.tickCount',
    'phase154PreWalkStep <= 0.01',
    'phase154PreWalkCarriage.getId() == carryBaselineCarriageId',
    'vs2.productionFixtureJumpFloorSupportNow',
    'vs2.productionFixtureJumpFloorSupportTick',
]
missing = [token for token in required_probe if token not in probe_source]
if missing:
    raise SystemExit("M1 live-frame jump gate lost anchors: " + ", ".join(missing))

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
    if forbidden in immediate_replacement + floor_probe_replacement:
        raise SystemExit("M1 fixture gate found forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
print("M1 fixture refinement: aims native strafe across supported floor and gates jump on live active-carriage support")
