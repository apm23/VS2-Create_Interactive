#!/usr/bin/env python3
"""Add M1 jump admission telemetry and repair fixture-local floor-support bookkeeping."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = java.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")

anchor = '        boolean jumpArmReady = vs2$jumpArmReady(self);\n'
replacement = anchor + '''        if (vs2$jumpStartTick == Integer.MIN_VALUE
                && vs2$walkConfirmedTick != Integer.MIN_VALUE
                && self.tickCount >= vs2$walkConfirmedTick) {
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_JUMP_ARM_TRACE player_tick={} walk_confirmed_tick={} backward_confirmed={} strafe_confirmed={} strafe_start_tick={} on_ground={} jump_arm_ready={} floor_support_now={} floor_support_tick={} native_contact_tick={} delta_y={} fixture_only=true read_only=true",
                self.tickCount,
                vs2$walkConfirmedTick,
                vs2$backwardConfirmed,
                vs2$strafeConfirmed,
                vs2$strafeStartTick,
                self.onGround(),
                jumpArmReady,
                Boolean.getBoolean("vs2.productionFixtureJumpFloorSupportNow"),
                System.getProperty("vs2.productionFixtureJumpFloorSupportTick"),
                System.getProperty("vs2.phase170NativeContactApplicationTick"),
                self.getDeltaMovement().y);
        }
'''

if source.count(anchor) != 1:
    raise SystemExit(f"M1 jump-arm trace expected one final admission boundary, found {source.count(anchor)}")
source = source.replace(anchor, replacement, 1)

# Production-world #729 isolates the first post-walk support failure to the old local-step gate:
# tick/carriage/broadphase/onGround/baseline all remain valid while ordinary backward/strafe motion
# makes m1StepSq > 0.0001. Requiring the player to be almost motionless therefore contradicts the
# native input sequence we are trying to prove. Keep the safety intent from #604 (reject non-floor
# Create contact), but classify the fixed M1 fixture floor by carriage-local feet Y instead of total
# XYZ displacement. The proven floor after walk is at local Y ~= 1.0001, while #604's bad contact
# was local Y ~= 1.812. This changes fixture acceptance bookkeeping only; no player, collision,
# carriage, train, or world state is mutated.
floor_anchor = '''                            m1ContinuitySettledSupport = m1PrevTick + 1 == player.tickCount
                                && m1PrevCarriage == localFrameCarriage.getId()
                                && m1StepSq <= 0.0001
                                && broadphase && player.onGround()
                                && localFrameCarriage.getId() == carryBaselineCarriageId;
'''
floor_replacement = '''                            boolean m1FixtureFloorAligned = Math.abs(
                                m1JumpContinuityLocal.y - Math.rint(m1JumpContinuityLocal.y)) <= 0.05;
                            m1ContinuitySettledSupport = m1PrevTick + 1 == player.tickCount
                                && m1PrevCarriage == localFrameCarriage.getId()
                                && m1FixtureFloorAligned
                                && broadphase && player.onGround()
                                && localFrameCarriage.getId() == carryBaselineCarriageId;
                            LOGGER.info(
                                "GATE_E_M1_JUMP_FLOOR_TRACE player_tick={} carriage_id={} previous_tick={} previous_carriage_id={} tick_consecutive={} same_carriage={} local_step_sq={} locally_settled={} local_y={} floor_aligned={} broadphase={} on_ground={} baseline_carriage_id={} baseline_match={} support_now={} fixture_only=true bookkeeping_fix=true",
                                player.tickCount,
                                localFrameCarriage.getId(),
                                m1PrevTick,
                                m1PrevCarriage,
                                m1PrevTick + 1 == player.tickCount,
                                m1PrevCarriage == localFrameCarriage.getId(),
                                m1StepSq,
                                m1StepSq <= 0.0001,
                                m1JumpContinuityLocal.y,
                                m1FixtureFloorAligned,
                                broadphase,
                                player.onGround(),
                                carryBaselineCarriageId,
                                localFrameCarriage.getId() == carryBaselineCarriageId,
                                m1ContinuitySettledSupport);
'''
if probe_source.count(floor_anchor) != 1:
    raise SystemExit(f"M1 jump-floor fix expected one continuity publisher boundary, found {probe_source.count(floor_anchor)}")
probe_source = probe_source.replace(floor_anchor, floor_replacement, 1)

required = [
    "GATE_E_M1_JUMP_ARM_TRACE",
    "jump_arm_ready={}",
    "floor_support_now={}",
    "vs2.productionFixtureJumpFloorSupportTick",
    "vs2.phase170NativeContactApplicationTick",
    "fixture_only=true read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("M1 jump-arm trace lost anchors: " + ", ".join(missing))

required_probe = [
    "GATE_E_M1_JUMP_FLOOR_TRACE",
    "tick_consecutive={}",
    "same_carriage={}",
    "local_step_sq={}",
    "locally_settled={}",
    "local_y={}",
    "floor_aligned={}",
    "baseline_match={}",
    "support_now={}",
    "bookkeeping_fix=true",
    "Math.rint(m1JumpContinuityLocal.y)",
]
missing_probe = [token for token in required_probe if token not in probe_source]
if missing_probe:
    raise SystemExit("M1 jump-floor fix lost anchors: " + ", ".join(missing_probe))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", ".teleport(",
    "setBlock(", "syncCarriage(", "setVelocity(", "setOnGround(",
    "keyJump.setDown(true)",
]:
    if forbidden in replacement + floor_replacement:
        raise SystemExit("M1 jump fix introduced mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
print("M1 jump floor bookkeeping: native horizontal motion allowed while fixed fixture-floor alignment remains required")
