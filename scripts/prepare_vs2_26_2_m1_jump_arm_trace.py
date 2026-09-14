#!/usr/bin/env python3
"""Add read-only telemetry for the final M1 native-jump admission boundary."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
source = java.read_text(encoding="utf-8")

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

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", ".teleport(",
    "setBlock(", "syncCarriage(", "setVelocity(", "setOnGround(",
    "keyJump.setDown(true)",
]:
    if forbidden in replacement:
        raise SystemExit("M1 jump-arm trace introduced mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
print("M1 jump-arm trace: read-only final admission predicate telemetry installed")
