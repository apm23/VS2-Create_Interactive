#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #77 proved CarriageContraptionEntity.setBlock rejects ClientLevel
# specifically because Create casts its level to ServerLevel. Exercise the exact same
# same-cell/same-entry canary on the already-resolved integrated-server carriage.
# This remains production-smoke-fixture-only: no empty-cell write, removal, inventory
# consumption, world placement, or physics/train mutation is introduced.
anchor = '''                        System.setProperty("vs2.productionServerFixtureReady", "true")
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)'''
probe = '''                        System.setProperty("vs2.productionServerFixtureReady", "true")
                        if (!java.lang.Boolean.getBoolean("vs2.productionServerNoopSetBlockProbed")) {
                            val canaryGetContraption = syncCarriage.javaClass.methods.firstOrNull { method ->
                                method.name == "getContraption" && method.parameterCount == 0
                            }
                            val canaryContraption = canaryGetContraption?.invoke(syncCarriage)
                            val canaryGetBlocks = canaryContraption?.javaClass?.methods?.firstOrNull { method ->
                                method.name == "getBlocks" && method.parameterCount == 0
                            }
                            val canaryBlocks = canaryGetBlocks?.invoke(canaryContraption) as? java.util.Map<*, *>
                            var canaryPos: net.minecraft.core.BlockPos? = null
                            var canaryEntry: Any? = null
                            var canaryDistance = Double.POSITIVE_INFINITY
                            if (canaryBlocks != null) {
                                for (entry in canaryBlocks.entries) {
                                    val pos = entry.key as? net.minecraft.core.BlockPos ?: continue
                                    val value = entry.value ?: continue
                                    val dx = pos.x + 0.5 - syncLocalX
                                    val dy = pos.y + 1.0 - syncLocalY
                                    val dz = pos.z + 0.5 - syncLocalZ
                                    val distance = dx * dx + dy * dy + dz * dz
                                    if (distance < canaryDistance) {
                                        canaryDistance = distance
                                        canaryPos = pos
                                        canaryEntry = value
                                    }
                                }
                            }
                            val canarySetBlock = if (canaryEntry != null) syncCarriage.javaClass.methods.firstOrNull { method ->
                                method.name == "setBlock" && method.parameterCount == 2
                                    && method.parameterTypes[0] == net.minecraft.core.BlockPos::class.java
                                    && method.parameterTypes[1].isAssignableFrom(canaryEntry!!.javaClass)
                            } else null
                            val beforeSize = canaryBlocks?.size ?: -1
                            val beforeEntry = if (canaryBlocks != null && canaryPos != null) canaryBlocks[canaryPos] else null
                            var beforeState: Any? = null
                            if (canaryEntry != null) {
                                beforeState = canaryEntry!!.javaClass.methods.firstOrNull { method ->
                                    method.name == "state" && method.parameterCount == 0
                                }?.invoke(canaryEntry)
                            }
                            var invoked = false
                            var sizeStable = false
                            var stateStable = false
                            var errorType = "none"
                            var rootType = "none"
                            var rootMessage = "none"
                            try {
                                if (canarySetBlock != null && canaryPos != null && canaryEntry != null) {
                                    canarySetBlock.invoke(syncCarriage, canaryPos!!.immutable(), canaryEntry)
                                    invoked = true
                                    val afterEntry = canaryBlocks?.get(canaryPos)
                                    val afterState = afterEntry?.javaClass?.methods?.firstOrNull { method ->
                                        method.name == "state" && method.parameterCount == 0
                                    }?.invoke(afterEntry)
                                    sizeStable = canaryBlocks != null && canaryBlocks.size == beforeSize
                                    stateStable = java.util.Objects.equals(beforeState, afterState)
                                }
                            } catch (canaryException: ReflectiveOperationException) {
                                errorType = canaryException.javaClass.simpleName
                                var root: Throwable = canaryException
                                val seen = java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Throwable, Boolean>())
                                while (root.cause != null && seen.add(root)) root = root.cause!!
                                rootType = root.javaClass.name
                                rootMessage = String.valueOf(root.message).replace('\\n', ' ').replace('\\r', ' ')
                            } catch (canaryException: RuntimeException) {
                                errorType = canaryException.javaClass.simpleName
                                var root: Throwable = canaryException
                                val seen = java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Throwable, Boolean>())
                                while (root.cause != null && seen.add(root)) root = root.cause!!
                                rootType = root.javaClass.name
                                rootMessage = String.valueOf(root.message).replace('\\n', ' ').replace('\\r', ' ')
                            }
                            val safe = invoked && sizeStable && stateStable
                            System.setProperty("vs2.productionServerNoopSetBlockProbed", "true")
                            logger.info("GATE_D_CONTRAPTION_SETBLOCK_NOOP_SERVER carriage_id={} local_cell={} method_found={} invoked={} before_size={} after_size={} size_stable={} state_stable={} same_entry_identity={} safe={} error={} root_type={} root_message={} fixture_only=true",
                                syncCarriageId, canaryPos, canarySetBlock != null, invoked, beforeSize, canaryBlocks?.size ?: -1,
                                sizeStable, stateStable, beforeEntry === canaryBlocks?.get(canaryPos), safe,
                                errorType, rootType, rootMessage)
                        }
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)'''

if "GATE_D_CONTRAPTION_SETBLOCK_NOOP_SERVER" not in server:
    if anchor not in server:
        raise SystemExit("Phase 106 could not find Phase 104 exact-carriage server fixture anchor")
    server = server.replace(anchor, probe, 1)

required = [
    'GATE_D_CONTRAPTION_SETBLOCK_NOOP_SERVER',
    'method.name == "setBlock"',
    'canarySetBlock.invoke(syncCarriage, canaryPos!!.immutable(), canaryEntry)',
    'vs2.productionServerNoopSetBlockProbed',
    'val safe = invoked && sizeStable && stateStable',
    'fixture_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 106 lost server no-op setBlock anchors: " + ", ".join(missing))

for forbidden in [
    'firstEmptyAdjacent', '.remove(', '.clear(', 'Blocks.STONE', 'Blocks.AIR',
    'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 106 found forbidden placement/mutation expansion: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
print("Phase 106: exercised Create setBlock as a same-cell/same-entry canary on the exact ServerLevel carriage; no empty-cell placement, inventory, world, train, or physics mutation")
