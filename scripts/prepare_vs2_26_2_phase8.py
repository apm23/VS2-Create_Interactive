#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

def replace(path, old, new, minimum=1):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f"Expected at least {minimum} occurrence(s) of {old!r} in {path}, found {count}")
    p.write_text(text.replace(old, new), encoding="utf-8")
    return count

# Minecraft 26.2 renamed packed ChunkPos helpers:
#   ChunkPos.asLong(x,z) -> ChunkPos.pack(x,z)
#   chunkPos.toLong()    -> chunkPos.pack()
#   ChunkPos(long)       -> ChunkPos.unpack(long)
#   ChunkPos(BlockPos)   -> ChunkPos.containing(BlockPos)
replace("common/src/main/kotlin/org/valkyrienskies/mod/common/VSGameUtils.kt",
        "ChunkPos.asLong(chunkX, chunkZ)", "ChunkPos.pack(chunkX, chunkZ)")

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/assembly/SeamlessChunksManager.kt"
t = p.read_text(encoding="utf-8")
if "ChunkPos.asLong(chunkX, chunkZ)" not in t or ".toLong()" not in t:
    raise SystemExit("Expected legacy ChunkPos packing calls in SeamlessChunksManager")
t = t.replace("ChunkPos.asLong(chunkX, chunkZ)", "ChunkPos.pack(chunkX, chunkZ)")
t = t.replace(".toMinecraft().toLong()", ".toMinecraft().pack()")
t = t.replace("pos.toLong()", "pos.pack()")
p.write_text(t, encoding="utf-8")

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/world/ShipActivationManager.kt"
t = p.read_text(encoding="utf-8")
if "ChunkPos.asLong" not in t or "ChunkPos(packed)" not in t:
    raise SystemExit("Expected legacy ChunkPos APIs in ShipActivationManager")
t = t.replace("ChunkPos.asLong(", "ChunkPos.pack(")
t = t.replace("ChunkPos(packed)", "ChunkPos.unpack(packed)")
t = t.replace("ChunkPos(vIter.nextLong())", "ChunkPos.unpack(vIter.nextLong())")
p.write_text(t, encoding="utf-8")

replace("common/src/main/kotlin/org/valkyrienskies/mod/common/assembly/ShipAssembler.kt",
        "ChunkPos(blockPos)", "ChunkPos.containing(blockPos)")

print("Ported ChunkPos packing/unpacking/construction calls to Minecraft 26.2")
