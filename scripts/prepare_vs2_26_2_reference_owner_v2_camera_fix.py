#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
camera_file = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/MixinCamera.java"

text = camera_file.read_text(encoding="utf-8")

import_anchor = "import org.valkyrienskies.mod.common.VSGameUtilsKt;\n"
extra_imports = (
    "import org.valkyrienskies.mod.common.util.EntityDraggingInformation;\n"
    "import org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver;\n"
    "import org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider;\n"
)
if "import org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver;" not in text:
    if text.count(import_anchor) != 1:
        raise SystemExit("camera reference fix lost VSGameUtils import anchor")
    text = text.replace(import_anchor, import_anchor + extra_imports, 1)

anchor = '''        final float partialTicks = deltaTracker.getGameTimeDeltaPartialTick(true);
        final ShipMountedToData shipMountedToData = VSGameUtilsKt.getShipMountedToData(localPlayer, partialTicks);
'''
replacement = '''        final float partialTicks = deltaTracker.getGameTimeDeltaPartialTick(true);

        // REFERENCE_OWNER_V2_CAMERA_POSITIONAL_FRAME:
        // Reuse the native VS2 Camera.update post-align seam, but only map the already-aligned
        // camera point from the previous external-owner frame into the current owner frame.
        // The ordinary LocalPlayer motion component is left in vanilla interpolation space by
        // removing only this tick's VS2-owned addedMovement fraction before the frame transform.
        // This is the same previous->current transform basis used by the proven standing-player
        // render path. It never changes yaw, pitch, camera quaternion, look vectors, player
        // position/motion, Create collision state, or train state.
        if (minecraft.getCameraEntity() == localPlayer
            && localPlayer instanceof IEntityDraggingInformationProvider referenceProvider) {
            final EntityDraggingInformation dragging = referenceProvider.getDraggingInformation();
            final Integer externalOwnerId = dragging.getExternalReferenceOwnerEntityId();
            if (externalOwnerId != null && dragging.isEntityBeingDraggedByExternalReference()) {
                final Vector3dc addedMovement = dragging.getAddedMovementLastTick();
                final Vector3d cameraPreOwnerTransform = new Vector3d(
                    this.position.x - addedMovement.x() * partialTicks,
                    this.position.y - addedMovement.y() * partialTicks,
                    this.position.z - addedMovement.z() * partialTicks
                );
                final Vector3d cameraPreviousLocal = ExternalReferenceFrameResolver.previousWorldToLocal(
                    clientLevel, externalOwnerId, cameraPreOwnerTransform
                );
                if (cameraPreviousLocal != null) {
                    final Vector3d cameraCurrentWorld = ExternalReferenceFrameResolver.currentLocalToWorld(
                        clientLevel, externalOwnerId, cameraPreviousLocal
                    );
                    if (cameraCurrentWorld != null) {
                        this.setPosition(cameraCurrentWorld.x(), cameraCurrentWorld.y(), cameraCurrentWorld.z());
                        return;
                    }
                }
            }
        }

        final ShipMountedToData shipMountedToData = VSGameUtilsKt.getShipMountedToData(localPlayer, partialTicks);
'''
if "REFERENCE_OWNER_V2_CAMERA_POSITIONAL_FRAME:" not in text:
    if text.count(anchor) != 1:
        raise SystemExit(f"camera reference fix expected exactly one Phase46 partial-tick anchor, found {text.count(anchor)}")
    text = text.replace(anchor, replacement, 1)

start = text.find("// REFERENCE_OWNER_V2_CAMERA_POSITIONAL_FRAME:")
end = text.find("final ShipMountedToData shipMountedToData", start)
if start < 0 or end < 0:
    raise SystemExit("camera reference fix could not bound installed external-owner branch")
branch = text[start:end]
for forbidden in [
    "setRotation", "valkyrienskies$setRotationWithShipTransform", "this.rotation",
    "this.yRot", "this.xRot", "setYRot", "setXRot",
    "localPlayer.setPos", "localPlayer.setDeltaMovement", "teleport",
]:
    if forbidden in branch:
        raise SystemExit("camera reference fix introduced forbidden camera/body authority: " + forbidden)

required = [
    "minecraft.getCameraEntity() == localPlayer",
    "isEntityBeingDraggedByExternalReference()",
    "getAddedMovementLastTick()",
    "previousWorldToLocal(",
    "currentLocalToWorld(",
    "this.setPosition(cameraCurrentWorld.x(), cameraCurrentWorld.y(), cameraCurrentWorld.z())",
]
for token in required:
    if token not in branch:
        raise SystemExit("camera reference fix lost required transform token: " + token)

camera_file.write_text(text, encoding="utf-8")
print("REFERENCE_OWNER_V2_CAMERA_POSITIONAL_FRAME installed=true seam=Camera.update_after_alignWithEntity")
print("REFERENCE_OWNER_V2_CAMERA_POSITIONAL_FRAME transform=previous_owner_to_current_owner look_mutated=false player_mutated=false collision_mutated=false")
