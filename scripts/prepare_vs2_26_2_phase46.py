#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

game_renderer = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/renderer/MixinGameRenderer.java"
camera_mixin = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/MixinCamera.java"

# MC 26.2 removed GameRenderer.updateCamera(). Camera.update(DeltaTracker) now owns
# camera alignment, FOV, cull-frustum, and projection preparation. The ship mount
# transform must run after alignWithEntity(), but before frustum/projection are built.
game_text = game_renderer.read_text(encoding="utf-8")
start_marker = "    // Mount the player's camera to the ship they are mounted on."
end_marker = "    // endregion"
start = game_text.find(start_marker)
if start < 0:
    raise SystemExit("Expected legacy GameRenderer ship-camera block missing before Phase 46")
end = game_text.find(end_marker, start)
if end < 0:
    raise SystemExit("Expected legacy GameRenderer ship-camera end marker missing before Phase 46")
end += len(end_marker)
game_text = (
    game_text[:start]
    + "    // MC 26.2: ship-mounted camera mutation moved into MixinCamera.update immediately\n"
      "    // after Camera.alignWithEntity(), before vanilla builds cull-frustum/projection.\n"
      "    // endregion"
    + game_text[end:]
)
if 'method = "updateCamera"' in game_text:
    raise SystemExit("Stale GameRenderer.updateCamera injection survived Phase 46")
game_renderer.write_text(game_text, encoding="utf-8")

camera_text = camera_mixin.read_text(encoding="utf-8")

imports = [
    ("import net.minecraft.client.Camera;\n", "import net.minecraft.client.Camera;\nimport net.minecraft.client.CameraType;\nimport net.minecraft.client.DeltaTracker;\nimport net.minecraft.client.Minecraft;\nimport net.minecraft.client.multiplayer.ClientLevel;\nimport net.minecraft.client.player.LocalPlayer;\n"),
    ("import org.spongepowered.asm.mixin.Unique;\n", "import org.spongepowered.asm.mixin.Unique;\nimport org.spongepowered.asm.mixin.injection.At;\nimport org.spongepowered.asm.mixin.injection.Inject;\nimport org.spongepowered.asm.mixin.injection.callback.CallbackInfo;\n"),
    ("import org.valkyrienskies.mod.client.ShipCameraZoom;\n", "import org.valkyrienskies.mod.client.ShipCameraZoom;\nimport org.valkyrienskies.mod.client.ShipMountPerspective;\nimport org.valkyrienskies.mod.common.VSGameUtilsKt;\nimport org.valkyrienskies.mod.common.entity.ShipMountedToData;\nimport org.valkyrienskies.mod.common.entity.ShipMountingEntity;\n"),
]
for old, new in imports:
    if new in camera_text:
        continue
    if old not in camera_text:
        raise SystemExit(f"Expected import anchor missing before Phase 46: {old.strip()}")
    camera_text = camera_text.replace(old, new, 1)

anchor = "    @Override\n    public void setupWithShipMounted"
if anchor not in camera_text:
    raise SystemExit("Expected setupWithShipMounted anchor missing before Phase 46")

hook = '''    /**
     * MC 26.2 camera pipeline hook.
     *
     * Vanilla Camera.update() now performs alignWithEntity(), then computes FOV,
     * cull-frustum and projection. Applying the ship transform at this exact point
     * makes every downstream camera snapshot/culling pass see the same ship-space pose.
     */
    @Inject(
        method = "update",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/client/Camera;alignWithEntity(F)V",
            shift = At.Shift.AFTER
        ),
        require = 1
    )
    private void valkyrienskies$mountCameraToShip26_2(final DeltaTracker deltaTracker, final CallbackInfo ci) {
        this.resetShipMountedRenderTransform();
        ShipCameraZoom.setShipCameraActive(false);

        final Minecraft minecraft = Minecraft.getInstance();
        final ClientLevel clientLevel = minecraft.level;
        final LocalPlayer localPlayer = minecraft.player;
        if (clientLevel == null || localPlayer == null) {
            return;
        }

        final float partialTicks = deltaTracker.getGameTimeDeltaPartialTick(true);
        final ShipMountedToData shipMountedToData = VSGameUtilsKt.getShipMountedToData(localPlayer, partialTicks);
        if (shipMountedToData == null || localPlayer.getVehicle() == null) {
            return;
        }

        final ClientShip clientShip = (ClientShip) shipMountedToData.getShipMountedTo();
        final Entity cameraEntity = minecraft.getCameraEntity() == null ? localPlayer : minecraft.getCameraEntity();
        final Entity vehicle = localPlayer.getVehicle();
        final boolean standing = vehicle instanceof ShipMountingEntity;
        final CameraType cameraType = minecraft.options.getCameraType();

        if (standing) {
            // Preserve the VS mounted F5 cycle: vanilla first/back/front views remain vanilla;
            // only the virtual ship-view slot receives the ship-coupled camera transform.
            if (!ShipMountPerspective.isShipViewEngaged()) {
                return;
            }
            ShipCameraZoom.setShipCameraActive(true);
            this.setupWithShipMounted(
                clientLevel,
                cameraEntity,
                true,
                false,
                partialTicks,
                clientShip,
                shipMountedToData.getMountPosInShip()
            );
            return;
        }

        // Sitting helm / non-helm passenger keeps the original VS2 behavior.
        final boolean thirdPerson = !cameraType.isFirstPerson();
        ShipCameraZoom.setShipCameraActive(thirdPerson);
        this.setupWithShipMounted(
            clientLevel,
            cameraEntity,
            thirdPerson,
            cameraType.isMirrored(),
            partialTicks,
            clientShip,
            shipMountedToData.getMountPosInShip()
        );
    }

'''
if "valkyrienskies$mountCameraToShip26_2" not in camera_text:
    camera_text = camera_text.replace(anchor, hook + anchor, 1)

if 'target = "Lnet/minecraft/client/Camera;alignWithEntity(F)V"' not in camera_text:
    raise SystemExit("Phase 46 Camera.update injection target was not installed")
if 'method = "updateCamera"' in camera_text:
    raise SystemExit("Legacy updateCamera reference unexpectedly present in MixinCamera")

camera_mixin.write_text(camera_text, encoding="utf-8")
print("Phase 46: moved ship camera mount into Camera.update after alignWithEntity and before frustum/projection")
