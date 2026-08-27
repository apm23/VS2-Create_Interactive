#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/world/chunk/MixinLevelChunk.java"
s = p.read_text(encoding="utf-8")

# Phase 29 removed the only remaining *use* of blendingData, but an earlier port
# phase had also injected an explicit @Shadow/@Final/@Mutable field for it. MC 26.2
# no longer exposes a bindable LevelChunk target field under that contract, so the
# mixin aborts at runtime before server bootstrap. Remove the obsolete shadow and
# its now-unused imports entirely; cross-dimension ship chunk copying no longer
# depends on terrain blending metadata.
shadow = '''    @Shadow\n    @Final\n    @Mutable\n    protected BlendingData blendingData;\n\n'''
if shadow not in s:
    raise SystemExit("Expected obsolete blendingData shadow block not found")
s = s.replace(shadow, "", 1)
s = s.replace("import net.minecraft.world.level.levelgen.blending.BlendingData;\n", "", 1)
s = s.replace("import org.spongepowered.asm.mixin.Mutable;\n", "", 1)

# Guard against silently reintroducing the runtime-fatal field.
if "blendingData" in s:
    raise SystemExit("blendingData still present after phase30 cleanup")

p.write_text(s, encoding="utf-8")
print("Removed obsolete MC 26.2 LevelChunk blendingData mixin shadow")
