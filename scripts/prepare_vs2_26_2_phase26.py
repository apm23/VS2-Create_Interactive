#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/entity/MixinEntity.java"
s = p.read_text(encoding="utf-8")

# MC 26.2 no longer exposes Entity.fluidHeight under the old field contract.
# Keeping the obsolete shadow prevents the entire core entity mixin from applying.
shadow_pattern = re.compile(
    r"\n\s*@Shadow\s*\n\s*@Final\s*\n\s*private\s+Object2DoubleMap<TagKey<Fluid>>\s+fluidHeight\s*;\s*\n",
    re.MULTILINE,
)
s, count = shadow_pattern.subn("\n", s, count=1)
if count != 1:
    raise SystemExit("Expected obsolete fluidHeight @Shadow not found")

# Preserve direct ship-water body detection without writing to the removed vanilla map.
old = '''            // fluidHeight drives jumpInLiquid (swim-up on jump) and floatInWaterWhileRidden:
            // both require height > jump threshold (0.4 default). Mirror the height vanilla
            // would have stored if the water lived at the player's world AABB.
            this.fluidHeight.put(FluidTags.WATER, maxHeightAboveMinY[0]);'''
new = '''            // MC 26.2 removed the old Entity.fluidHeight map. Marking body contact here
            // still preserves the critical ship-water touch state; height-specific behavior
            // is left to the 26.2 fluid implementation instead of targeting a stale field.'''
if old not in s:
    raise SystemExit("Expected fluidHeight write block not found")
s = s.replace(old, new, 1)

# This import existed only for the removed shadow.
s = s.replace("import it.unimi.dsi.fastutil.objects.Object2DoubleMap;\n", "")

p.write_text(s, encoding="utf-8")
print("Adapted core Entity mixin to MC 26.2 fluidHeight removal")
