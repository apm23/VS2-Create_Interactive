#!/usr/bin/env python3
"""Add M1 jump admission telemetry, floor-support bookkeeping, and read-only jump seam tracing."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collider = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"
source = java.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")
collider_source = collider.read_text(encoding="utf-8")

# Production-world #748 reaches grounded tick 53 with walk/reverse/strafe confirmed, fresh floor
# support, fresh native Create contact, and the six-tick post-strafe delay satisfied, yet the final
# jumpArmReady result remains false and no jump request is emitted. Previous nearest-carriage and
# Phase83-airborne telemetry also show carriage selection stays stable and the external frame lease
# remains eligible. Do not change admission semantics. Publish the exact composed method body at
# prepare time plus independently derived runtime gate ages so the hidden rejecting predicate can be
# identified without relaxing the verifier or changing player/train/collision/physics state.
method_signature = "    private boolean vs2$jumpArmReady(LocalPlayer self) {"
method_start = source.find(method_signature)
if method_start < 0:
    raise SystemExit("M1 jump-arm predicate trace could not find composed vs2$jumpArmReady method")
brace_start = source.find("{", method_start)
depth = 0
method_end = -1
for index in range(brace_start, len(source)):
    if source[index] == "{":
        depth += 1
    elif source[index] == "}":
        depth -= 1
        if depth == 0:
            method_end = index + 1
            break
if method_end < 0:
    raise SystemExit("M1 jump-arm predicate trace could not close composed vs2$jumpArmReady method")
print("M1_JUMP_ARM_METHOD_SOURCE_BEGIN")
print(source[method_start:method_end])
print("M1_JUMP_ARM_METHOD_SOURCE_END")

anchor = '        boolean jumpArmReady = vs2$jumpArmReady(self);\n'
replacement = anchor + '''        int vs2$jumpFloorSupportAge = Integer.MAX_VALUE;
        int vs2$jumpNativeContactAge = Integer.MAX_VALUE;
        try {
            String floorTickRaw = System.getProperty("vs2.productionFixtureJumpFloorSupportTick");
            if (floorTickRaw != null) vs2$jumpFloorSupportAge = self.tickCount - Integer.parseInt(floorTickRaw);
        } catch (NumberFormatException ignored) {
            vs2$jumpFloorSupportAge = Integer.MAX_VALUE;
        }
        try {
            String nativeTickRaw = System.getProperty("vs2.phase170NativeContactApplicationTick");
            if (nativeTickRaw != null) vs2$jumpNativeContactAge = self.tickCount - Integer.parseInt(nativeTickRaw);
        } catch (NumberFormatException ignored) {
            vs2$jumpNativeContactAge = Integer.MAX_VALUE;
        }
        int vs2$jumpStrafeAge = vs2$strafeStartTick == Integer.MIN_VALUE
            ? Integer.MIN_VALUE : self.tickCount - vs2$strafeStartTick;
        boolean vs2$jumpWalkProperty = Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");
        boolean vs2$jumpFloorProperty = Boolean.getBoolean("vs2.productionFixtureJumpFloorSupportNow");
        boolean vs2$jumpKnownDelayReady = vs2$strafeStartTick != Integer.MIN_VALUE && vs2$jumpStrafeAge >= 6;
        boolean vs2$jumpKnownFloorFresh = vs2$jumpFloorProperty
            && vs2$jumpFloorSupportAge >= 0 && vs2$jumpFloorSupportAge <= 1;
        boolean vs2$jumpKnownNativeFresh = vs2$jumpNativeContactAge >= 0 && vs2$jumpNativeContactAge <= 3;
        if (vs2$jumpStartTick == Integer.MIN_VALUE
                && vs2$walkConfirmedTick != Integer.MIN_VALUE
                && self.tickCount >= vs2$walkConfirmedTick) {
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_JUMP_ARM_PREDICATES player_tick={} walk_property={} backward_confirmed={} strafe_confirmed={} strafe_age={} known_delay_ready={} on_ground={} floor_property={} floor_age={} known_floor_fresh={} native_age={} known_native_fresh={} final_jump_arm_ready={} fixture_only=true read_only=true",
                self.tickCount,
                vs2$jumpWalkProperty,
                vs2$backwardConfirmed,
                vs2$strafeConfirmed,
                vs2$jumpStrafeAge,
                vs2$jumpKnownDelayReady,
                self.onGround(),
                vs2$jumpFloorProperty,
                vs2$jumpFloorSupportAge,
                vs2$jumpKnownFloorFresh,
                vs2$jumpNativeContactAge,
                vs2$jumpKnownNativeFresh,
                jumpArmReady);
        }
        if (vs2$jumpStartTick == Integer.MIN_VALUE
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

# Production-world #730 proves the native jump request and positive vertical arc execute, while
# LocalPlayer still reports grounded through most of the arc and later transfers to a sibling
# carriage before landing. Do not alter collision, grounding, velocity, input, lease, or ownership.
# Instead correlate the exact Create setOnGround decision with the later final motion write.
ground_anchor = '''    private static void vs2$preserveVanillaAirborneDuringCreateCarry(Entity entity, boolean onGround) {
        boolean risingLocalPlayer = Boolean.getBoolean("vs2.createCarryCompat")
            && "net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName())
            && entity.getDeltaMovement().y > 0.05;
        entity.setOnGround(onGround && !risingLocalPlayer);
    }
'''
ground_replacement = '''    private static void vs2$preserveVanillaAirborneDuringCreateCarry(Entity entity, boolean onGround) {
        boolean compatLocalPlayer = Boolean.getBoolean("vs2.createCarryCompat")
            && "net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName());
        double deltaYAtCall = entity.getDeltaMovement().y;
        boolean risingLocalPlayer = compatLocalPlayer && deltaYAtCall > 0.05;
        boolean appliedOnGround = onGround && !risingLocalPlayer;
        if (compatLocalPlayer && entity.tickCount >= 45 && entity.tickCount <= 80) {
            LOGGER.info(
                "GATE_E_CREATE_SET_ON_GROUND_SEAM player_tick={} requested_on_ground={} before_on_ground={} delta_y_at_call={} rising_guard={} applied_on_ground={} pos={},{},{} fixture_only=true read_only=true",
                entity.tickCount, onGround, entity.onGround(), deltaYAtCall, risingLocalPlayer, appliedOnGround,
                entity.getX(), entity.getY(), entity.getZ());
        }
        entity.setOnGround(appliedOnGround);
    }
'''
if collider_source.count(ground_anchor) != 1:
    raise SystemExit(f"M1 ground-motion trace expected one Create setOnGround seam, found {collider_source.count(ground_anchor)}")
collider_source = collider_source.replace(ground_anchor, ground_replacement, 1)

motion_anchor = '''        entity.setDeltaMovement(appliedMotion);
    }
'''
motion_replacement = '''        boolean compatLocalPlayer = Boolean.getBoolean("vs2.createCarryCompat")
            && "net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName());
        if (compatLocalPlayer && entity.tickCount >= 45 && entity.tickCount <= 80) {
            LOGGER.info(
                "GATE_E_CREATE_FINAL_MOTION_SEAM player_tick={} on_ground_before_write={} current_delta_y={} incoming_y={} applied_y={} grounded_clip={} pos={},{},{} fixture_only=true read_only=true",
                entity.tickCount, entity.onGround(), entity.getDeltaMovement().y,
                motion.y, appliedMotion.y, groundedLocalPlayer && motion.y < 0.0,
                entity.getX(), entity.getY(), entity.getZ());
        }
        entity.setDeltaMovement(appliedMotion);
    }
'''
if collider_source.count(motion_anchor) != 1:
    raise SystemExit(f"M1 ground-motion trace expected one final native-motion write, found {collider_source.count(motion_anchor)}")
collider_source = collider_source.replace(motion_anchor, motion_replacement, 1)

required = [
    "GATE_E_M1_JUMP_ARM_TRACE",
    "GATE_E_M1_JUMP_ARM_PREDICATES",
    "known_delay_ready={}",
    "known_floor_fresh={}",
    "known_native_fresh={}",
    "final_jump_arm_ready={}",
    "M1_JUMP_ARM_METHOD_SOURCE_BEGIN",
    "M1_JUMP_ARM_METHOD_SOURCE_END",
    "jump_arm_ready={}",
    "floor_support_now={}",
    "vs2.productionFixtureJumpFloorSupportTick",
    "vs2.phase170NativeContactApplicationTick",
    "fixture_only=true read_only=true",
]
missing = [token for token in required if token not in replacement + Path(__file__).read_text(encoding="utf-8")]
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

required_collider = [
    "GATE_E_CREATE_SET_ON_GROUND_SEAM",
    "requested_on_ground={}",
    "delta_y_at_call={}",
    "applied_on_ground={}",
    "GATE_E_CREATE_FINAL_MOTION_SEAM",
    "on_ground_before_write={}",
    "incoming_y={}",
    "applied_y={}",
    "grounded_clip={}",
    "fixture_only=true read_only=true",
]
missing_collider = [token for token in required_collider if token not in collider_source]
if missing_collider:
    raise SystemExit("M1 ground-motion trace lost anchors: " + ", ".join(missing_collider))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", ".teleport(",
    "setBlock(", "syncCarriage(", "setVelocity(", "setOnGround(",
    "keyJump.setDown(true)",
]:
    if forbidden in replacement + floor_replacement:
        raise SystemExit("M1 jump fix introduced mutation token: " + forbidden)

# The collider replacements preserve the exact existing writes. They only name the already-computed
# ground boolean and log state around the same setOnGround/final setDeltaMovement calls.
if ground_replacement.count("entity.setOnGround(appliedOnGround);") != 1:
    raise SystemExit("M1 ground trace must preserve exactly one native setOnGround write")
if motion_replacement.count("entity.setDeltaMovement(appliedMotion);") != 1:
    raise SystemExit("M1 motion trace must preserve exactly one final native-motion write")

java.write_text(source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
collider.write_text(collider_source, encoding="utf-8")
print("M1 jump ground-motion ordering: read-only exact admission predicate + Create seam telemetry installed")
