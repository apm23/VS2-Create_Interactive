#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCameraExternalReferenceFrameProof.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.Camera;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
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
 * CI-only final Camera.update measurement for the external reference owner.
 * Expected eye position independently rebuilds the proven standing-render basis:
 * ordinary player interpolation with added owner movement removed, then previous
 * owner frame -> current owner frame. This mixin writes nothing.
 */
@Mixin(Camera.class)
public abstract class MixinCameraExternalReferenceFrameProof {
    @Shadow private Vec3 position;
    @Shadow private float eyeHeight;
    @Shadow private float eyeHeightOld;

    @Unique private static final Logger VS2_CAMERA_REFERENCE_LOGGER =
        LogManager.getLogger("VS2-CameraExternalReferenceProof");
    @Unique private static int vs2$cameraReferenceSamples;

    @Inject(method = "update", at = @At("TAIL"), require = 1)
    private void vs2$measureExternalReferenceCamera(final DeltaTracker deltaTracker, final CallbackInfo ci) {
        final Minecraft minecraft = Minecraft.getInstance();
        final LocalPlayer player = minecraft.player;
        if (player == null || minecraft.level == null || minecraft.getCameraEntity() != player) return;
        if (!(player instanceof IEntityDraggingInformationProvider provider)) return;

        final EntityDraggingInformation dragging = provider.getDraggingInformation();
        final Integer ownerId = dragging.getExternalReferenceOwnerEntityId();
        if (ownerId == null || !dragging.isEntityBeingDraggedByExternalReference()) return;
        if (++vs2$cameraReferenceSamples > 4096) return;

        final float partialTick = deltaTracker.getGameTimeDeltaPartialTick(true);
        final Vector3dc addedMovement = dragging.getAddedMovementLastTick();
        final double ordinaryX = player.getX() - addedMovement.x() - player.xo;
        final double ordinaryY = player.getY() - addedMovement.y() - player.yo;
        final double ordinaryZ = player.getZ() - addedMovement.z() - player.zo;
        final double eye = Mth.lerp(partialTick, this.eyeHeightOld, this.eyeHeight);

        final Vector3d preOwnerEye = new Vector3d(
            player.xo + ordinaryX * partialTick,
            player.yo + ordinaryY * partialTick + eye,
            player.zo + ordinaryZ * partialTick
        );
        final Vector3d previousLocal = ExternalReferenceFrameResolver.previousWorldToLocal(
            minecraft.level, ownerId, preOwnerEye
        );
        if (previousLocal == null) return;
        final Vector3d expectedCurrent = ExternalReferenceFrameResolver.currentLocalToWorld(
            minecraft.level, ownerId, previousLocal
        );
        if (expectedCurrent == null) return;

        final Vector3d currentX = ExternalReferenceFrameResolver.currentLocalToWorld(
            minecraft.level, ownerId, new Vector3d(previousLocal).add(1.0, 0.0, 0.0)
        );
        if (currentX == null) return;
        final double ownerHeading = Math.atan2(
            currentX.z() - expectedCurrent.z(),
            currentX.x() - expectedCurrent.x()
        );

        final double horizontalError = Math.hypot(
            this.position.x - expectedCurrent.x(),
            this.position.z - expectedCurrent.z()
        );

        VS2_CAMERA_REFERENCE_LOGGER.info(
            "REFERENCE_OWNER_V2_CAMERA_REFERENCE_FRAME_PROOF sample={} player_tick={} owner_id={} partial={} " +
            "camera_x={} camera_y={} camera_z={} expected_x={} expected_y={} expected_z={} " +
            "horizontal_error={} owner_heading={} owner_age={} on_ground={} read_only=true",
            vs2$cameraReferenceSamples,
            player.tickCount,
            ownerId,
            partialTick,
            this.position.x, this.position.y, this.position.z,
            expectedCurrent.x(), expectedCurrent.y(), expectedCurrent.z(),
            horizontalError,
            ownerHeading,
            dragging.getTicksSinceExternalReferenceOwner(),
            player.onGround()
        );
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinCameraExternalReferenceFrameProof" not in client:
    client.append("MixinCameraExternalReferenceFrameProof")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("CAMERA_EXTERNAL_REFERENCE_PROOF installed=true injection=Camera.update_tail read_only=true horizon=4096")
