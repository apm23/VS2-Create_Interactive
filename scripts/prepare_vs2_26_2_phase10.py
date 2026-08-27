#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# CreativeModeTab.Output became protected in 26.2. Keep the VS tab itself
# registered, but leave its dev/test-only item population empty for the core
# port. None of these entries are required for train/player physics.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/ValkyrienSkiesMod.kt"
t = p.read_text(encoding="utf-8")
old = '''            .displayItems { _, output ->
                if (::TEST_CHAIR.isInitialized) output.accept(TEST_CHAIR)
                if (::TEST_HINGE.isInitialized) output.accept(TEST_HINGE)
                if (::TEST_FLAP.isInitialized) output.accept(TEST_FLAP)
                if (::TEST_WING.isInitialized) output.accept(TEST_WING)
                if (::TEST_THRUSTER.isInitialized) output.accept(TEST_THRUSTER)
                if (::TEST_ANTIGRAV.isInitialized) output.accept(TEST_ANTIGRAV)
                if (::CONNECTION_CHECKER_ITEM.isInitialized) output.accept(CONNECTION_CHECKER_ITEM)
                // Dev-only ship debug items hidden from the creative tab. Still registered so
                // existing item stacks in chests / inventories load fine and /give works.
                // if (::SHIP_CREATOR_ITEM.isInitialized) output.accept(SHIP_CREATOR_ITEM)
                // if (::SHIP_ASSEMBLER_ITEM.isInitialized) output.accept(SHIP_ASSEMBLER_ITEM)
                // if (::SHIP_CREATOR_ITEM_SMALLER.isInitialized) output.accept(SHIP_CREATOR_ITEM_SMALLER)
                if (::AREA_ASSEMBLER_ITEM.isInitialized) output.accept(AREA_ASSEMBLER_ITEM)
                if (::PHYSICS_ENTITY_CREATOR_ITEM.isInitialized) output.accept(PHYSICS_ENTITY_CREATOR_ITEM)
            }
'''
if old not in t:
    raise SystemExit("Expected VS creative-tab item population block not found")
t = t.replace(old, '            .displayItems { _, _ -> }\n', 1)
p.write_text(t, encoding="utf-8")

# Kotlin nullability now mirrors 26.2's non-null Block/BlockEntity generic
# signatures more strictly.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/block/TestHingeBlock.kt"
t = p.read_text(encoding="utf-8")
old_shape = '''    override fun getShape(
        state: BlockState, level: BlockGetter?, pos: BlockPos?, context: CollisionContext?
    ): VoxelShape'''
new_shape = '''    override fun getShape(
        state: BlockState, level: BlockGetter, pos: BlockPos, context: CollisionContext
    ): VoxelShape'''
if old_shape not in t:
    raise SystemExit("Expected nullable TestHingeBlock#getShape signature not found")
t = t.replace(old_shape, new_shape, 1)
old_ticker = "    override fun <T : BlockEntity?> getTicker("
if old_ticker not in t:
    raise SystemExit("Expected nullable TestHingeBlock#getTicker generic not found")
t = t.replace(old_ticker, "    override fun <T : BlockEntity> getTicker(", 1)
p.write_text(t, encoding="utf-8")

# SynchedEntityData serializers/accessors are non-null generic values in 26.2.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/util/EntityData.kt"
t = p.read_text(encoding="utf-8")
if "inline fun <reified T : Entity, R> defineSynced" not in t or "class EntityDataDelegate<T>(" not in t:
    raise SystemExit("Expected legacy EntityData generic declarations not found")
t = t.replace("inline fun <reified T : Entity, R> defineSynced", "inline fun <reified T : Entity, R : Any> defineSynced", 1)
t = t.replace("class EntityDataDelegate<T>(", "class EntityDataDelegate<T : Any>(", 1)
p.write_text(t, encoding="utf-8")

# RandomizableContainerBlockEntity#setLootTable(ResourceKey,long) was split in
# 26.2. Preserve the old behavior: clear the loot table and reset its seed.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/util/RelocationUtil.kt"
t = p.read_text(encoding="utf-8")
old_loot = "            it.setLootTable(null, 0)"
new_loot = "            it.setLootTable(null)\n            it.setLootTableSeed(0L)"
if old_loot not in t:
    raise SystemExit("Expected legacy setLootTable(null, 0) call not found")
t = t.replace(old_loot, new_loot, 1)
p.write_text(t, encoding="utf-8")

print("Ported creative-tab, block signatures, entity-data generics, and loot-table API to 26.2")
