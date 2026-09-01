#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = fixture_input.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")

# Production-world #588 proved the right-strafe KeyMapping executed natively, but the
# deterministic fixture still had world yaw 0 while the train corridor runs along world X.
# That maps "right" toward carriage-local -X and off the carriage end instead of toward the
# already-verified side wall at local Z=-2. Align the disposable fixture view once, at the
# start of the strafe window, so ordinary Minecraft right-strafe exercises the intended wall.
# This changes only test orientation; movement/collision/carry remain vanilla/Create native.
anchor = '''        client.options.keyLeft.setDown(false);\n        client.options.keyRight.setDown(strafeWindow);'''
replacement = '''        client.options.keyLeft.setDown(false);\n        if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE) {\n            self.setYRot(90.0F);\n        }\n        client.options.keyRight.setDown(strafeWindow);'''

count = source.count(anchor)
if count != 2:
    raise SystemExit(f"M1 strafe alignment expected two fixture KeyMapping sites, found {count}")
source = source.replace(anchor, replacement)

# Production-world #589 proves the wall fixture was armed only after the already-confirmed
# forward sprint had carried the disposable player out of carriage broadphase. The native walk
# proof itself completed before that loss of support. Stop the bounded forward KeyMapping as soon
# as the existing walk-confirmed property becomes authoritative, leaving the later reverse/strafe
# inputs to run from the still-supported carriage surface. The cumulative input harness contains
# two equivalent LocalPlayer forward-pulse sites, so gate both consistently. Harness input only;
# no player transform, velocity, collision, carry, train, or world state is synthesized.
pulse_anchor = 'boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3;'
pulse_replacement = 'boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
pulse_count = source.count(pulse_anchor)
if pulse_count != 2:
    raise SystemExit(f"M1 forward-stop expected two LocalPlayer forward pulse boundaries, found {pulse_count}")
source = source.replace(pulse_anchor, pulse_replacement)

walk_window_anchor = 'boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3;'
walk_window_replacement = 'boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
walk_window_count = source.count(walk_window_anchor)
if walk_window_count != 1:
    raise SystemExit(f"M1 forward-stop expected one headless forward pulse boundary, found {walk_window_count}")
source = source.replace(walk_window_anchor, walk_window_replacement, 1)

# Production-world #599 proved same-tick Phase194 acceptance can still start the disposable
# locomotion fixture on the first settled-ready sample: tick 16 had strict support, fresh native
# Create application and native-health age 0, but ready_ticks was only 1. The next frames contained
# the startup carriage-frame discontinuity and the walk start prevented the standing-carry verifier
# from collecting a clean native plateau. Keep the same-tick path required by #594, but require the
# existing Phase185 settled-ready counter to have survived one prior consecutive frame. This is only
# fixture acceptance; no movement, collision, carry vector, train/world state, or VS2/Create physics
# is changed.
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

# Production-world #601 proves native right-strafe is already confirmed on its first input tick,
# but holding it for nine ticks keeps pressing the disposable player through the finite side-wall
# seam until the later jump starts from a degraded support frame. Four input ticks still provide the
# existing wall verifier its required three-sample impact plateau, then release the key and permit
# the jump on the next tick. Harness timing only; no movement, collision, carry, velocity, player
# position, train state, or VS2/Create physics is changed.
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

# Production-world #598 proved the jump executes natively and later performs a real descent.
# Phase202 also established that Create's moving-contraption contact can legitimately keep
# LocalPlayer.onGround true through that vertical arc. Production-world #602 reproduces exactly
# that native shape: jump request at tick 37 and positive vertical arc at tick 38 while on_ground
# remains true. Do not require an onGround=false edge that Create is not required to publish.
# Restore the existing native landing boundary: a prior falling sample, Create/vanilla onGround,
# and near-zero vertical speed. Fixture observation only; no motion/collision/carry is synthesized.
landing_anchor = 'if (vs2$jumpFallingSeen && self.onGround() && Math.abs(deltaY) < 0.005 && self.tickCount > vs2$jumpStartTick) {'
if source.count(landing_anchor) != 1:
    raise SystemExit("M1 landing proof expected the Phase202 falling/onGround settle boundary")

# Production-world #603 proves the native jump observer itself is being switched off too early.
# The jump starts at tick 44 and native/Create movement subsequently exposes descending deltas
# (-0.0122 by tick 61, settling below 0.005 by tick 64) while carriage-local continuity remains
# broadphase/onGround. The existing jumpArmReady predicate is intentionally a pre-jump admission
# gate based on recent native Create contact; once the jump is already armed, a later contact-age
# change must not stop observation of that already-authoritative native arc. Keep the arm gate only
# before vs2$jumpStartTick is assigned. This changes fixture observation lifetime only.
jump_observer_gate_anchor = '''        boolean jumpArmReady = vs2$jumpArmReady(self);\n        if (!jumpArmReady || vs2$jumpLandedLogged) {'''
jump_observer_gate_replacement = '''        boolean jumpArmReady = vs2$jumpArmReady(self);\n        if ((vs2$jumpStartTick == Integer.MIN_VALUE && !jumpArmReady) || vs2$jumpLandedLogged) {'''
if source.count(jump_observer_gate_anchor) != 1:
    raise SystemExit("M1 jump observer expected one pre-jump native-contact admission gate")
source = source.replace(jump_observer_gate_anchor, jump_observer_gate_replacement, 1)

# Production-world #592 reached the authoritative jump request but did not always produce the
# vertical arc, while #591 proved the exact same one-tick KeyMapping path can work. Hold the
# ordinary vanilla jump KeyMapping for the request tick plus one following tick so normal input
# sampling cannot miss it. This remains input-only and never writes motion or position.
jump_pulse_anchor = 'boolean jumpPulse = vs2$jumpStartTick != Integer.MIN_VALUE && self.tickCount == vs2$jumpStartTick;'
jump_pulse_replacement = 'boolean jumpPulse = vs2$jumpStartTick != Integer.MIN_VALUE && self.tickCount >= vs2$jumpStartTick && self.tickCount <= vs2$jumpStartTick + 1;'
jump_pulse_count = source.count(jump_pulse_anchor)
if jump_pulse_count < 1:
    raise SystemExit(f"M1 jump pulse expected at least one vanilla KeyMapping boundary, found {jump_pulse_count}")
source = source.replace(jump_pulse_anchor, jump_pulse_replacement)

required = [
    'if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE)',
    'self.setYRot(90.0F)',
    'client.options.keyRight.setDown(strafeWindow)',
    '!Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")',
    'return strafeElapsed >= 0 && strafeElapsed <= 3;',
    'self.tickCount >= vs2$strafeStartTick + 4',
    'vs2$jumpFallingSeen && self.onGround() && Math.abs(deltaY) < 0.005',
    '(vs2$jumpStartTick == Integer.MIN_VALUE && !jumpArmReady) || vs2$jumpLandedLogged',
    'self.tickCount <= vs2$jumpStartTick + 1',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("M1 fixture refinement lost anchors: " + ", ".join(missing))
if 'phase185WalkReadyTicks >= 2' not in probe_source:
    raise SystemExit("M1 settled-start lost Phase185 two-frame readiness guard")

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
    if forbidden in immediate_replacement:
        raise SystemExit("M1 settled-start found forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
print("M1 fixture refinement: keeps native jump observation alive after admission while preserving frozen carry/walk/collision behavior")
