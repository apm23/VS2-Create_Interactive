#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
source = probe.read_text(encoding="utf-8")

old_state = '''        var playerOnEnvelopeAtStart = false

        logger.info("GATE_D_INPROC_READY")'''
new_state = '''        var playerOnEnvelopeAtStart = false
        var fixturePlayerChecked = false

        logger.info("GATE_D_INPROC_READY")'''
if old_state not in source:
    raise SystemExit("Phase 60 could not find Gate D state anchor")
source = source.replace(old_state, new_state, 1)

old_before_drag = '''            val dragInfo = (player as? IEntityDraggingInformationProvider)?.draggingInformation

            if (!seenCarriage) {'''
new_before_drag = '''            // The verified save's stored player is horizontally inside the carriage AABB,
            // but Phase 59 proved the nearest actual contraption block top is ~16 blocks away.
            // Normalize only the CI smoke fixture once so carry/contact is tested from real
            // carriage geometry. This does not alter runtime physics or production behavior.
            if (!fixturePlayerChecked) {
                fixturePlayerChecked = true
                try {
                    val getContraption = carriage.javaClass.getMethod("getContraption")
                    val contraption = getContraption.invoke(carriage)
                    val getBlocks = contraption?.javaClass?.getMethod("getBlocks")
                    val blocks = getBlocks?.invoke(contraption) as? Map<*, *>
                    val toGlobal = carriage.javaClass.methods.firstOrNull { method ->
                        method.name == "toGlobalVector" && method.parameterCount == 2 &&
                            method.parameterTypes[0] == net.minecraft.world.phys.Vec3::class.java &&
                            method.parameterTypes[1] == java.lang.Float.TYPE
                    }
                    if (blocks != null && toGlobal != null) {
                        var bestWorldTop: net.minecraft.world.phys.Vec3? = null
                        var bestDistanceSq = Double.POSITIVE_INFINITY
                        for (key in blocks.keys) {
                            val pos = key as? net.minecraft.core.BlockPos ?: continue
                            val localTop = net.minecraft.world.phys.Vec3(
                                pos.x + 0.5, pos.y + 1.0, pos.z + 0.5)
                            val worldTop = toGlobal.invoke(carriage, localTop, 0.0f) as? net.minecraft.world.phys.Vec3 ?: continue
                            val dx = worldTop.x - player.x
                            val dy = worldTop.y - player.y
                            val dz = worldTop.z - player.z
                            val distanceSq = dx * dx + dy * dy + dz * dz
                            if (distanceSq < bestDistanceSq) {
                                bestDistanceSq = distanceSq
                                bestWorldTop = worldTop
                            }
                        }
                        val target = bestWorldTop
                        if (target != null && bestDistanceSq > 4.0) {
                            player.setPos(target.x, target.y + 0.05, target.z)
                            player.setDeltaMovement(net.minecraft.world.phys.Vec3.ZERO)
                            logger.info(
                                "GATE_D_FIXTURE_PLAYER_REPOSITIONED old_distance_sq={} target={},{},{} source=nearest_contraption_block_top",
                                bestDistanceSq, target.x, target.y + 0.05, target.z)
                            return@register
                        } else if (target != null) {
                            logger.info("GATE_D_FIXTURE_PLAYER_ALREADY_ON_GEOMETRY distance_sq={}", bestDistanceSq)
                        }
                    }
                } catch (exception: ReflectiveOperationException) {
                    logger.info("GATE_D_FIXTURE_PLAYER_NORMALIZE_ERROR type={}", exception.javaClass.simpleName)
                }
            }

            val dragInfo = (player as? IEntityDraggingInformationProvider)?.draggingInformation

            if (!seenCarriage) {'''
if old_before_drag not in source:
    raise SystemExit("Phase 60 could not find Gate D pre-baseline anchor")
source = source.replace(old_before_drag, new_before_drag, 1)

probe.write_text(source, encoding="utf-8")
print("Phase 60: normalized the CI smoke player's saved position onto the nearest real Create carriage block top before measuring carry; test-harness-only, no production physics changes")
