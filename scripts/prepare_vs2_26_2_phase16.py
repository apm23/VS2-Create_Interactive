#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# Minecraft 26.2 replaced large parts of the client render pipeline (including
# MultiBufferSource-era entity/terrain paths). Keep those legacy sources out of
# the physics-core compile pass. This is intentionally narrow: player/entity
# movement, collision, chunk, assembly, and server mixins remain enabled.
p = ROOT / "common/build.gradle"
t = p.read_text(encoding="utf-8")
anchor = '            exclude "org/valkyrienskies/mod/mixin/world/level/levelgen/MixinNoiseBasedChunkGenerator.java"\n'
if anchor not in t:
    raise SystemExit("Expected Java source exclusion anchor not found")
extra = anchor + '''            // MC 26.2 core-port isolation: legacy 1.21.x rendering/optional compat.\n            exclude "org/valkyrienskies/mod/common/render/**"\n            exclude "org/valkyrienskies/mod/mixin/client/renderer/MixinLevelRenderer.java"\n            exclude "org/valkyrienskies/mod/mixin/client/renderer/MixinFeatureRenderDispatcher.java"\n            exclude "org/valkyrienskies/mod/mixin/client/world/MixinClientChunkCache.java"\n            exclude "org/valkyrienskies/mod/mixin/client/world/MixinLevelChunkClientRender.java"\n            exclude "org/valkyrienskies/mod/mixin/feature/vs2_alpha_hud/**"\n            exclude "org/valkyrienskies/mod/mixin/feature/hit_outline/**"\n            exclude "org/valkyrienskies/mod/mixin/feature/shipyard_entities/MixinEntityRenderDispatcher.java"\n            exclude "org/valkyrienskies/mod/mixin/mod_compat/sodium/**"\n            exclude "org/valkyrienskies/mod/mixinducks/mod_compat/sodium/**"\n            exclude "org/valkyrienskies/mod/compat/SodiumCompat.java"\n            exclude "org/valkyrienskies/mod/compat/create/**"\n'''
t = t.replace(anchor, extra, 1)
p.write_text(t, encoding="utf-8")

# Weather2 has no 26.2 dependency in this core build. Remove only its optional
# tick hook; do not remove MixinMinecraftServer because it owns the VS pipeline,
# chunk activation, ship-world setup, and server tick integration.
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/server/MixinMinecraftServer.java"
t = p.read_text(encoding="utf-8")
t = t.replace("import org.valkyrienskies.mod.compat.Weather2Compat;\r\n", "")
t = t.replace("import org.valkyrienskies.mod.compat.Weather2Compat;\n", "")
old_crlf = "            if (LoadedMods.getWeather2())\r\n                Weather2Compat.INSTANCE.tick(level);\r\n"
old_lf = "            if (LoadedMods.getWeather2())\n                Weather2Compat.INSTANCE.tick(level);\n"
if old_crlf in t:
    t = t.replace(old_crlf, "", 1)
elif old_lf in t:
    t = t.replace(old_lf, "", 1)
else:
    raise SystemExit("Expected optional Weather2 tick hook not found")
p.write_text(t, encoding="utf-8")

# Match runtime mixin registration to the deliberately excluded visual sources,
# otherwise a successful compile would still crash at boot while Mixin tries to
# load classes that are no longer packaged.
p = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
data = json.loads(p.read_text(encoding="utf-8"))
remove_mixins = {
    "feature.hit_outline.MixinLevelRenderer",
}
remove_client = {
    "client.renderer.MixinLevelRenderer",
    "client.renderer.MixinFeatureRenderDispatcher",
    "client.world.MixinClientChunkCache",
    "client.world.MixinLevelChunkClientRender",
    "feature.shipyard_entities.MixinEntityRenderDispatcher",
    "feature.vs2_alpha_hud.MixinGui",
    "mod_compat.sodium.MixinChunkTracker",
    "mod_compat.sodium.MixinDefaultChunkRenderer",
    "mod_compat.sodium.MixinRenderSection",
    "mod_compat.sodium.MixinRenderSectionManager",
}
missing = remove_mixins - set(data.get("mixins", []))
missing |= remove_client - set(data.get("client", []))
if missing:
    raise SystemExit(f"Expected mixin entries missing before phase16 removal: {sorted(missing)}")
data["mixins"] = [x for x in data.get("mixins", []) if x not in remove_mixins]
data["client"] = [x for x in data.get("client", []) if x not in remove_client]
data["compatibilityLevel"] = "JAVA_25"
p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Isolated legacy 1.21 render/optional compat Java while preserving VS2 physics/server core")
