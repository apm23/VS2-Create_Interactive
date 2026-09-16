#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
source = probe.read_text(encoding="utf-8")

# Natural-landing admission varies by which carriage the CI fixture normalizes onto.
# GateDProbe currently takes level.allEntities.firstOrNull(create:carriage_contraption),
# then Phase60+ performs one-shot fixture normalization inside that carriage.  Trace
# every available carriage before that first-hit selection so a later deterministic
# fixture selector can be based on stable geometry instead of runtime entity ids.
# This script is intentionally read-only: it adds logs only and does not change the
# selected carriage, player/train position, velocity, collision, input, or timing.
state_anchor = '''        var fixturePlayerChecked = false\n'''
if "runwaySelectionTraceDone" not in source:
    if state_anchor not in source:
        raise SystemExit("runway selection trace could not find Phase60 fixture state anchor")
    source = source.replace(
        state_anchor,
        state_anchor + '''        var runwaySelectionTraceDone = false\n''',
        1,
    )

selection_anchor = '''            val carriage = level.allEntities.firstOrNull { entity ->\n'''
trace = r'''            if (!runwaySelectionTraceDone) {
                val runwayCandidates = level.allEntities.filter { entity ->
                    BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString() == "create:carriage_contraption"
                }
                if (runwayCandidates.isNotEmpty()) {
                    runwaySelectionTraceDone = true
                    val currentFirstId = runwayCandidates.first().getId()
                    logger.info(
                        "REFERENCE_OWNER_V2_RUNWAY_SELECTION candidate_count={} current_first_id={} source=level_allEntities_firstOrNull read_only=true",
                        runwayCandidates.size, currentFirstId)
                    for (candidate in runwayCandidates) {
                        var blockCount = -1
                        var minX = Int.MAX_VALUE
                        var minY = Int.MAX_VALUE
                        var minZ = Int.MAX_VALUE
                        var maxX = Int.MIN_VALUE
                        var maxY = Int.MIN_VALUE
                        var maxZ = Int.MIN_VALUE
                        var nearestWorldTopDistanceSq = Double.POSITIVE_INFINITY
                        var geometryState = "unresolved"
                        try {
                            val contraption = candidate.javaClass.getMethod("getContraption").invoke(candidate)
                            val blocks = contraption?.javaClass?.getMethod("getBlocks")?.invoke(contraption) as? Map<*, *>
                            val toGlobal = candidate.javaClass.methods.firstOrNull { method ->
                                method.name == "toGlobalVector" && method.parameterCount == 2 &&
                                    method.parameterTypes[0] == net.minecraft.world.phys.Vec3::class.java &&
                                    method.parameterTypes[1] == java.lang.Float.TYPE
                            }
                            if (blocks != null) {
                                blockCount = blocks.size
                                for (key in blocks.keys) {
                                    val pos = key as? net.minecraft.core.BlockPos ?: continue
                                    minX = kotlin.math.min(minX, pos.x)
                                    minY = kotlin.math.min(minY, pos.y)
                                    minZ = kotlin.math.min(minZ, pos.z)
                                    maxX = kotlin.math.max(maxX, pos.x)
                                    maxY = kotlin.math.max(maxY, pos.y)
                                    maxZ = kotlin.math.max(maxZ, pos.z)
                                    if (toGlobal != null) {
                                        val localTop = net.minecraft.world.phys.Vec3(pos.x + 0.5, pos.y + 1.0, pos.z + 0.5)
                                        val worldTop = toGlobal.invoke(candidate, localTop, 0.0f) as? net.minecraft.world.phys.Vec3 ?: continue
                                        val dx = worldTop.x - player.x
                                        val dy = worldTop.y - player.y
                                        val dz = worldTop.z - player.z
                                        val d2 = dx * dx + dy * dy + dz * dz
                                        if (d2 < nearestWorldTopDistanceSq) nearestWorldTopDistanceSq = d2
                                    }
                                }
                                geometryState = if (blockCount > 0) "blocks_mapped" else "empty_blocks"
                            } else {
                                geometryState = "blocks_missing"
                            }
                        } catch (exception: ReflectiveOperationException) {
                            geometryState = "reflection_error=" + exception.javaClass.simpleName
                        }
                        val normalizedMinX = if (blockCount > 0) minX else 0
                        val normalizedMinY = if (blockCount > 0) minY else 0
                        val normalizedMinZ = if (blockCount > 0) minZ else 0
                        val normalizedMaxX = if (blockCount > 0) maxX else 0
                        val normalizedMaxY = if (blockCount > 0) maxY else 0
                        val normalizedMaxZ = if (blockCount > 0) maxZ else 0
                        val spanX = if (blockCount > 0) maxX - minX + 1 else 0
                        val spanY = if (blockCount > 0) maxY - minY + 1 else 0
                        val spanZ = if (blockCount > 0) maxZ - minZ + 1 else 0
                        val box = candidate.getBoundingBox()
                        logger.info(
                            "REFERENCE_OWNER_V2_RUNWAY_CANDIDATE candidate_id={} uuid={} selected_by_current_first={} block_count={} local_bounds={},{},{}->{},{},{} local_span={},{},{} nearest_world_top_d2={} geometry_state={} pos={},{},{} box={},{},{}->{},{},{} read_only=true",
                            candidate.getId(), candidate.getUUID(), candidate.getId() == currentFirstId,
                            blockCount,
                            normalizedMinX, normalizedMinY, normalizedMinZ,
                            normalizedMaxX, normalizedMaxY, normalizedMaxZ,
                            spanX, spanY, spanZ,
                            nearestWorldTopDistanceSq, geometryState,
                            candidate.getX(), candidate.getY(), candidate.getZ(),
                            box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ)
                    }
                    logger.info(
                        "REFERENCE_OWNER_V2_RUNWAY_SELECTION_TRACE_COMPLETE current_first_id={} selector_unchanged=true player_mutation=false train_mutation=false collision_mutation=false input_mutation=false timing_mutation=false",
                        currentFirstId)
                }
            }

'''
if "REFERENCE_OWNER_V2_RUNWAY_SELECTION_TRACE_COMPLETE" not in source:
    if selection_anchor not in source:
        raise SystemExit("runway selection trace could not find current firstOrNull carriage selector")
    source = source.replace(selection_anchor, trace + selection_anchor, 1)

inserted = trace
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setVelocity(", "setNoGravity(", "setOnGround(", "KeyMapping.set(",
]:
    if forbidden in inserted:
        raise SystemExit("runway selection trace introduced forbidden mutation: " + forbidden)

probe.write_text(source, encoding="utf-8")
print("REFERENCE_OWNER_V2_RUNWAY_SELECTION_TRACE prepared=true read_only=true selector_unchanged=true")
