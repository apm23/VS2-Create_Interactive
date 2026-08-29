#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #91 proved the client-native occupied/empty target pair resolves
# unchanged on the authoritative ServerLevel carriage. Before any empty-cell write,
# construct the exact StructureBlockInfo value that Create would receive for that
# empty local cell and validate its position/state/NBT fields. Construction only:
# no contraption map, world, inventory, player, train, collider, or physics mutation.
anchor = '''                            logger.info("GATE_D_NATIVE_PLACEMENT_TARGET_SERVER_READONLY carriage_id={} fixture_carriage_id={} entity_resolved={} hit_local={} empty_local={} hit_present={} empty_present={} block_count={} authoritative_ready={} read_only=true",
                                nativeCarriageId, syncCarriageId, nativeCarriage != null, hitPos, emptyPos,
                                hitPresent, emptyPresent, nativeBlocks?.size ?: -1, authoritativeReady)'''
probe = anchor + '''
                            if (authoritativeReady) {
                                val sourceEntry = if (nativeBlocks != null && hitPos != null) nativeBlocks[hitPos] else null
                                val sourceState = sourceEntry?.javaClass?.methods?.firstOrNull { method ->
                                    method.name == "state" && method.parameterCount == 0
                                }?.invoke(sourceEntry)
                                val sourceNbt = sourceEntry?.javaClass?.methods?.firstOrNull { method ->
                                    method.name == "nbt" && method.parameterCount == 0
                                }?.invoke(sourceEntry)
                                val entryConstructor = sourceEntry?.javaClass?.constructors?.firstOrNull { constructor ->
                                    val params = constructor.parameterTypes
                                    params.size == 3
                                        && params[0] == net.minecraft.core.BlockPos::class.java
                                        && params[1].isInstance(sourceState)
                                        && (sourceNbt == null || params[2].isInstance(sourceNbt))
                                }
                                var candidate: Any? = null
                                var errorType = "none"
                                try {
                                    if (entryConstructor != null && emptyPos != null && sourceState != null) {
                                        candidate = entryConstructor.newInstance(emptyPos.immutable(), sourceState, sourceNbt)
                                    }
                                } catch (candidateException: ReflectiveOperationException) {
                                    errorType = candidateException.javaClass.name
                                } catch (candidateException: RuntimeException) {
                                    errorType = candidateException.javaClass.name
                                }
                                val candidatePos = candidate?.javaClass?.methods?.firstOrNull { method ->
                                    method.name == "pos" && method.parameterCount == 0
                                }?.invoke(candidate)
                                val candidateState = candidate?.javaClass?.methods?.firstOrNull { method ->
                                    method.name == "state" && method.parameterCount == 0
                                }?.invoke(candidate)
                                val candidateNbt = candidate?.javaClass?.methods?.firstOrNull { method ->
                                    method.name == "nbt" && method.parameterCount == 0
                                }?.invoke(candidate)
                                val candidateReady = candidate != null
                                    && java.util.Objects.equals(candidatePos, emptyPos)
                                    && java.util.Objects.equals(candidateState, sourceState)
                                    && java.util.Objects.equals(candidateNbt, sourceNbt)
                                System.setProperty("vs2.productionNativePlacementCandidateProbed", "true")
                                logger.info("GATE_D_NATIVE_PLACEMENT_CANDIDATE_SERVER carriage_id={} hit_local={} empty_local={} constructor_found={} source_state={} source_nbt={} candidate_class={} candidate_pos={} candidate_ready={} error={} read_only=true",
                                    nativeCarriageId, hitPos, emptyPos, entryConstructor != null, sourceState,
                                    sourceNbt != null, candidate?.javaClass?.name ?: "null", candidatePos,
                                    candidateReady, errorType)
                            }'''

if "GATE_D_NATIVE_PLACEMENT_CANDIDATE_SERVER" not in server:
    if anchor not in server:
        raise SystemExit("Phase 110 could not find Phase 109 authoritative target log anchor")
    server = server.replace(anchor, probe, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_CANDIDATE_SERVER',
    'entryConstructor.newInstance(emptyPos.immutable(), sourceState, sourceNbt)',
    'method.name == "pos"',
    'method.name == "state"',
    'method.name == "nbt"',
    'candidateReady = candidate != null',
    'vs2.productionNativePlacementCandidateProbed',
    'read_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 110 lost server placement-candidate anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'invalidateColliders(',
    'setPos(', 'setDeltaMovement(', 'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 110 found forbidden mutation/dispatch: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
print("Phase 110: constructed and field-validated the authoritative empty-cell StructureBlockInfo candidate read-only; no contraption, world, inventory, player, train, or physics mutation")
