#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #99 exposed a harness race: the client published the exact native
# placement target after the one-shot server fixture block had already completed, so
# Phase 109/111 had no second chance to run. Add a fixture-only retry before the normal
# 20-tick Gate D telemetry throttle. It runs only after the exact client target exists,
# only while no placement mutation has been probed, and uses the same public Create
# setBlock API with one inert STONE candidate. Normal gameplay never sets the fixture flag.
anchor = '''            ticks++
            if (ticks % 20L != 0L) return@register'''
retry = '''            ticks++

            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")) {
                val placementPlayer = server.playerList.players.firstOrNull()
                val placementLevel = placementPlayer?.level()
                val carriageId = System.getProperty("vs2.productionNativePlacementCarriageId")?.toIntOrNull()
                val hitX = System.getProperty("vs2.productionNativePlacementHitX")?.toIntOrNull()
                val hitY = System.getProperty("vs2.productionNativePlacementHitY")?.toIntOrNull()
                val hitZ = System.getProperty("vs2.productionNativePlacementHitZ")?.toIntOrNull()
                val emptyX = System.getProperty("vs2.productionNativePlacementEmptyX")?.toIntOrNull()
                val emptyY = System.getProperty("vs2.productionNativePlacementEmptyY")?.toIntOrNull()
                val emptyZ = System.getProperty("vs2.productionNativePlacementEmptyZ")?.toIntOrNull()
                if (placementLevel != null && carriageId != null && hitX != null && hitY != null && hitZ != null
                        && emptyX != null && emptyY != null && emptyZ != null) {
                    try {
                        val getEntity = placementLevel.javaClass.methods.firstOrNull { method ->
                            method.name == "getEntity" && method.parameterCount == 1
                                && method.parameterTypes[0] == java.lang.Integer.TYPE
                        }
                        val carriage = getEntity?.invoke(placementLevel, carriageId)
                        val contraption = carriage?.javaClass?.methods?.firstOrNull { method ->
                            method.name == "getContraption" && method.parameterCount == 0
                        }?.invoke(carriage)
                        val blocks = contraption?.javaClass?.methods?.firstOrNull { method ->
                            method.name == "getBlocks" && method.parameterCount == 0
                        }?.invoke(contraption) as? Map<*, *>
                        val hitPos = net.minecraft.core.BlockPos(hitX, hitY, hitZ)
                        val emptyPos = net.minecraft.core.BlockPos(emptyX, emptyY, emptyZ)
                        val sourceEntry = blocks?.get(hitPos)
                        val sourceBefore = sourceEntry
                        val emptyBefore = blocks?.get(emptyPos)
                        val stoneState = net.minecraft.world.level.block.Blocks.STONE.defaultBlockState()
                        val constructor = sourceEntry?.javaClass?.constructors?.firstOrNull { ctor ->
                            val params = ctor.parameterTypes
                            params.size == 3
                                && params[0] == net.minecraft.core.BlockPos::class.java
                                && params[1].isInstance(stoneState)
                        }
                        val candidate = if (constructor != null && emptyBefore == null) {
                            constructor.newInstance(emptyPos.immutable(), stoneState, null)
                        } else null
                        val setBlock = carriage?.javaClass?.methods?.firstOrNull { method ->
                            val params = method.parameterTypes
                            method.name == "setBlock" && params.size == 2
                                && params[0] == net.minecraft.core.BlockPos::class.java
                                && candidate != null && params[1].isInstance(candidate)
                        }
                        val beforeSize = blocks?.size ?: -1
                        var invoked = false
                        if (setBlock != null && carriage != null && candidate != null) {
                            setBlock.invoke(carriage, emptyPos.immutable(), candidate)
                            invoked = true
                        }
                        val placedEntry = blocks?.get(emptyPos)
                        val placedState = placedEntry?.javaClass?.methods?.firstOrNull { method ->
                            method.name == "state" && method.parameterCount == 0
                        }?.invoke(placedEntry)
                        val afterSize = blocks?.size ?: -1
                        val sourceAfter = blocks?.get(hitPos)
                        val success = invoked
                            && beforeSize >= 0 && afterSize == beforeSize + 1
                            && java.util.Objects.equals(placedState, stoneState)
                            && sourceBefore === sourceAfter
                        if (success) {
                            System.setProperty("vs2.productionNativePlacementMutationProbed", "true")
                            System.setProperty("vs2.productionNativePlacementMutationSucceeded", "true")
                        }
                        logger.info("GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION carriage_id={} hit_local={} empty_local={} invoked={} before_size={} after_size={} state_match={} source_identity_stable={} success={} fixture_only=true",
                            carriageId, hitPos, emptyPos, invoked, beforeSize, afterSize,
                            java.util.Objects.equals(placedState, stoneState), sourceBefore === sourceAfter, success)
                    } catch (placementException: Throwable) {
                        var root: Throwable = placementException
                        val seen = java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Throwable, Boolean>())
                        while (root.cause != null && seen.add(root)) root = root.cause!!
                        logger.info("GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION carriage_id={} invoked=false success=false root_type={} root_message={} fixture_only=true",
                            carriageId, root.javaClass.name, (root.message ?: "null").replace('\\n', ' ').replace('\\r', ' '))
                    }
                }
            }

            if (ticks % 20L != 0L) return@register'''

if "GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION" not in server:
    if anchor not in server:
        raise SystemExit("Phase 114 could not find recurring Gate D tick throttle anchor")
    server = server.replace(anchor, retry, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION',
    'vs2.productionNativePlacementTargetReady',
    'vs2.productionNativePlacementMutationSucceeded',
    'setBlock.invoke(carriage, emptyPos.immutable(), candidate)',
    'afterSize == beforeSize + 1',
    'sourceBefore === sourceAfter',
    'fixture_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 114 lost retry placement anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
print("Phase 114: retries the exact fixture-only server placement after native target publication so late client target timing cannot skip the mutation")
