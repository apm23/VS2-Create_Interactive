#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/entity/MixinEntity.java"
s = p.read_text(encoding="utf-8")

# MC 26.2 removed the old Entity.fluidHeight storage contract. The upstream
# declaration is @Shadow + protected (not @Final/private), so remove it by its
# exact field declaration and the immediately preceding @Shadow annotation.
lines = s.splitlines(keepends=True)
field_index = next(
    (i for i, line in enumerate(lines)
     if "Object2DoubleMap<TagKey<Fluid>> fluidHeight" in line),
    None,
)
if field_index is None:
    raise SystemExit("Expected obsolete fluidHeight field not found")
start = field_index
while start > 0 and lines[start - 1].strip() in {"@Shadow", "@Final"}:
    start -= 1
del lines[start:field_index + 1]
s = "".join(lines)

# Preserve direct ship-water body detection but stop writing to the removed map.
write = "            this.fluidHeight.put(FluidTags.WATER, maxHeightAboveMinY[0]);\n"
if write not in s:
    raise SystemExit("Expected fluidHeight write not found")
s = s.replace(
    write,
    "            // MC 26.2: body-water contact is retained via wasTouchingWater;\n"
    "            // no stale vanilla fluid-height map is written here.\n",
    1,
)

# Object2DoubleMap was only used by the removed shadow.
s = s.replace("import it.unimi.dsi.fastutil.objects.Object2DoubleMap;\n", "")

p.write_text(s, encoding="utf-8")
print("Adapted core Entity mixin to MC 26.2 fluidHeight removal")
