#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #93 proved the exact client-native empty cell is authoritative on
# ServerLevel and that StructureBlockInfo construction is valid. Perform the first
# mutation only inside the disposable productionSmokeFixture world: place one inert
# vanilla STONE block with no NBT into that exact empty local cell through Create's
# public CarriageContraptionEntity.setBlock API, then verify map +1 and source stability.
anchor = '''                                logger.info("GATE_D_NATIVE_PLACEMENT_CANDIDATE_SERVER carriage_id={} hit_local={} empty_local={} constructor_found={} source_state={} source_nbt={} candidate_class={} candidate_pos={} candidate_ready={} error={} read_only=true",
                                    nativeCarriageId, hitPos, emptyPos, entryConstructor != null, sourceState,
                                    sourceNbt != null, candidate?.javaClass?.name ?: "null", candidatePos,
                                    candidateReady, errorType)'''
probe = anchor + '''
                                if (candidateReady
                                        && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")) {
                                    val stoneState = net.minecraft.world.level.block.Blocks.STONE.defaultBlockState()
                                    val placementCandidate = entryConstructor?.newInstance(emptyPos?.immutable(), stoneState, null)
                                    val setBlockMethod = nativeCarriage?.javaClass?.methods?.firstOrNull { method ->
                                        val params = method.parameterTypes
                                        method.name == "setBlock" && params.size == 2
                                            && params[0] == net.minecraft.core.BlockPos::class.java
                                            && placementCandidate != null && params[1].isInstance(placementCandidate)
                                    }
                                    val beforeSize = nativeBlocks?.size ?: -1
                                    val sourceBefore = if (nativeBlocks != null && hitPos != null) nativeBlocks[hitPos] else null
                                    var invoked = false
                                    var rootType = "none"
                                    var rootMessage = "none"
                                    try {
                                        if (setBlockMethod != null && nativeCarriage != null && emptyPos != null && placementCandidate != null) {
                                            setBlockMethod.invoke(nativeCarriage, emptyPos.immutable(), placementCandidate)
                                            invoked = true
                                        }
                                    } catch (placementException: Throwable) {
                                        var root: Throwable = placementException
                                        val seen = java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Throwable, Boolean>())
                                        while (root.cause != null && seen.add(root)) root = root.cause!!
                                        rootType = root.javaClass.name
                                        rootMessage = (root.message ?: "null").replace('\\n', ' ').replace('\\r', ' ')
                                    }
                                    val placedEntry = if (nativeBlocks != null && emptyPos != null) nativeBlocks[emptyPos] else null
                                    val placedState = placedEntry?.javaClass?.methods?.firstOrNull { method ->
                                        method.name == "state" && method.parameterCount == 0
                                    }?.invoke(placedEntry)
                                    val afterSize = nativeBlocks?.size ?: -1
                                    val sourceAfter = if (nativeBlocks != null && hitPos != null) nativeBlocks[hitPos] else null
                                    val success = invoked
                                        && beforeSize >= 0 && afterSize == beforeSize + 1
                                        && java.util.Objects.equals(placedState, stoneState)
                                        && sourceBefore === sourceAfter
                                    System.setProperty("vs2.productionNativePlacementMutationProbed", "true")
                                    logger.info("GATE_D_NATIVE_PLACEMENT_EMPTY_CELL_MUTATION carriage_id={} hit_local={} empty_local={} method_found={} invoked={} before_size={} after_size={} size_plus_one={} placed_state={} state_match={} source_identity_stable={} success={} root_type={} root_message={} fixture_only=true",
                                        nativeCarriageId, hitPos, emptyPos, setBlockMethod != null, invoked,
                                        beforeSize, afterSize, afterSize == beforeSize + 1, placedState,
                                        java.util.Objects.equals(placedState, stoneState), sourceBefore === sourceAfter,
                                        success, rootType, rootMessage)
                                }'''

if "GATE_D_NATIVE_PLACEMENT_EMPTY_CELL_MUTATION" not in server:
    if anchor not in server:
        raise SystemExit("Phase 111 could not find Phase 110 candidate log anchor")
    server = server.replace(anchor, probe, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_EMPTY_CELL_MUTATION',
    'Blocks.STONE.defaultBlockState()',
    'setBlockMethod.invoke(nativeCarriage, emptyPos.immutable(), placementCandidate)',
    'afterSize == beforeSize + 1',
    'sourceBefore === sourceAfter',
    'fixture_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 111 lost fixture placement anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
print("Phase 111: placed one inert STONE block into the exact authoritative empty carriage cell only in the disposable smoke fixture and verifies map/state/source stability")

# Run the direct-carry interaction bridge after every existing interaction phase has
# already instrumented GateE, so it can reuse the complete validated read-only block.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase112.py")), run_name="__main__")
