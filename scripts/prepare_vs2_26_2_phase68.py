#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"

# A 0.05-block air gap is enough for ContinuousOBBCollider to report no surface
# collision when the smoke LocalPlayer has zero vertical motion. Place the test
# player's feet exactly on Create's own simplified collider top instead. Create
# inflates the local entity AABB by 1e-7, so exact surface contact is the correct
# standing-state fixture and does not require a forced penetration.
source = client_probe.read_text(encoding="utf-8")
old_client_target = '''Vec3 localTarget = new Vec3(localFeetFixture.x, bestTop + 0.05, localFeetFixture.z);'''
new_client_target = '''Vec3 localTarget = new Vec3(localFeetFixture.x, bestTop, localFeetFixture.z);'''
if old_client_target not in source:
    raise SystemExit("Phase 68 could not find Phase 67 client collider target")
source = source.replace(old_client_target, new_client_target, 1)
old_client_check = '''if (Math.abs(gap - 0.05) > 0.02) {'''
new_client_check = '''if (Math.abs(gap) > 1.0E-4) {'''
if old_client_check not in source:
    raise SystemExit("Phase 68 could not find Phase 67 client alignment check")
source = source.replace(old_client_check, new_client_check, 1)
client_probe.write_text(source, encoding="utf-8")

# Phase 60 still places ServerPlayer at block-coordinate Y+1. Mirror the exact
# simplified-collider surface selection server-side so ServerPlayer and
# LocalPlayer start from the same physical surface before train motion.
server = server_probe.read_text(encoding="utf-8")
old = '''                    if (blocks != null && toGlobal != null) {
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
                    }'''
new = '''                    if (blocks != null && toGlobal != null) {
                        val getSimplified = contraption?.javaClass?.getMethod("getSimplifiedEntityColliders")
                        val simplified = getSimplified?.invoke(contraption)
                        if (simplified != null) {
                            val listType = simplified.javaClass
                            val size = listType.getField("size").getInt(simplified)
                            val cx = listType.getField("centerX").get(simplified) as DoubleArray
                            val cy = listType.getField("centerY").get(simplified) as DoubleArray
                            val cz = listType.getField("centerZ").get(simplified) as DoubleArray
                            val ex = listType.getField("extentsX").get(simplified) as DoubleArray
                            val ey = listType.getField("extentsY").get(simplified) as DoubleArray
                            val ez = listType.getField("extentsZ").get(simplified) as DoubleArray
                            val toLocal = carriage.javaClass.methods.firstOrNull { method ->
                                method.name == "toLocalVector" && method.parameterCount == 2 &&
                                    method.parameterTypes[0] == net.minecraft.world.phys.Vec3::class.java &&
                                    method.parameterTypes[1] == java.lang.Float.TYPE
                            }
                            if (toLocal != null) {
                                val localFeet = toLocal.invoke(carriage, player.position(), 0.0f) as net.minecraft.world.phys.Vec3
                                val eps = 1.0E-5
                                var best = -1
                                var bestTop = -Double.MAX_VALUE
                                for (i in 0 until size) {
                                    val minX = cx[i] - ex[i] - eps
                                    val maxX = cx[i] + ex[i] + eps
                                    val minZ = cz[i] - ez[i] - eps
                                    val maxZ = cz[i] + ez[i] + eps
                                    val top = cy[i] + ey[i]
                                    if (localFeet.x < minX || localFeet.x > maxX || localFeet.z < minZ || localFeet.z > maxZ) continue
                                    if (top > localFeet.y + 1.5) continue
                                    if (top > bestTop) {
                                        bestTop = top
                                        best = i
                                    }
                                }
                                if (best >= 0) {
                                    val localTarget = net.minecraft.world.phys.Vec3(localFeet.x, bestTop, localFeet.z)
                                    val target = toGlobal.invoke(carriage, localTarget, 0.0f) as net.minecraft.world.phys.Vec3
                                    val dx = target.x - player.x
                                    val dy = target.y - player.y
                                    val dz = target.z - player.z
                                    val distanceSq = dx * dx + dy * dy + dz * dz
                                    player.setPos(target.x, target.y, target.z)
                                    player.setDeltaMovement(net.minecraft.world.phys.Vec3.ZERO)
                                    logger.info(
                                        "GATE_D_FIXTURE_PLAYER_REPOSITIONED old_distance_sq={} target={},{},{} source=simplified_collider_surface collider_index={} local_top={}",
                                        distanceSq, target.x, target.y, target.z, best, bestTop)
                                    return@register
                                }
                            }
                        }
                    }'''
if old not in server:
    raise SystemExit("Phase 68 could not find Phase 60 server fixture block-top normalizer")
server = server.replace(old, new, 1)
server_probe.write_text(server, encoding="utf-8")

print("Phase 68: aligned both ServerPlayer and LocalPlayer exactly to Create's simplified collision-surface top so standing contact is tested without the previous 0.05-block air gap; CI harness only")

# The verified save starts ServerPlayer far from real collision geometry, so Phase
# 68's under-feet selector alone cannot normalize the server fixture. Chain the
# globally-nearest simplified-collider selector before smoke execution.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase69.py")), run_name="__main__")
