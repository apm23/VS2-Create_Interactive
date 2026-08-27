#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# 1) DataComponentType<T> requires non-null T on 26.2.
p = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/VSDataComponents.kt"
t = p.read_text(encoding="utf-8")
old = "    private fun <T> register(name: String, builder: () -> DataComponentType<T>): DataComponentType<T> {"
new = "    private fun <T : Any> register(name: String, builder: () -> DataComponentType<T>): DataComponentType<T> {"
if old not in t:
    raise SystemExit("VSDataComponents generic anchor missing")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

# 2) Fabric Networking API 26.x directional registry rename.
p = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/VSFabricNetworking.kt"
t = p.read_text(encoding="utf-8")
repls = {
    "PayloadTypeRegistry.playC2S()": "PayloadTypeRegistry.serverboundPlay()",
    "PayloadTypeRegistry.playS2C()": "PayloadTypeRegistry.clientboundPlay()",
}
for old, new in repls.items():
    if old not in t:
        raise SystemExit(f"VSFabricNetworking expected API missing: {old}")
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8")

# 3) Physics-core gate: remove only optional visual/map Fabric Kotlin sources.
p = ROOT / "fabric/build.gradle"
t = p.read_text(encoding="utf-8")
anchor = '            exclude "org/valkyrienskies/mod/fabric/compat/hexcasting/**"\n'
if anchor not in t:
    raise SystemExit("fabric kotlin exclusion anchor missing")
extra = anchor + '''            // MC 26.2 core gate: restore these in the client-render/optional-compat phase.\n            exclude "org/valkyrienskies/mod/fabric/compat/dynmap/**"\n            exclude "org/valkyrienskies/mod/fabric/common/ShipInfluenceBorderRenderer.kt"\n'''
t = t.replace(anchor, extra, 1)
p.write_text(t, encoding="utf-8")

# 4) ValkyrienSkiesModFabric mixes critical common init with old client convenience
#    APIs and ForgeConfigAPIPort shims whose 26.2 packages changed. Preserve all
#    registry/server/datapack/common init; park the client command/render/keybind
#    block and config shim for the dedicated restoration passes.
p = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/ValkyrienSkiesModFabric.kt"
t = p.read_text(encoding="utf-8")

# Remove imports that no longer exist in Fabric API 26.2 or are only used by the
# parked client/debug/config code.
remove_import_prefixes = [
    "import com.mojang.brigadier.arguments.BoolArgumentType",
    "import com.mojang.brigadier.arguments.DoubleArgumentType",
    "import com.mojang.brigadier.arguments.StringArgumentType",
    "import net.fabricmc.fabric.api.client.command.v2.",
    "import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents",
    "import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper",
    "import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry",
    "import net.minecraft.client.CameraType",
    "import net.minecraft.client.gui.screens.ChatScreen",
    "import net.minecraft.client.renderer.entity.EntityRendererProvider.Context",
    "import net.minecraft.network.chat.Component",
    "import org.valkyrienskies.mod.client.EmptyRenderer",
    "import org.valkyrienskies.mod.client.ShipCameraZoom",
    "import org.valkyrienskies.mod.client.ShipDebugRender",
    "import org.valkyrienskies.mod.client.ShipGamepad",
    "import org.valkyrienskies.mod.client.ShipMountPerspective",
    "import fuzs.forgeconfigapiport.fabric.api.neoforge.v4.",
    "import net.neoforged.fml.config.ModConfig",
    "import org.valkyrienskies.mod.common.config.VSClientConfig",
    "import org.valkyrienskies.mod.common.config.VSKeyBindings",
    "import org.valkyrienskies.mod.common.networking.PacketRequestPassengerSeat",
    "import org.valkyrienskies.mod.common.vsCore",
]
lines = []
for line in t.splitlines():
    if any(line.startswith(prefix) for prefix in remove_import_prefixes):
        continue
    lines.append(line)
t = "\n".join(lines) + "\n"

# Keep client JSON load harmlessly for now, but do not call the parked legacy
# client initializer. Runtime client restoration gets its own gate later.
t = t.replace("            onInitializeClient()\n", "            // Client API restoration is gated separately for MC 26.2.\n", 1)

# Remove ForgeConfigAPIPort direct shim block. Config values retain compiled-in
# defaults for the core boot gate; correct 26.2 config persistence is restored
# before final gameplay acceptance tests.
start_marker = "        // Register our four ModConfigSpecs with fcap-fabric's NeoForgeConfigRegistry\n"
end_marker = "        // VSEntityManager.registerContraptionHandler(ContraptionShipyardEntityHandlerFabric)\n"
start = t.find(start_marker)
end = t.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("ValkyrienSkiesModFabric config block markers missing")
t = t[:start] + "        // ForgeConfigAPIPort 26.2 adapter restoration is gated separately; defaults are active.\n" + t[end:]

# Park old client command/render/keybind/camera implementation wholesale. This
# avoids pretending those APIs are ported while allowing server/physics runtime
# to become testable first.
start_marker = "    /**\n     * Only run on client\n     */\n    private fun onInitializeClient() {\n"
end_marker = "    private fun registerBlockAndItem(registryName: String, block: Block): Item {\n"
start = t.find(start_marker)
end = t.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("ValkyrienSkiesModFabric client block markers missing")
replacement = '''    /**\n     * Client-side render/command/keybind integration is restored after the\n     * Fabric physics/server boot gate is green on Minecraft 26.2.\n     */\n    private fun onInitializeClient() {\n        // intentionally empty during the core port gate\n    }\n\n'''
t = t[:start] + replacement + t[end:]
p.write_text(t, encoding="utf-8")

print("Ported Fabric networking/data components and isolated legacy client/config/optional Fabric seams")
