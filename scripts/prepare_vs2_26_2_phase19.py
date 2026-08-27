#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"

def replace_exact(rel, pairs):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    original = t
    for old, new in pairs:
        if old not in t:
            raise SystemExit(f"phase19 expected text missing in {rel}: {old}")
        t = t.replace(old, new)
    if t == original:
        raise SystemExit(f"phase19 made no changes to {rel}")
    p.write_text(t, encoding="utf-8")

# ChunkPos became a record in 26.x. Use explicit accessors, not broad regexes.
replace_exact(
    "common/src/main/java/org/valkyrienskies/mod/mixin/feature/mob_spawning/NaturalSpawnerMixin.java",
    [
        ("chunk.getPos().x, chunk.getPos().z", "chunk.getPos().x(), chunk.getPos().z()"),
    ],
)

replace_exact(
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinChunkMapShipyard.java",
    [
        ("center.x, center.z", "center.x(), center.z()"),
    ],
)

replace_exact(
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinServerLevel.java",
    [
        ("worldChunk.getPos().x", "worldChunk.getPos().x()"),
        ("worldChunk.getPos().z", "worldChunk.getPos().z()"),
        ("cp.x, cp.z", "cp.x(), cp.z()"),
        ("ChunkPos.containing(chunkX, chunkZ)", "new ChunkPos(chunkX, chunkZ)"),
    ],
)

replace_exact(
    "common/src/main/java/org/valkyrienskies/mod/mixin/feature/poi/MixinPOIManager.java",
    [
        ("new ChunkPos(blockPos)", "ChunkPos.containing(blockPos)"),
    ],
)

replace_exact(
    "common/src/main/java/org/valkyrienskies/mod/mixin/server/world/MixinChunkMap.java",
    [
        (
            "new ChunkPos(BlockPos.containing(VSGameUtilsKt.toWorldCoordinates(level, arg.getMiddleBlockPosition(63))))",
            "ChunkPos.containing(BlockPos.containing(VSGameUtilsKt.toWorldCoordinates(level, arg.getMiddleBlockPosition(63))))",
        ),
        (
            "new ChunkPos(BlockPos.containing(VSGameUtilsKt.toWorldCoordinates(level, d0.getMiddleBlockPosition(63))))",
            "ChunkPos.containing(BlockPos.containing(VSGameUtilsKt.toWorldCoordinates(level, d0.getMiddleBlockPosition(63))))",
        ),
    ],
)

# WeatherEffectRenderer is a pure client visual seam. Keep it out of the
# physics-core gate until the 26.2 client renderer restoration phase.
p = ROOT / "common/build.gradle"
t = p.read_text(encoding="utf-8")
anchor = '            exclude "org/valkyrienskies/mod/mixin/client/MixinWeatherEffectRenderer.java"\n'
extra = anchor + '            exclude "org/valkyrienskies/mod/mixin/feature/world_weather/MixinWeatherEffectRenderer.java"\n'
if anchor not in t:
    raise SystemExit("phase19 weather exclusion anchor missing")
if 'mixin/feature/world_weather/MixinWeatherEffectRenderer.java' not in t:
    t = t.replace(anchor, extra, 1)
p.write_text(t, encoding="utf-8")

mix = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
data = json.loads(mix.read_text(encoding="utf-8"))
entry = "feature.world_weather.MixinWeatherEffectRenderer"
if entry not in data.get("client", []):
    raise SystemExit("phase19 expected weather mixin entry missing")
data["client"] = [x for x in data["client"] if x != entry]
mix.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Fixed final known 26.2 core Java ChunkPos call sites and isolated weather renderer seam")
