#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
collider = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collider_source = collider.read_text(encoding="utf-8")
probe_source = client_probe.read_text(encoding="utf-8")

# Direct runtime #742 proved the pre-OBB reference-frame ordering seam. The read-only floor-owner
# diagnostic #34903325140 then proved a second, narrower defect: Phase205 can reanchor sibling
# carriage 7 while Gate E selected carriage 5 (ticks 21/22/33), and carriage 7 while selected 8
# (tick 38). Keep the existing pre-OBB ordering, but bind it to Gate E's same-tick selected owner.
# This removes duplicate/sibling transform ownership; it does not add collision, carry, gravity,
# velocity, floor clamps, teleport, or recovery behavior.

import_anchor = "import org.spongepowered.asm.mixin.injection.At;\n"
if "import org.spongepowered.asm.mixin.injection.Coerce;" not in collider_source:
    if collider_source.count(import_anchor) != 1:
        raise SystemExit("Phase 205 expected one collider At import")
    collider_source = collider_source.replace(import_anchor, import_anchor + "import org.spongepowered.asm.mixin.injection.Coerce;\n", 1)

method_anchor = '''    @Redirect(\n        method = "collideEntities",\n        at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/Entity;setOnGround(Z)V"),'''
prebridge = r'''    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)
    private static void vs2$preCollisionExternalFrame(@Coerce Object carriage, CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.createCarryCompat")) return;
        net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;
        if (player == null || !player.onGround() || !(carriage instanceof Entity carriageEntity)) return;

        int carriageId = carriageEntity.getId();
        String selectedTick = System.getProperty("vs2.phase205SelectedCarriageTick");
        String selectedId = System.getProperty("vs2.phase205SelectedCarriageId");
        if (!Integer.toString(player.tickCount).equals(selectedTick)
                || !Integer.toString(carriageId).equals(selectedId)) return;
        String nativeTickRaw = System.getProperty("vs2.phase170NativeContactApplicationTick." + carriageId);
        int nativeAge;
        try {
            nativeAge = player.tickCount - Integer.parseInt(nativeTickRaw == null ? "-2147483648" : nativeTickRaw);
        } catch (NumberFormatException exception) {
            return;
        }
        if (nativeAge != 1) return;

        String markerKey = "vs2.phase205PreCollisionReanchorTick." + carriageId;
        String currentTick = Integer.toString(player.tickCount);
        if (currentTick.equals(System.getProperty(markerKey))) return;

        try {
            java.lang.reflect.Method toPreviousLocal = carriage.getClass().getMethod("toLocalVector", Vec3.class, float.class, boolean.class);
            java.lang.reflect.Method toCurrentWorld = carriage.getClass().getMethod("toGlobalVector", Vec3.class, float.class, boolean.class);
            Vec3 previousReference = new Vec3(player.xo, player.yo, player.zo);
            Vec3 previousLocal = (Vec3) toPreviousLocal.invoke(carriage, previousReference, 0.0f, true);
            Vec3 currentTarget = (Vec3) toCurrentWorld.invoke(carriage, previousLocal, 1.0f, false);
            Vec3 frameStep = currentTarget.subtract(player.xo, player.yo, player.zo);
            if (!Double.isFinite(frameStep.x) || !Double.isFinite(frameStep.y) || !Double.isFinite(frameStep.z)
                    || frameStep.lengthSqr() <= 1.0E-16) return;

            org.valkyrienskies.mod.common.util.EntityDragger.reanchorEntityWithExternalFrame(player, currentTarget);
            System.setProperty(markerKey, currentTick);
            System.setProperty("vs2.phase205PreCollisionReanchorCarriageId", Integer.toString(carriageId));
            LOGGER.info("GATE_E_PHASE205_PRE_COLLISION_REANCHOR player_tick={} carriage_id={} native_age={} frame_step={} pos={} on_ground={} before_create_obb=true external_reference_frame=true create_collision_authoritative=true selected_owner=true",
                player.tickCount, carriageId, nativeAge, frameStep, player.position(), player.onGround());
        } catch (ReflectiveOperationException | RuntimeException exception) {
            LOGGER.info("GATE_E_PHASE205_PRE_COLLISION_REANCHOR_ERROR player_tick={} carriage_id={} type={}", player.tickCount, carriageId, exception.getClass().getSimpleName());
        }
    }

    @Redirect(method = "collideEntities", at = @At(value = "INVOKE", target = "Lcom/zurrtum/create/content/contraptions/AbstractContraptionEntity;getContactPointMotion(Lnet/minecraft/world/phys/Vec3;)Lnet/minecraft/world/phys/Vec3;"), remap = false, require = 0)
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
        boolean preBridged = Integer.toString(player.tickCount).equals(System.getProperty("vs2.phase205PreCollisionReanchorTick." + carriageId));
        if (!preBridged) return nativeMotion;
        LOGGER.info("GATE_E_PHASE205_DUPLICATE_CONTACT_CARRY_SUPPRESSED player_tick={} carriage_id={} native_motion={} pre_collision_frame_already_applied=true create_collision_preserved=true", player.tickCount, carriageId, nativeMotion);
        return Vec3.ZERO;
    }

'''
if "GATE_E_PHASE205_PRE_COLLISION_REANCHOR" not in collider_source:
    if collider_source.count(method_anchor) != 1:
        raise SystemExit("Phase 205 expected one pre-setOnGround collider boundary")
    collider_source = collider_source.replace(method_anchor, prebridge + method_anchor, 1)

# Publish the already-selected Gate E carriage for the same LocalPlayer tick. This is owner identity
# only; no movement or collision response occurs here.
selection_anchor = '''            LOGGER.info(
                "GATE_E_CARRIAGE_SELECTION player_tick={} selected_id={} selected_center_d2={} on_ground={} candidate_count={} arbitration=nearest_entity_center read_only=true",
                player.tickCount,
                carriage == null ? -1 : carriage.getId(),
                carriage == null ? Double.NaN : carriage.distanceToSqr(player),
                player.onGround(), carriageCandidates.size());'''
selection_replacement = selection_anchor + '''
            System.setProperty("vs2.phase205SelectedCarriageTick", Integer.toString(player.tickCount));
            System.setProperty("vs2.phase205SelectedCarriageId", Integer.toString(carriage == null ? -1 : carriage.getId()));'''
if "vs2.phase205SelectedCarriageTick" not in probe_source:
    if probe_source.count(selection_anchor) != 1:
        raise SystemExit("Phase 205 expected one Gate E carriage selection publication boundary")
    probe_source = probe_source.replace(selection_anchor, selection_replacement, 1)

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

phase83_gate_anchor = '''            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);
            if (Boolean.getBoolean("vs2.createCarryCompat")'''
phase83_gate_replacement = '''            boolean phase83ExternalFrameLease = !phase83NativeAppliedThisTick
                && (phase83GroundedSupportGap || phase83AirborneNativeLease || phase83AirborneSupportedBaselineLease);
            if (Boolean.getBoolean("vs2.productionSmokeFixture") && !player.onGround()) {
                LOGGER.info("GATE_E_PHASE205_AIRBORNE_FRAME_GATE player_tick={} carriage_id={} exact_baseline={} native_age={} supported_baseline_age={} current_envelope={} native_applied_this_tick={} airborne_native_lease={} airborne_supported_baseline_lease={} native_frame_eligible={} external_frame_lease={} collision_eligible={} broadphase={} read_only=true",
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

required_collider = ["GATE_E_PHASE205_PRE_COLLISION_REANCHOR", "nativeAge != 1", "vs2.phase205SelectedCarriageTick", "vs2.phase205SelectedCarriageId", "toLocalVector", "toGlobalVector", "reanchorEntityWithExternalFrame", "selected_owner=true", "GATE_E_PHASE205_DUPLICATE_CONTACT_CARRY_SUPPRESSED", "getContactPointMotion", "return Vec3.ZERO", "create_collision_preserved=true"]
missing_collider = [token for token in required_collider if token not in collider_source]
if missing_collider:
    raise SystemExit("Phase 205 lost pre-collision ownership anchors: " + ", ".join(missing_collider))
required_probe = ["vs2.phase205SelectedCarriageTick", "vs2.phase205SelectedCarriageId", "phase205PreCollisionReanchoredThisTick", "vs2.phase205PreCollisionReanchorTick.", "!phase205PreCollisionReanchoredThisTick", "phase83AirborneNativeLease", "phase83AirborneSupportedBaselineLease", "GATE_E_PHASE205_AIRBORNE_FRAME_GATE", "read_only=true"]
missing_probe = [token for token in required_probe if token not in probe_source]
if missing_probe:
    raise SystemExit("Phase 205 lost Phase83 de-dup/airborne anchors: " + ", ".join(missing_probe))

inserted = prebridge + selection_replacement + grounded_replacement + phase83_gate_replacement
for forbidden in ["player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "floorY", "floor_y", "gravity"]:
    if forbidden in inserted:
        raise SystemExit("Phase 205 introduced forbidden workaround token: " + forbidden)

collider.write_text(collider_source, encoding="utf-8")
client_probe.write_text(probe_source, encoding="utf-8")
print("Phase 205: binds the existing pre-OBB external-frame reanchor to the same-tick selected Create carriage owner; duplicate sibling ownership is rejected")
