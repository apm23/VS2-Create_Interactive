#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCameraExternalOwnerTurnTrace.java"
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

/**
 * CI-only read-only measurement of the LocalPlayer camera immediately after vanilla
 * Camera.alignWithEntity(). The expected horizontal player render target is rebuilt
 * with the exact external-owner algorithm used later by MixinGameRenderer:
 * previous owner frame -> current owner frame. Nothing is written to camera, player,
 * owner, motion, look, collision, input, timing, or train state.
 *
 * Run 35113644070 proved Camera.update is sparse in this headless fixture but does see
 * LocalPlayer + provider + active external owner + resolvable transforms. Therefore do
 * not decimate active-owner callbacks here: every such callback is a useful turn sample.
 */
@Mixin(Camera.class)
public abstract class MixinCameraExternalOwnerTurnTrace {
    @Shadow private Vec3 position;

    @Unique private static final Logger VS2_CAMERA_TURN_LOGGER = LogManager.getLogger("VS2-CameraTurn");
    @Unique private static int vs2$cameraTurnCalls;
    @Unique private static int vs2$cameraTurnSamples;

    @Inject(
        method = "update",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/client/Camera;alignWithEntity(F)V",
            shift = At.Shift.AFTER
        ),
        require = 1
    )
    private void vs2$traceExternalOwnerCameraAfterAlign(final DeltaTracker deltaTracker, final CallbackInfo ci) {
        final Minecraft minecraft = Minecraft.getInstance();
        final LocalPlayer player = minecraft.player;
        if (player == null || minecraft.level == null || minecraft.getCameraEntity() != player) return;
        if (!(player instanceof IEntityDraggingInformationProvider provider)) return;

        final EntityDraggingInformation dragging = provider.getDraggingInformation();
        if (!dragging.isEntityBeingDraggedByExternalReference()) return;
        final Integer ownerId = dragging.getExternalReferenceOwnerEntityId();
        if (ownerId == null) return;

        final int call = ++vs2$cameraTurnCalls;
        if (call > 4096) return;
        final int sample = ++vs2$cameraTurnSamples;

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
        if (previousLocal == null) return;
        final Vector3d expectedCurrent = ExternalReferenceFrameResolver.currentLocalToWorld(
            minecraft.level, ownerId, previousLocal
        );
        if (expectedCurrent == null) return;

        final Vector3d localX = new Vector3d(previousLocal).add(1.0, 0.0, 0.0);
        final Vector3d currentX = ExternalReferenceFrameResolver.currentLocalToWorld(
            minecraft.level, ownerId, localX
        );
        if (currentX == null) return;
        final double axisX = currentX.x() - expectedCurrent.x();
        final double axisZ = currentX.z() - expectedCurrent.z();
        final double ownerHeading = Math.atan2(axisZ, axisX);

        final double dx = this.position.x - expectedCurrent.x();
        final double dz = this.position.z - expectedCurrent.z();
        final double horizontalError = Math.hypot(dx, dz);

        VS2_CAMERA_TURN_LOGGER.info(
            "REFERENCE_OWNER_V2_CAMERA_TURN_FRAME sample={} call={} player_tick={} owner_id={} partial={} " +
            "camera_x={} camera_y={} camera_z={} expected_x={} expected_y={} expected_z={} " +
            "horizontal_error={} owner_heading={} player_x={} player_y={} player_z={} " +
            "camera_entity_is_player=true read_only=true",
            sample, call, player.tickCount, ownerId, partialTick,
            this.position.x, this.position.y, this.position.z,
            expectedCurrent.x(), expectedCurrent.y(), expectedCurrent.z(),
            horizontalError, ownerHeading,
            player.getX(), player.getY(), player.getZ()
        );
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinCameraExternalOwnerTurnTrace" not in client:
    client.append("MixinCameraExternalOwnerTurnTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("CAMERA_TURN_TRACE installed=true injection=Camera.update_after_alignWithEntity external_owner_render_algorithm=mirrored read_only=true horizon_calls=4096 log_every=1")
