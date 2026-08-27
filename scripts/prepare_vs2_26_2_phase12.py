#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# ScheduledTick<T> is non-null in 26.2; blocks are never nullable here.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/assembly/AssemblyUtil.kt"
t = p.read_text(encoding="utf-8")
old = "ScheduledTick<Block?>(state.block, to, 0, 0)"
if old not in t:
    raise SystemExit("Expected nullable ScheduledTick<Block?> call not found")
t = t.replace(old, "ScheduledTick<Block>(state.block, to, 0, 0)", 1)
p.write_text(t, encoding="utf-8")

# StructureProcessor became an interface in 26.2 and its serialization hook is
# now codec(): MapCodec. ICopyableProcessor is instantiated programmatically,
# never via datapacks, so a harmless unit codec is sufficient for the required
# interface contract while preserving the runtime copy callback/state.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/assembly/ShipAssembler.kt"
t = p.read_text(encoding="utf-8")
if "import com.mojang.serialization.MapCodec\n" not in t:
    t = t.replace("package org.valkyrienskies.mod.common.assembly\n\n", "package org.valkyrienskies.mod.common.assembly\n\nimport com.mojang.serialization.MapCodec\n", 1)
t = t.replace("import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorType\n", "")
old_decl = "    ): StructureProcessor() {"
if old_decl not in t:
    raise SystemExit("Expected legacy StructureProcessor superclass declaration not found")
t = t.replace(old_decl, "    ): StructureProcessor {", 1)
old_type = '''        // getType is used for referencing this processor from a datapack, which we don't need
        override fun getType(): StructureProcessorType<*>? = null
'''
new_type = '''        // This processor is created only in code; datapack deserialization is not used.
        override fun codec(): MapCodec<out StructureProcessor> =
            MapCodec.unit { ICopyableProcessor(emptyMap(), emptyMap()) }
'''
if old_type not in t:
    raise SystemExit("Expected legacy StructureProcessor#getType override not found")
t = t.replace(old_type, new_type, 1)
p.write_text(t, encoding="utf-8")

print("Ported ScheduledTick and StructureProcessor assembly APIs to Minecraft 26.2")
