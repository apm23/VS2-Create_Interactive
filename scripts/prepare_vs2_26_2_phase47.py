#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
game_renderer = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/renderer/MixinGameRenderer.java"
camera_mixin = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/MixinCamera.java"

game_text = game_renderer.read_text(encoding="utf-8")

# MC 26.2 removed GameRenderer.getDepthFar(). Camera.update() now owns depthFar and
# consumes it immediately for cull-frustum + perspective projection. Retire the stale
# GameRenderer ModifyReturnValue hook; Phase 47 reinstalls the same policy in Camera.
start = game_text.find('    @ModifyReturnValue(method = "getDepthFar"')
if start < 0:
    raise SystemExit("Expected legacy getDepthFar ModifyReturnValue hook missing before Phase 47")
# The old hook is the final member before the class closing brace.
end = game_text.rfind('\n}')
if end < start:
    raise SystemExit("Could not locate MixinGameRenderer class end for Phase 47")
game_text = game_text[:start] + game_text[end:]
game_text = game_text.replace("import com.llamalad7.mixinextras.injector.ModifyReturnValue;\n", "", 1)
if '@ModifyReturnValue(method = "getDepthFar"' in game_text or 'public float includeShipsIn' in game_text:
    raise SystemExit("Stale GameRenderer far-plane hook survived Phase 47")
game_renderer.write_text(game_text, encoding="utf-8")

camera_text = camera_mixin.read_text(encoding="utf-8")

if "import org.valkyrienskies.mod.common.config.VSClientConfig;\n" not in camera_text:
    anchor = "import org.valkyrienskies.mod.common.entity.ShipMountingEntity;\n"
    if anchor not in camera_text:
        raise SystemExit("Expected Phase 46 camera import anchor missing")
    camera_text = camera_text.replace(
        anchor,
        anchor + "import org.valkyrienskies.mod.common.config.VSClientConfig;\n",
        1,
    )

# Camera.depthFar is private in MC 26.2. Shadow it so the ship-distance policy can be
# applied after vanilla calculates its baseline but before culling/projection use it.
shadow_anchor = "    @Shadow\n    private float eyeHeightOld;\n"
shadow_block = "    @Shadow\n    private float eyeHeightOld;\n    @Shadow\n    private float depthFar;\n"
if "private float depthFar;" not in camera_text:
    if shadow_anchor not in camera_text:
        raise SystemExit("Expected Camera eyeHeightOld shadow anchor missing")
    camera_text = camera_text.replace(shadow_anchor, shadow_block, 1)

hook_anchor = "        final Minecraft minecraft = Minecraft.getInstance();\n"
far_plane_logic = '''        final Minecraft minecraft = Minecraft.getInstance();

        // MC 26.2 moved the far plane from GameRenderer.getDepthFar() into Camera.depthFar.
        // Preserve VS2's fixed minimum ship render distance only while ships are loaded,
        // before vanilla builds the cull frustum and projection from this value.
        if (VSGameUtilsKt.getShipObjectWorld(minecraft).getLoadedShips().iterator().hasNext()) {
            this.depthFar = Math.max(this.depthFar, VSClientConfig.CLIENT.getShipRenderDistance());
        }
'''
if "MC 26.2 moved the far plane" not in camera_text:
    if hook_anchor not in camera_text:
        raise SystemExit("Expected Phase 46 Minecraft hook anchor missing")
    camera_text = camera_text.replace(hook_anchor, far_plane_logic, 1)

if "this.depthFar = Math.max(this.depthFar, VSClientConfig.CLIENT.getShipRenderDistance())" not in camera_text:
    raise SystemExit("Phase 47 Camera.depthFar extension was not installed")
# Only executable/injection leftovers are invalid; documentation may legitimately name
# the removed GameRenderer.getDepthFar() API while explaining the 26.2 migration.
if '@ModifyReturnValue(method = "getDepthFar"' in camera_text or 'public float includeShipsIn' in camera_text:
    raise SystemExit("Unexpected executable legacy far-plane hook survived in MixinCamera")

camera_mixin.write_text(camera_text, encoding="utf-8")
print("Phase 47: moved ship far-plane extension from removed GameRenderer.getDepthFar into Camera.update before frustum/projection")
