#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/world/chunk/MixinLevelChunk.java"
s = p.read_text(encoding="utf-8")

# MC 26.2 still exposes ChunkAccess.getBlendingData(), but direct protected-field
# transplantation from this LevelChunk mixin is no longer a valid mixin shadow
# contract: Mixin tries to bind blendingData against LevelChunk itself and aborts.
# Shipyard chunks are not terrain-generation seam chunks, so blending metadata is
# irrelevant to cross-dimension ship block transfer. Keep the deep-copy of sections,
# block entities, heightmaps and lighting, but do not transplant terrain blending data.
old = "        this.blendingData = loadedChunk.getBlendingData();\n"
if old not in s:
    raise SystemExit("Expected blendingData transplant line not found")
s = s.replace(old, "        // MC 26.2: intentionally do not transplant terrain blending metadata into shipyard chunks.\n", 1)

p.write_text(s, encoding="utf-8")
print("Removed invalid LevelChunk blendingData field access for MC 26.2 shipyard chunks")
