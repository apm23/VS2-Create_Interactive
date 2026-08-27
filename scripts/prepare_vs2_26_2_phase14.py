#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

def edit(rel, replacements):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in t:
            raise SystemExit(f"Expected text not found in {rel}: {old}")
        t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")

# 26.2 Component.translatable varargs reject nullable arguments. A ship slug is
# optional by design, so fall back to the stable numeric ship id for messages.
edit("common/src/main/kotlin/org/valkyrienskies/mod/common/command/commands/DeleteCommand.kt", [
    ("Component.translatable(DELETED_ONE_SHIP_MESSAGE, r[0].slug)",
     "Component.translatable(DELETED_ONE_SHIP_MESSAGE, r[0].slug ?: r[0].id.toString())")
])
edit("common/src/main/kotlin/org/valkyrienskies/mod/common/command/commands/GetShipCommand.kt", [
    ("translatable(GET_SHIP_SUCCESS_MESSAGE, ship.slug, ship.id)",
     "translatable(GET_SHIP_SUCCESS_MESSAGE, ship.slug ?: ship.id.toString(), ship.id)")
])
edit("common/src/main/kotlin/org/valkyrienskies/mod/common/command/commands/RemassCommand.kt", [
    ("REMASSED_SHIP_FAIL_MESSAGE, ship.slug", "REMASSED_SHIP_FAIL_MESSAGE, ship.slug ?: ship.id.toString()")
])
edit("common/src/main/kotlin/org/valkyrienskies/mod/common/item/ShipAssemblerItem.kt", [
    ("shipData.slug)", "shipData.slug ?: shipData.id.toString())")
])
edit("common/src/main/kotlin/org/valkyrienskies/mod/common/item/ShipCreatorItem.kt", [
    ("serverShip.slug))", "serverShip.slug ?: serverShip.id.toString()))")
])
edit("common/src/main/kotlin/org/valkyrienskies/mod/common/item/ShipRemoverItem.kt", [
    ("ship.slug))", "ship.slug ?: ship.id.toString()))")
])

# Kotlin sees these 26.2 helpers as nullable. The miss direction has a natural
# UP fallback, and every selected entity hit normally sets a location; retain a
# position fallback only for defensive completeness.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/world/RaycastUtils.kt"
t = p.read_text(encoding="utf-8")
old_dir = "Direction.getNearest(line.x.toInt(), line.y.toInt(), line.z.toInt(), Direction.UP)"
if old_dir not in t:
    raise SystemExit("Expected Direction.getNearest raycast call not found")
t = t.replace(old_dir, f"({old_dir} ?: Direction.UP)", 1)
old_hit = "EntityHitResult(resultEntity, location)"
if old_hit not in t:
    raise SystemExit("Expected nullable EntityHitResult location call not found")
t = t.replace(old_hit, "EntityHitResult(resultEntity, location ?: resultEntity.position())", 1)
p.write_text(t, encoding="utf-8")

print("Ported nullable ship display names and raycast nullability to Minecraft 26.2")
