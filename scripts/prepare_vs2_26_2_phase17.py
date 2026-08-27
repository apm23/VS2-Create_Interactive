#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"

def edit(rel, fn):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    n = fn(t)
    if n == t:
        raise SystemExit(f"phase17 made no change to {rel}")
    p.write_text(n, encoding="utf-8")

# ---------------------------------------------------------------------------
# 1) Keep optional/legacy rendering out of the physics-core compile gate.
#    These are not needed for ship collision, player movement, assembly, world
#    persistence, or server ticking. They will be restored in the render phase.
# ---------------------------------------------------------------------------
p = ROOT / "common/build.gradle"
t = p.read_text(encoding="utf-8")
anchor = '            exclude "org/valkyrienskies/mod/compat/create/**"\n'
if anchor not in t:
    raise SystemExit("phase17 source exclusion anchor missing")
extra = anchor + '''            exclude "org/valkyrienskies/mod/compat/voxy/**"\n            exclude "org/valkyrienskies/mod/mixin/client/renderer/MixinViewAreaVanilla.java"\n            exclude "org/valkyrienskies/mod/mixin/client/MixinWeatherEffectRenderer.java"\n            exclude "org/valkyrienskies/mod/mixin/client/MixinMouseHandler.java"\n'''
t = t.replace(anchor, extra, 1)
p.write_text(t, encoding="utf-8")

mix = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
data = json.loads(mix.read_text(encoding="utf-8"))
remove_any = {
    "client.renderer.MixinViewAreaVanilla",
    "client.MixinWeatherEffectRenderer",
    "client.MixinMouseHandler",
    "mod_compat.voxy.MixinVoxyIngestShipyardGuard",
    "mod_compat.voxy.MixinVoxyRenderSystem",
}
for key in ("mixins", "client"):
    data[key] = [x for x in data.get(key, []) if x not in remove_any]
mix.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 2) Minecraft 26.x ChunkPos is a record and renamed its packed helpers.
#    Apply only to the concrete Java files reported by the compiler.
# ---------------------------------------------------------------------------
chunk_files = [
    "common/src/main/java/org/valkyrienskies/mod/mixin/world/level/levelgen/MixinChunkStatus.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/world/chunk/MixinLevelChunk.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/feature/mob_spawning/NaturalSpawnerMixin.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/feature/tick_ship_chunks/MixinChunkMap.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinGenerationChunkHolder.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinChunkHolder.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinChunkMapShipyard.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinServerLevel.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinChunkMap.java",
]
for rel in chunk_files:
    p = ROOT / rel
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    old = s
    s = s.replace("ChunkPos.asLong(", "ChunkPos.pack(")
    s = re.sub(r"\.toLong\(\)", ".pack()", s)
    s = re.sub(r"new ChunkPos\(([^;\n()]*)\)", r"ChunkPos.containing(\1)", s)
    # Revert packed-long constructions accidentally matching the generic rule;
    # known old long ctor forms use unpack(), not containing().
    s = re.sub(r"ChunkPos\.containing\(([^)]*(?:packed|chunkPosLong|posLong|long)[^)]*)\)", r"ChunkPos.unpack(\1)", s, flags=re.I)
    # Record component access. Restrict to common local names to avoid touching
    # unrelated vector/entity fields.
    for name in ("chunkPos", "pos", "chunk", "shipChunkPos", "centerChunk"):
        s = s.replace(f"{name}.x", f"{name}.x()")
        s = s.replace(f"{name}.z", f"{name}.z()")
        # Avoid double conversion when an upstream line was already modern.
        s = s.replace(f"{name}.x()()", f"{name}.x()")
        s = s.replace(f"{name}.z()()", f"{name}.z()")
    if s != old:
        p.write_text(s, encoding="utf-8")

# Explicitly cover this.chunkPos record access (not handled by simple name loop).
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/world/chunk/MixinLevelChunk.java"
s = p.read_text(encoding="utf-8")
s = s.replace("this.chunkPos.x", "this.chunkPos.x()").replace("this.chunkPos.z", "this.chunkPos.z()")
s = s.replace("this.chunkPos.x()()", "this.chunkPos.x()").replace("this.chunkPos.z()()", "this.chunkPos.z()")

# ChunkAccess.blendingData became final in 26.2. Shadow it as @Mutable so the
# existing cross-dimension deep-copy path can preserve blending metadata instead
# of silently dropping data.
if "this.blendingData = loadedChunk.getBlendingData();" in s:
    if "import net.minecraft.world.level.levelgen.blending.BlendingData;" not in s:
        s = s.replace("import net.minecraft.world.level.levelgen.Heightmap;\n", "import net.minecraft.world.level.levelgen.Heightmap;\nimport net.minecraft.world.level.levelgen.blending.BlendingData;\n")
    if "import org.spongepowered.asm.mixin.Mutable;" not in s:
        s = s.replace("import org.spongepowered.asm.mixin.Mixin;\n", "import org.spongepowered.asm.mixin.Mixin;\nimport org.spongepowered.asm.mixin.Mutable;\n")
    marker = "    @Shadow\n    @Final\n    Level level;\n"
    if marker not in s:
        raise SystemExit("MixinLevelChunk shadow insertion anchor missing")
    shadow = marker + "\n    @Shadow\n    @Final\n    @Mutable\n    protected BlendingData blendingData;\n"
    s = s.replace(marker, shadow, 1)
p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------------------
# 3) BlockPos center: avoid relying on the removed/unstable convenience method
#    in Java call sites; construct the exact block center explicitly.
# ---------------------------------------------------------------------------
for rel in [
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinServerLevel.java",
    "common/src/main/java/org/valkyrienskies/mod/mixin/client/MixinWeatherEffectRenderer.java",
]:
    p = ROOT / rel
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    old = s
    # Typical variable names seen in the port errors.
    for v in ("pos", "blockPos"):
        s = s.replace(f"{v}.getCenter()", f"new net.minecraft.world.phys.Vec3({v}.getX() + 0.5D, {v}.getY() + 0.5D, {v}.getZ() + 0.5D)")
    if s != old:
        p.write_text(s, encoding="utf-8")

# POI manager: BlockPos -> ChunkPos factory.
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinPOIManager.java"
if p.exists():
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"new ChunkPos\(([^)]+)\)", r"ChunkPos.containing(\1)", s)
    p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------------------
# 4) SavedDataType switched its key from String to Identifier in 26.x.
#    withDefaultNamespace preserves the old path name (minecraft:<old-id>), so
#    existing world's data/<old-id>.dat naming remains stable.
# ---------------------------------------------------------------------------
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/server/MixinMinecraftServer.java"
s = p.read_text(encoding="utf-8")
if "import net.minecraft.resources.Identifier;" not in s:
    # Insert beside other net.minecraft imports, before server import if present.
    anchor = "import net.minecraft.server.MinecraftServer;\n"
    if anchor not in s:
        raise SystemExit("MixinMinecraftServer Identifier import anchor missing")
    s = s.replace(anchor, "import net.minecraft.resources.Identifier;\n" + anchor, 1)
s = s.replace("            ShipSavedData.SAVED_DATA_ID,\n", "            Identifier.withDefaultNamespace(ShipSavedData.SAVED_DATA_ID),\n", 1)
p.write_text(s, encoding="utf-8")

print("Ported remaining core ChunkPos/SavedData APIs and isolated optional 1.21 render/Voxy seams")
