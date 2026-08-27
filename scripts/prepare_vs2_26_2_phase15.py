#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# Mounted-camera perspective changes no longer expose the old LevelRenderer
# invalidation methods through the 26.2 compile API. The camera transform itself
# remains authoritative; remove these two legacy forced chunk rebuilds rather
# than binding to an internal renderer method.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/client/ShipMountPerspective.kt"
t = p.read_text(encoding="utf-8")
if t.count("mc.levelRenderer.allChanged()") != 2:
    raise SystemExit("Expected two legacy renderer invalidation calls")
t = t.replace("        mc.levelRenderer.allChanged()\n", "", 2)
p.write_text(t, encoding="utf-8")

# transformPosition(Vec3) already returns Minecraft Vec3 in the active 26.2
# API, so the JOML conversion extension is invalid here.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/CompatUtil.kt"
t = p.read_text(encoding="utf-8")
old = "ship.shipToWorld.transformPosition(Vec3.atCenterOf(pos)).toMinecraft()"
if old not in t:
    raise SystemExit("Expected compound-brightness transform expression not found")
t = t.replace(old, "ship.shipToWorld.transformPosition(Vec3.atCenterOf(pos))", 1)
p.write_text(t, encoding="utf-8")

# Actual 26.2 compiler contract for StructureProcessor uses three BlockPos
# parameters followed by the processed block info. Preserve ICopyableBlock's
# onPaste callback at the final processed world position.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/assembly/ShipAssembler.kt"
t = p.read_text(encoding="utf-8")
old = '''        override fun processBlock(
            levelReader: LevelReader, oldBPos: BlockPos, newBPos: BlockPos,
            oldStructureBlockInfo: StructureTemplate.StructureBlockInfo,
            newStructureBlockInfo: StructureTemplate.StructureBlockInfo, structurePlaceSettings: StructurePlaceSettings
        ): StructureTemplate.StructureBlockInfo? {
            val block = newStructureBlockInfo.state.block
            if (block !is ICopyableBlock) return newStructureBlockInfo
            block.onPaste((levelReader as ServerLevelAccessor).level, newBPos, newStructureBlockInfo.state, oldShipIdToNewShipId, centerPositions, newStructureBlockInfo.nbt)
            return newStructureBlockInfo
        }
'''
new = '''        override fun processBlock(
            levelReader: LevelReader, targetPosition: BlockPos, referencePos: BlockPos,
            templateRelativePos: BlockPos,
            processedBlockInfo: StructureTemplate.StructureBlockInfo, structurePlaceSettings: StructurePlaceSettings
        ): StructureTemplate.StructureBlockInfo? {
            val block = processedBlockInfo.state.block
            if (block !is ICopyableBlock) return processedBlockInfo
            block.onPaste(
                (levelReader as ServerLevelAccessor).level, processedBlockInfo.pos, processedBlockInfo.state,
                oldShipIdToNewShipId, centerPositions, processedBlockInfo.nbt
            )
            return processedBlockInfo
        }
'''
if old not in t:
    raise SystemExit("Expected post-phase12 ICopyableProcessor processBlock body not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

# ServerPlayer.connection is nullable in the 26.2 Kotlin surface.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/entity/ShipMountingEntity.kt"
t = p.read_text(encoding="utf-8")
old = "?.connection.send(ClientboundSystemChatPacket(SEATED_PROMPT, true))"
if t.count(old) != 2:
    raise SystemExit("Expected two nullable seat overlay packet sends")
t = t.replace(old, "?.connection?.send(ClientboundSystemChatPacket(SEATED_PROMPT, true))", 2)
p.write_text(t, encoding="utf-8")

# MultiBufferSource is no longer exposed to this common compile surface in 26.2,
# and these handlers never consume the buffer argument. Remove the obsolete seam
# parameter; call sites will be migrated by the compiler-guided next pass.
for rel in [
    "common/src/main/kotlin/org/valkyrienskies/mod/common/entity/handling/VSEntityHandler.kt",
    "common/src/main/kotlin/org/valkyrienskies/mod/common/entity/handling/AbstractShipyardEntityHandler.kt",
    "common/src/main/kotlin/org/valkyrienskies/mod/common/entity/handling/WorldEntityHandler.kt",
]:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t = t.replace("import net.minecraft.client.renderer.MultiBufferSource\n", "")
    if "buffer: MultiBufferSource, packedLight: Int" not in t:
        raise SystemExit(f"Expected MultiBufferSource render seam in {rel}")
    t = t.replace("buffer: MultiBufferSource, packedLight: Int", "packedLight: Int")
    p.write_text(t, encoding="utf-8")

print("Resolved renderer invalidation, Vec3 transform, processor signature, seat connection, and render buffer seam")
