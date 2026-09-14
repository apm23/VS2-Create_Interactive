#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
collider = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collider_source = collider.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")

# Direct user runtime plus production-world #742 prove a one-frame authority/order defect rather
# than missing floor geometry. On tick 26 Create's OBB pass returns surface=false twice while the
# player is still in the previous carriage frame. Immediately afterwards Phase83/EntityDragger
# reanchors the LocalPlayer by ~3.6688 X, matching the carriage's ~3.6666 frame step. On tick 27
# vanilla therefore consumes a full -0.0784 gravity move before Create sees the corrected horizontal
# frame, producing the visible floor penetration. Move the already-existing authoritative external
# reference-frame transform to the HEAD of the exact Create carriage collision call, after the
# carriage has advanced but before Create samples LocalPlayer bounds. Do not synthesize a floor,
# velocity, gravity, collision response, or arbitrary position correction.
#
# Once VS2 has applied that previous->current reference-frame transform, Create must not apply the
# same carriage frame displacement again through getContactPointMotion. We still invoke Create's
# native method (so Phase170 observes/publishes genuine native ownership), but return Vec3.ZERO only
# to this call site for the exact pre-bridged carriage/tick. Create remains authoritative for OBB
# collision, grounding, wall/floor response, damage and contact registration; VS2 owns only the
# external frame transform. This removes duplicate ownership instead of adding another carry path.

import_anchor = "import org.spongepowered.asm.mixin.injection.At;\n"
if "import org.spongepowered.asm.mixin.injection.Coerce;" not in collider_source:
    if collider_source.count(import_anchor) != 1:
        raise SystemExit("Phase 205 expected one collider At import")
    collider_source = collider_source.replace(
        import_anchor,
        import_anchor + "import org.spongepowered.asm.mixin.injection.Coerce;\n",
        1,
    )

method_anchor = '''    @Redirect(\n        method = "collideEntities",\n        at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/Entity;setOnGround(Z)V"),'''
prebridge = r'''    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)
    private static void vs2$preCollisionExternalFrame(@Coerce Object carriage, CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.createCarryCompat")) return;
        net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;
        if (player == null || !player.onGround() || !(carriage instanceof Entity carriageEntity)) return;

        int carriageId = carriageEntity.getId();
        if (!Integer.toString(carriageId).equals(
                System.getProperty("vs2.phase170NativeContactApplicationCarriageId"))) return;

        String nativeTickRaw = System.getProperty("vs2.phase170NativeContactApplicationTick." + carriageId);
        int nativeAge;
        try {
            nativeAge = player.tickCount - Integer.parseInt(nativeTickRaw == null ? "-2147483648" : nativeTickRaw);
        } catch (NumberFormatException exception) {
            return;
        }
        // #742 is specifically the next-frame stale-position seam. Keep this bridge exact and
        // bounded; longer native-loss recovery remains Phase83's separate, already-proven lease.
        if (nativeAge != 1) return;

        String markerKey = "vs2.phase205PreCollisionReanchorTick." + carriageId;
        String currentTick = Integer.toString(player.tickCount);
        if (currentTick.equals(System.getProperty(markerKey))) return;

        try {
            java.lang.reflect.Method toPreviousLocal = carriage.getClass().getMethod(
                "toLocalVector", Vec3.class, float.class, boolean.class);
            java.lang.reflect.Method toCurrentWorld = carriage.getClass().getMethod(
                "toGlobalVector", Vec3.class, float.class, boolean.class);
            Vec3 previousReference = new Vec3(player.xo, player.yo, player.zo);
            Vec3 previousLocal = (Vec3) toPreviousLocal.invoke(carriage, previousReference, 0.0f, true);
            Vec3 currentTarget = (Vec3) toCurrentWorld.invoke(carriage, previousLocal, 1.0f, false);
            Vec3 frameStep = currentTarget.subtract(player.xo, player.yo, player.zo);
            if (!Double.isFinite(frameStep.x) || !Double.isFinite(frameStep.y) || !Double.isFinite(frameStep.z)
                    || frameStep.lengthSqr() <= 1.0E-16) return;

            org.valkyrienskies.mod.common.util.EntityDragger.reanchorEntityWithExternalFrame(
                player, currentTarget);
            System.setProperty(markerKey, currentTick);
            System.setProperty("vs2.phase205PreCollisionReanchorCarriageId", Integer.toString(carriageId));
            LOGGER.info(
                "GATE_E_PHASE205_PRE_COLLISION_REANCHOR player_tick={} carriage_id={} native_age={} frame_step={} pos={} on_ground={} before_create_obb=true external_reference_frame=true create_collision_authoritative=true",
                player.tickCount, carriageId, nativeAge, frameStep, player.position(), player.onGround());
        } catch (ReflectiveOperationException | RuntimeException exception) {
            LOGGER.info(
                "GATE_E_PHASE205_PRE_COLLISION_REANCHOR_ERROR player_tick={} carriage_id={} type={}",
                player.tickCount, carriageId, exception.getClass().getSimpleName());
        }
    }

    @Redirect(
        method = "collideEntities",
        at = @At(
            value = "INVOKE",
            target = "Lcom/zurrtum/create/content/contraptions/AbstractContraptionEntity;getContactPointMotion(Lnet/minecraft/world/phys/Vec3;)Lnet/minecraft/world/phys/Vec3;"
        ),
        remap = false,
        require = 0
    )
    private static Vec3 vs2$avoidDuplicateExternalFrameCarry(@Coerce Object carriage, Vec3 entityPosition) {
        Vec3 nativeMotion;
        try {
            java.lang.reflect.Method method = carriage.getClass().getMethod("getContactPointMotion", Vec3.class);
            nativeMotion = (Vec3) method.invoke(carriage, entityPosition);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            LOGGER.info("GATE_E_PHASE205_NATIVE_CONTACT_MOTION_ERROR type={}", exception.getClass().getSimpleName());
            return Vec3.ZERO;
        }

        net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;
        if (player == null || !(carriage instanceof Entity carriageEntity)) return nativeMotion;
        int carriageId = carriageEntity.getId();
        boolean preBridged = Integer.toString(player.tickCount).equals(System.getProperty(
            "vs2.phase205PreCollisionReanchorTick." + carriageId));
        if (!preBridged) return nativeMotion;

        LOGGER.info(
            "GATE_E_PHASE205_DUPLICATE_CONTACT_CARRY_SUPPRESSED player_tick={} carriage_id={} native_motion={} pre_collision_frame_already_applied=true create_collision_preserved=true",
            player.tickCount, carriageId, nativeMotion);
        return Vec3.ZERO;
    }

'''
if "GATE_E_PHASE205_PRE_COLLISION_REANCHOR" not in collider_source:
    if collider_source.count(method_anchor) != 1:
        raise SystemExit("Phase 205 expected one pre-setOnGround collider boundary")
    collider_source = collider_source.replace(method_anchor, prebridge + method_anchor, 1)

# The old Phase83 END_CLIENT_TICK bridge is retained for bounded airborne/native-loss recovery,
# but it must not repeat a grounded frame transform that Phase205 already applied before Create OBB.
grounded_anchor = '''            boolean phase83GroundedSupportGap = player.onGround()
                && phase81PhysicalSupport
                && phase83CurrentEnvelopeEligible
                && !phase83NativeAppliedThisTick;'''
grounded_replacement = '''            boolean phase205PreCollisionReanchoredThisTick = Integer.toString(player.tickCount).equals(
                System.getProperty("vs2.phase205PreCollisionReanchorTick." + carriage.getId()));
            boolean phase83GroundedSupportGap = player.onGround()
                && phase81PhysicalSupport
                && phase83CurrentEnvelopeEligible
                && !phase83NativeAppliedThisTick
                && !phase205PreCollisionReanchoredThisTick;'''
if "phase205PreCollisionReanchoredThisTick" not in probe_source:
    if probe_source.count(grounded_anchor) != 1:
        raise SystemExit("Phase 205 expected one Phase83 grounded support-gap boundary")
    probe_source = probe_source.replace(grounded_anchor, grounded_replacement, 1)

# #746 reaches a genuine native airborne arc but intermittently misses the Phase83 external-frame
# application on ticks 47-48, after which the carriage-local X jumps by about one full train frame.
# Do not alter eligibility yet. Publish the already-computed gate inputs at the exact root boundary so
# the next production-world run can identify whether baseline identity, native age, envelope, or the
# de-dup owner is suppressing the reference-frame bridge. This is read-only fixture telemetry.
phase83_gate_anchor = '''            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);
            if (Boolean.getBoolean("vs2.createCarryCompat")'''
phase83_gate_replacement = '''            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);
            if (Boolean.getBoolean("vs2.productionSmokeFixture") && !player.onGround()) {
                LOGGER.info(
                    "GATE_E_PHASE205_AIRBORNE_FRAME_GATE player_tick={} carriage_id={} exact_baseline={} native_age={} supported_baseline_age={} current_envelope={} native_applied_this_tick={} airborne_native_lease={} airborne_supported_baseline_lease={} native_frame_eligible={} external_frame_lease={} collision_eligible={} broadphase={} read_only=true",
                    player.tickCount, carriage.getId(), phase83ExactBaselineCarriage, phase83NativeApplicationAge,
                    phase83SupportedBaselineAge, phase83CurrentEnvelopeEligible, phase83NativeAppliedThisTick,
                    phase83AirborneNativeLease, phase83AirborneSupportedBaselineLease, phase83NativeFrameEligible,
                    phase83ExternalFrameLease, collisionEligible, broadphaseOverlap);
            }
            if (Boolean.getBoolean("vs2.createCarryCompat")'''
if "GATE_E_PHASE205_AIRBORNE_FRAME_GATE" not in probe_source:
    if probe_source.count(phase83_gate_anchor) != 1:
        raise SystemExit("Phase 205 expected one Phase83 external-frame gate boundary")
    probe_source = probe_source.replace(phase83_gate_anchor, phase83_gate_replacement, 1)

required_collider = [
    "GATE_E_PHASE205_PRE_COLLISION_REANCHOR",
    "nativeAge != 1",
    "vs2.phase170NativeContactApplicationCarriageId",
    "vs2.phase170NativeContactApplicationTick.",
    "toLocalVector",
    "toGlobalVector",
    "reanchorEntityWithExternalFrame",
    "before_create_obb=true",
    "GATE_E_PHASE205_DUPLICATE_CONTACT_CARRY_SUPPRESSED",
    "getContactPointMotion",
    "return Vec3.ZERO",
    "create_collision_preserved=true",
]
missing_collider = [token for token in required_collider if token not in collider_source]
if missing_collider:
    raise SystemExit("Phase 205 lost pre-collision ownership anchors: " + ", ".join(missing_collider))

required_probe = [
    "phase205PreCollisionReanchoredThisTick",
    "vs2.phase205PreCollisionReanchorTick.",
    "!phase205PreCollisionReanchoredThisTick",
    "phase83AirborneNativeLease",
    "phase83AirborneSupportedBaselineLease",
    "GATE_E_PHASE205_AIRBORNE_FRAME_GATE",
    "read_only=true",
]
missing_probe = [token for token in required_probe if token not in probe_source]
if missing_probe:
    raise SystemExit("Phase 205 lost Phase83 de-dup/airborne anchors: " + ", ".join(missing_probe))

# No floor coordinate, Y clamp, gravity replacement, synthetic velocity, train/world mutation,
# or LocalPlayer direct setPos is introduced. The only movement call is the existing VS2 reference-
# frame primitive, now ordered before Create's native collision sampling.
inserted = prebridge + grounded_replacement + phase83_gate_replacement
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "floorY", "floor_y", "gravity",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 205 introduced forbidden workaround token: " + forbidden)

collider.write_text(collider_source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
print("Phase 205: orders the existing VS2 external-frame reanchor before Create OBB, suppresses duplicate same-frame Create carry, and traces the airborne Phase83 gate read-only")
