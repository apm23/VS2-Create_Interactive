#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/accessors/server/level/ChunkMapAccessor.java"
s = p.read_text(encoding="utf-8")

old = '''    @Invoker("dropChunk")\n    void callDropChunk(ServerPlayer serverPlayer, ChunkPos chunkPos);\n'''
new = '''    @Invoker("dropChunk")\n    static void callDropChunk(ServerPlayer serverPlayer, ChunkPos chunkPos) {\n        throw new AssertionError();\n    }\n'''
if old not in s:
    raise SystemExit("Expected non-static dropChunk invoker not found")
if "static void callDropChunk" in s:
    raise SystemExit("dropChunk invoker already static before Phase 38")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Retargeted ChunkMapAccessor.callDropChunk to MC 26.2 static target")
