#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #86 proved all prerequisites independently in the real train save:
# moving-train carry and native right-click readiness pass, the client publishes an
# exact occupied hit plus empty adjacent local cell, and Create's ServerLevel setBlock
# path accepts a same-cell/same-entry no-op safely. Before attempting any empty-cell
# mutation, resolve that exact client-native carriage and both cells on the integrated
# server and verify the authoritative contraption map agrees. This phase is read-only.
anchor = '''                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)'''
probe = '''                        if (java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")
                                && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementServerReadProbed")) {
                            val nativeCarriageId = System.getProperty("vs2.productionNativePlacementCarriageId")?.toIntOrNull()
                            val hitX = System.getProperty("vs2.productionNativePlacementHitX")?.toIntOrNull()
                            val hitY = System.getProperty("vs2.productionNativePlacementHitY")?.toIntOrNull()
                            val hitZ = System.getProperty("vs2.productionNativePlacementHitZ")?.toIntOrNull()
                            val emptyX = System.getProperty("vs2.productionNativePlacementEmptyX")?.toIntOrNull()
                            val emptyY = System.getProperty("vs2.productionNativePlacementEmptyY")?.toIntOrNull()
                            val emptyZ = System.getProperty("vs2.productionNativePlacementEmptyZ")?.toIntOrNull()
                            val nativeCarriage = if (nativeCarriageId != null && syncGetEntity != null) {
                                syncGetEntity.invoke(syncLevel, nativeCarriageId)
                            } else null
                            val nativeGetContraption = nativeCarriage?.javaClass?.methods?.firstOrNull { method ->
                                method.name == "getContraption" && method.parameterCount == 0
                            }
                            val nativeContraption = nativeGetContraption?.invoke(nativeCarriage)
                            val nativeGetBlocks = nativeContraption?.javaClass?.methods?.firstOrNull { method ->
                                method.name == "getBlocks" && method.parameterCount == 0
                            }
                            val nativeBlocks = nativeGetBlocks?.invoke(nativeContraption) as? Map<*, *>
                            val hitPos = if (hitX != null && hitY != null && hitZ != null) net.minecraft.core.BlockPos(hitX, hitY, hitZ) else null
                            val emptyPos = if (emptyX != null && emptyY != null && emptyZ != null) net.minecraft.core.BlockPos(emptyX, emptyY, emptyZ) else null
                            val hitPresent = nativeBlocks != null && hitPos != null && nativeBlocks.containsKey(hitPos)
                            val emptyPresent = nativeBlocks != null && emptyPos != null && nativeBlocks.containsKey(emptyPos)
                            val authoritativeReady = nativeCarriage != null && nativeBlocks != null && hitPresent && !emptyPresent
                            System.setProperty("vs2.productionNativePlacementServerReadProbed", "true")
                            logger.info("GATE_D_NATIVE_PLACEMENT_TARGET_SERVER_READONLY carriage_id={} fixture_carriage_id={} entity_resolved={} hit_local={} empty_local={} hit_present={} empty_present={} block_count={} authoritative_ready={} read_only=true",
                                nativeCarriageId, syncCarriageId, nativeCarriage != null, hitPos, emptyPos,
                                hitPresent, emptyPresent, nativeBlocks?.size ?: -1, authoritativeReady)
                        }
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)'''

if "GATE_D_NATIVE_PLACEMENT_TARGET_SERVER_READONLY" not in server:
    if anchor not in server:
        raise SystemExit("Phase 109 could not find post-Phase106 exact-carriage server fixture anchor")
    server = server.replace(anchor, probe, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_TARGET_SERVER_READONLY',
    'vs2.productionNativePlacementTargetReady',
    'vs2.productionNativePlacementServerReadProbed',
    'syncGetEntity.invoke(syncLevel, nativeCarriageId)',
    'nativeBlocks.containsKey(hitPos)',
    'nativeBlocks.containsKey(emptyPos)',
    'authoritativeReady = nativeCarriage != null && nativeBlocks != null && hitPresent && !emptyPresent',
    'read_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 109 lost authoritative server placement-target anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'Blocks.STONE', 'Blocks.AIR',
    'setPos(', 'setDeltaMovement(', 'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 109 found forbidden gameplay mutation/dispatch: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
print("Phase 109: resolved the exact Create-native occupied/empty placement cells on the authoritative ServerLevel carriage read-only; no block, inventory, player, train, or physics mutation")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase105.py")), run_name="__main__")
