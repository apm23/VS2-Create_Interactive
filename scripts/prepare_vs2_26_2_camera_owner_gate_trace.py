#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCameraExternalOwnerGateTrace.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.Camera;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.joml.Vector3d;
import org.joml.Vector3dc;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.valkyrienskies.mod.common.util.EntityDraggingInformation;
import org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver;
import org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider;

/** CI-only read-only classifier for the external-owner gates at Camera.update. */
@Mixin(Camera.class)
public abstract class MixinCameraExternalOwnerGateTrace {
    @Shadow private Vec3 position;
    @Unique private static final Logger VS2_CAMERA_GATE_LOGGER = LogManager.getLogger("VS2-CameraOwnerGate");
    @Unique private static int vs2$cameraGateCalls;
    @Unique private static int vs2$cameraGateLastTick = Integer.MIN_VALUE;

    @Inject(
        method = "update",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/client/Camera;alignWithEntity(F)V",
            shift = At.Shift.AFTER
        ),
        require = 1
    )
    private void vs2$traceExternalOwnerGateAfterAlign(final DeltaTracker deltaTracker, final CallbackInfo ci) {
        final int call = ++vs2$cameraGateCalls;
        final Minecraft minecraft = Minecraft.getInstance();
        final LocalPlayer player = minecraft.player;
        final boolean levelPresent = minecraft.level != null;
        final boolean cameraIsPlayer = player != null && minecraft.getCameraEntity() == player;
        final boolean providerPresent = player instanceof IEntityDraggingInformationProvider;
        final EntityDraggingInformation dragging = providerPresent
            ? ((IEntityDraggingInformationProvider) player).getDraggingInformation()
            : null;
        final boolean externalActive = dragging != null && dragging.isEntityBeingDraggedByExternalReference();
        final Integer ownerId = dragging != null ? dragging.getExternalReferenceOwnerEntityId() : null;
        final int tick = player != null ? player.tickCount : -1;

        final boolean logGate = player != null
            ? tick != vs2$cameraGateLastTick
            : (call % 600) == 0;
        if (logGate) {
            if (player != null) vs2$cameraGateLastTick = tick;
            VS2_CAMERA_GATE_LOGGER.info(
                "REFERENCE_OWNER_V2_CAMERA_GATE call={} player_tick={} player_present={} level_present={} " +
                "camera_is_player={} provider_present={} external_active={} owner_id={} read_only=true",
                call, tick, player != null, levelPresent, cameraIsPlayer, providerPresent,
                externalActive, ownerId == null ? "null" : ownerId.toString()
            );
        }

        if (player == null || !levelPresent || !cameraIsPlayer || dragging == null || !externalActive || ownerId == null) return;

        final float partialTick = deltaTracker.getGameTimeDeltaPartialTick(true);
        final Vector3dc addedMovement = dragging.getAddedMovementLastTick();
        final double entityMovementX = player.getX() - addedMovement.x() - player.xo;
        final double entityMovementY = player.getY() - addedMovement.y() - player.yo;
        final double entityMovementZ = player.getZ() - addedMovement.z() - player.zo;
        final Vector3d preTransform = new Vector3d(
            player.xo + entityMovementX * partialTick,
            player.yo + entityMovementY * partialTick,
            player.zo + entityMovementZ * partialTick
        );
        final Vector3d previousLocal = ExternalReferenceFrameResolver.previousWorldToLocal(
            minecraft.level, ownerId, preTransform
        );
        final Vector3d expectedCurrent = previousLocal == null ? null
            : ExternalReferenceFrameResolver.currentLocalToWorld(minecraft.level, ownerId, previousLocal);

        VS2_CAMERA_GATE_LOGGER.info(
            "REFERENCE_OWNER_V2_CAMERA_TRANSFORM_GATE call={} player_tick={} owner_id={} previous_local={} current_world={} read_only=true",
            call, tick, ownerId, previousLocal != null, expectedCurrent != null
        );
        if (previousLocal == null || expectedCurrent == null) return;

        final double horizontalError = Math.hypot(
            this.position.x - expectedCurrent.x(), this.position.z - expectedCurrent.z()
        );
        VS2_CAMERA_GATE_LOGGER.info(
            "REFERENCE_OWNER_V2_CAMERA_GATE_FRAME call={} player_tick={} owner_id={} horizontal_error={} " +
            "camera_x={} camera_z={} expected_x={} expected_z={} read_only=true",
            call, tick, ownerId, horizontalError,
            this.position.x, this.position.z, expectedCurrent.x(), expectedCurrent.z()
        );
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinCameraExternalOwnerGateTrace" not in client:
    client.append("MixinCameraExternalOwnerGateTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
print("CAMERA_OWNER_GATE_TRACE installed=true injection=Camera.update_after_alignWithEntity one_gate_row_per_player_tick=true read_only=true")
