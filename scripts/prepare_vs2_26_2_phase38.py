#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# Minecraft 26.2 changed ChunkMap.dropChunk to static. Update both the Mixin
# invoker declaration and the Kotlin call-site so compile-time and runtime agree.
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/accessors/server/level/ChunkMapAccessor.java"
s = p.read_text(encoding="utf-8")
old = '''    @Invoker("dropChunk")\n    void callDropChunk(ServerPlayer serverPlayer, ChunkPos chunkPos);\n'''
new = '''    @Invoker("dropChunk")\n    static void callDropChunk(ServerPlayer serverPlayer, ChunkPos chunkPos) {\n        throw new AssertionError();\n    }\n'''
if old not in s:
    raise SystemExit("Expected non-static dropChunk invoker not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/world/ChunkManagement.kt"
s = p.read_text(encoding="utf-8")
old = '''                    (server.getLevelFromDimensionId(chunkUnwatchTask.dimensionId)!!.chunkSource.chunkMap as ChunkMapAccessor)\n                        .callDropChunk(serverPlayer, chunkPos)\n'''
new = '''                    ChunkMapAccessor.callDropChunk(serverPlayer, chunkPos)\n'''
if old not in s:
    raise SystemExit("Expected instance callDropChunk call-site not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("Retargeted ChunkMapAccessor.callDropChunk and its Kotlin call-site to MC 26.2 static target")
