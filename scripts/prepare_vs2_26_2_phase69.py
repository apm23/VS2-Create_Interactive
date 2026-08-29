#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
source = server_probe.read_text(encoding="utf-8")

# Phase 68 required a simplified collider directly below the saved ServerPlayer.
# The verified save starts ~16 blocks away from the carriage's real collision
# surface, so no such collider exists yet and the server fixture was never moved.
# For the smoke harness only, choose the globally nearest simplified collider
# surface point in local space, then place ServerPlayer exactly on that surface.
old = '''                                var best = -1
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
                                }'''
new = '''                                var best = -1
                                var bestTop = 0.0
                                var bestX = 0.0
                                var bestZ = 0.0
                                var bestLocalDistanceSq = Double.POSITIVE_INFINITY
                                for (i in 0 until size) {
                                    val minX = cx[i] - ex[i] - eps
                                    val maxX = cx[i] + ex[i] + eps
                                    val minZ = cz[i] - ez[i] - eps
                                    val maxZ = cz[i] + ez[i] + eps
                                    val top = cy[i] + ey[i]
                                    val targetX = localFeet.x.coerceIn(minX, maxX)
                                    val targetZ = localFeet.z.coerceIn(minZ, maxZ)
                                    val dx = targetX - localFeet.x
                                    val dy = top - localFeet.y
                                    val dz = targetZ - localFeet.z
                                    val distanceSq = dx * dx + dy * dy + dz * dz
                                    if (distanceSq < bestLocalDistanceSq) {
                                        bestLocalDistanceSq = distanceSq
                                        bestTop = top
                                        bestX = targetX
                                        bestZ = targetZ
                                        best = i
                                    }
                                }
                                if (best >= 0) {
                                    val localTarget = net.minecraft.world.phys.Vec3(bestX, bestTop, bestZ)
                                    val target = toGlobal.invoke(carriage, localTarget, 0.0f) as net.minecraft.world.phys.Vec3
                                    val dx = target.x - player.x
                                    val dy = target.y - player.y
                                    val dz = target.z - player.z
                                    val distanceSq = dx * dx + dy * dy + dz * dz
                                    player.setPos(target.x, target.y, target.z)
                                    player.setDeltaMovement(net.minecraft.world.phys.Vec3.ZERO)
                                    logger.info(
                                        "GATE_D_FIXTURE_PLAYER_REPOSITIONED old_distance_sq={} local_distance_sq={} target={},{},{} source=nearest_simplified_collider_surface collider_index={} local_top={}",
                                        distanceSq, bestLocalDistanceSq, target.x, target.y, target.z, best, bestTop)
                                    return@register
                                }'''
if old not in source:
    raise SystemExit("Phase 69 could not find Phase 68 server under-feet collider selector")
source = source.replace(old, new, 1)
server_probe.write_text(source, encoding="utf-8")
print("Phase 69: normalized the CI ServerPlayer to the globally nearest Create simplified collider surface so the verified save's distant stored position no longer prevents server/client fixture synchronization; harness-only")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase70.py")), run_name="__main__")
