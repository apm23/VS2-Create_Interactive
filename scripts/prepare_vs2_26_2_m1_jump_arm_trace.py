#!/usr/bin/env python3
"""Add read-only telemetry for the final M1 native-jump admission boundary."""
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

# #728 proves backward+strafe are already native-confirmed while jumpArmReady remains false because
# the live floor-support publisher stays false. Instrument the exact publisher predicate before its
# state is rolled forward, so we can distinguish continuity cadence, sibling-owner identity, local
# movement, broadphase, grounding, and baseline mismatch without changing acceptance or gameplay.
floor_anchor = '''                            m1ContinuitySettledSupport = m1PrevTick + 1 == player.tickCount
                                && m1PrevCarriage == localFrameCarriage.getId()
                                && m1StepSq <= 0.0001
                                && broadphase && player.onGround()
                                && localFrameCarriage.getId() == carryBaselineCarriageId;
'''
floor_replacement = floor_anchor + '''                            LOGGER.info(
                                "GATE_E_M1_JUMP_FLOOR_TRACE player_tick={} carriage_id={} previous_tick={} previous_carriage_id={} tick_consecutive={} same_carriage={} local_step_sq={} locally_settled={} broadphase={} on_ground={} baseline_carriage_id={} baseline_match={} support_now={} fixture_only=true read_only=true",
                                player.tickCount,
                                localFrameCarriage.getId(),
                                m1PrevTick,
                                m1PrevCarriage,
                                m1PrevTick + 1 == player.tickCount,
                                m1PrevCarriage == localFrameCarriage.getId(),
                                m1StepSq,
                                m1StepSq <= 0.0001,
                                broadphase,
                                player.onGround(),
                                carryBaselineCarriageId,
                                localFrameCarriage.getId() == carryBaselineCarriageId,
                                m1ContinuitySettledSupport);
'''
if probe_source.count(floor_anchor) != 1:
    raise SystemExit(f"M1 jump-floor trace expected one continuity publisher boundary, found {probe_source.count(floor_anchor)}")
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
    "baseline_match={}",
    "support_now={}",
    "fixture_only=true read_only=true",
]
missing_probe = [token for token in required_probe if token not in probe_source]
if missing_probe:
    raise SystemExit("M1 jump-floor trace lost anchors: " + ", ".join(missing_probe))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", ".teleport(",
    "setBlock(", "syncCarriage(", "setVelocity(", "setOnGround(",
    "keyJump.setDown(true)",
]:
    if forbidden in replacement + floor_replacement:
        raise SystemExit("M1 jump trace introduced mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
print("M1 jump-arm/floor trace: read-only final admission predicate telemetry installed")
