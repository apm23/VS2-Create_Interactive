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
 *
 * While external ownership is active, expected eye position independently rebuilds
 * the proven standing-render basis: ordinary player interpolation with added owner
 * movement removed, then previous owner frame -> current owner frame.
 *
 * Run 35128724524 proved the same still-resolvable owner can be cleared by grounded
 * expiry before that carriage later turns. Therefore this verifier also remembers
 * the last active external owner and, after release, computes the hypothetical
 * camera position the production reference-frame branch would have produced from
 * the vanilla-aligned camera point. That continuation is observation-only: it does
 * not restore ownership and writes no camera/player/look/collision/input/train state.
 */
@Mixin(Camera.class)
public abstract class MixinCameraExternalReferenceFrameProof {
    @Shadow private Vec3 position;
    @Shadow private float eyeHeight;
    @Shadow private float eyeHeightOld;

    @Unique private static final Logger VS2_CAMERA_REFERENCE_LOGGER =
        LogManager.getLogger("VS2-CameraExternalReferenceProof");
    @Unique private static int vs2$cameraReferenceSamples;
    @Unique private static Integer vs2$lastObservedExternalOwnerId;

    @Inject(method = "update", at = @At("TAIL"), require = 1)
    private void vs2$measureExternalReferenceCamera(final DeltaTracker deltaTracker, final CallbackInfo ci) {
        final Minecraft minecraft = Minecraft.getInstance();
        final LocalPlayer player = minecraft.player;
        if (player == null || minecraft.level == null || minecraft.getCameraEntity() != player) return;
        if (!(player instanceof IEntityDraggingInformationProvider provider)) return;

        final EntityDraggingInformation dragging = provider.getDraggingInformation();
        final boolean activeExternalOwner = dragging.isEntityBeingDraggedByExternalReference();
        final Integer currentOwnerId = dragging.getExternalReferenceOwnerEntityId();
        if (activeExternalOwner && currentOwnerId != null) {
            vs2$lastObservedExternalOwnerId = currentOwnerId;
        }
        final Integer ownerId = currentOwnerId != null ? currentOwnerId : vs2$lastObservedExternalOwnerId;
        if (ownerId == null) return;
        if (++vs2$cameraReferenceSamples > 4096) return;

        final float partialTick = deltaTracker.getGameTimeDeltaPartialTick(true);
        final Vector3d preOwnerEye;
        final String expectedBasis;
        if (activeExternalOwner && currentOwnerId != null) {
            final Vector3dc addedMovement = dragging.getAddedMovementLastTick();
            final double ordinaryX = player.getX() - addedMovement.x() - player.xo;
            final double ordinaryY = player.getY() - addedMovement.y() - player.yo;
            final double ordinaryZ = player.getZ() - addedMovement.z() - player.zo;
            final double eye = Mth.lerp(partialTick, this.eyeHeightOld, this.eyeHeight);
            preOwnerEye = new Vector3d(
                player.xo + ordinaryX * partialTick,
                player.yo + ordinaryY * partialTick + eye,
                player.zo + ordinaryZ * partialTick
            );
            expectedBasis = "active_player_render_basis";
        } else {
            // Ownership is already gone, so production does not execute its external-owner
            // camera branch. Use the untouched vanilla-aligned camera point as the branch
            // input and ask only where previous-owner -> current-owner mapping would place it.
            preOwnerEye = new Vector3d(this.position.x, this.position.y, this.position.z);
            expectedBasis = "post_release_hypothetical_branch_input";
        }

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
            "horizontal_error={} owner_heading={} owner_age={} on_ground={} active_external={} " +
            "current_owner_id={} expected_basis={} tracked_after_release={} read_only=true",
            vs2$cameraReferenceSamples,
            player.tickCount,
            ownerId,
            partialTick,
            this.position.x, this.position.y, this.position.z,
            expectedCurrent.x(), expectedCurrent.y(), expectedCurrent.z(),
            horizontalError,
            ownerHeading,
            dragging.getTicksSinceExternalReferenceOwner(),
            player.onGround(),
            activeExternalOwner,
            currentOwnerId,
            expectedBasis,
            !activeExternalOwner && vs2$lastObservedExternalOwnerId != null
        );
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinCameraExternalReferenceFrameProof" not in client:
    client.append("MixinCameraExternalReferenceFrameProof")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("CAMERA_EXTERNAL_REFERENCE_PROOF installed=true injection=Camera.update_tail read_only=true horizon=4096 post_release_last_owner_tracking=true")
