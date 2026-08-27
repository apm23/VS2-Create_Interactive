#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/CompatUtil.kt"
t = p.read_text(encoding="utf-8")

if "import net.minecraft.world.phys.shapes.CollisionContext" not in t:
    t = t.replace(
        "import net.minecraft.world.phys.Vec3\n",
        "import net.minecraft.world.phys.Vec3\nimport net.minecraft.world.phys.shapes.CollisionContext\n",
        1,
    )

# BlockPos.center -> BlockPos.getCenter() in 26.2.
t = t.replace(".center", ".getCenter()")

# The transformed JOML vector must be converted back to Minecraft Vec3 before
# BlockPos.containing(Position) can consume it.
old = "BlockPos.containing(ship.shipToWorld.transformPosition(pos.getCenter()))"
new = "BlockPos.containing(ship.shipToWorld.transformPosition(pos.getCenter()).toMinecraft())"
if old not in t:
    raise SystemExit("Expected transformed BlockPos center expression not found")
t = t.replace(old, new)

# 26.2's Entity overload is non-null; use the CollisionContext overload for
# entity-independent raycasts instead of forcing a nullable Entity.
old_null = "null as net.minecraft.world.entity.Entity?"
if t.count(old_null) < 2:
    raise SystemExit("Expected nullable ClipContext entity placeholders not found")
t = t.replace(old_null, "CollisionContext.empty()")

p.write_text(t, encoding="utf-8")
print("Ported BlockPos center access and entity-independent ClipContext construction to 26.2")
