#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
initializer = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/ValkyrienSkiesModFabric.kt"
probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"

source = initializer.read_text(encoding="utf-8")
anchor = "        ValkyrienSkiesMod.init()\n"
install = anchor + "\n        GateDProbe.install()\n"
if "GateDProbe.install()" not in source:
    if anchor not in source:
        raise SystemExit("Phase 51 could not find ValkyrienSkiesMod.init() anchor")
    source = source.replace(anchor, install, 1)
    initializer.write_text(source, encoding="utf-8")

probe.write_text(r'''package org.valkyrienskies.mod.fabric.common

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents
import net.minecraft.core.registries.BuiltInRegistries
import org.apache.logging.log4j.LogManager
import org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider

/** CI-only observer for verified Create train motion and player-relative stability. */
object GateDProbe {
    private val logger = LogManager.getLogger("VS2-GateD")

    fun install() {
        val enabled = java.lang.Boolean.getBoolean("vs2.gateD") || System.getenv("GITHUB_ACTIONS") == "true"
        if (!enabled) return

        var ticks = 0L
        var seenCarriage = false
        var moved = false
        var startX = 0.0
        var startY = 0.0
        var startZ = 0.0
        var playerStartX = 0.0
        var playerStartY = 0.0
        var playerStartZ = 0.0
        var playerNearAtStart = false
        var playerOnEnvelopeAtStart = false

        logger.info("GATE_D_INPROC_READY")
        logger.info("GATE_D_INPUT_OK transport=in_process_observer")

        ServerTickEvents.END_SERVER_TICK.register { server ->
            ticks++
            if (ticks % 20L != 0L) return@register

            val player = server.playerList.players.firstOrNull() ?: return@register
            val level = player.level()
            val carriage = level.allEntities.firstOrNull { entity ->
                BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString() == "create:carriage_contraption"
            }

            if (carriage == null) {
                if (ticks % 100L == 0L) {
                    val createEntityIds = level.allEntities
                        .map { BuiltInRegistries.ENTITY_TYPE.getKey(it.getType()).toString() }
                        .filter { it.startsWith("create:") || it.startsWith("railways:") }
                        .distinct().sorted().joinToString(",")
                    logger.info("GATE_D_WAITING_CARRIAGE tick={} create_entities=[{}]", ticks, createEntityIds)
                }
                return@register
            }

            val dragInfo = (player as? IEntityDraggingInformationProvider)?.draggingInformation

            if (!seenCarriage) {
                seenCarriage = true
                startX = carriage.getX()
                startY = carriage.getY()
                startZ = carriage.getZ()
                playerStartX = player.getX()
                playerStartY = player.getY()
                playerStartZ = player.getZ()

                val dx = playerStartX - startX
                val dy = playerStartY - startY
                val dz = playerStartZ - startZ
                playerNearAtStart = dx * dx + dy * dy + dz * dz <= 144.0

                val box = carriage.getBoundingBox()
                playerOnEnvelopeAtStart =
                    playerStartX >= box.minX && playerStartX <= box.maxX &&
                    playerStartZ >= box.minZ && playerStartZ <= box.maxZ &&
                    kotlin.math.abs(playerStartY - box.maxY) <= 0.25

                logger.info("GATE_D_CARRIAGE_PRESENT type={} pos={},{},{} gate_e_player_pos={},{},{} gate_e_carriage_box={},{},{} -> {},{},{}",
                    BuiltInRegistries.ENTITY_TYPE.getKey(carriage.getType()), startX, startY, startZ,
                    playerStartX, playerStartY, playerStartZ,
                    box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ)

                val velocity = player.getDeltaMovement()
                logger.info("GATE_D_GATE_E_SUPPORT_START on_ground={} velocity={},{},{} vs_last_ship={} vs_drag_ticks={} vs_drag_active={}",
                    player.onGround(), velocity.x, velocity.y, velocity.z,
                    dragInfo?.lastShipStoodOn, dragInfo?.ticksSinceStoodOnShip,
                    dragInfo?.isEntityBeingDraggedByAShip())

                if (playerOnEnvelopeAtStart) {
                    logger.info("GATE_D_GATE_E_CONTACT_START top_delta={} horizontal_inside=true",
                        playerStartY - box.maxY)
                }
                if (playerNearAtStart) logger.info("GATE_D_PLAYER_NEAR_START")
            }

            if (!moved) {
                val dx = carriage.getX() - startX
                val dy = carriage.getY() - startY
                val dz = carriage.getZ() - startZ
                val displacementSq = dx * dx + dy * dy + dz * dz
                if (displacementSq > 1.0) {
                    moved = true
                    val box = carriage.getBoundingBox()
                    val playerDx = player.getX() - playerStartX
                    val playerDy = player.getY() - playerStartY
                    val playerDz = player.getZ() - playerStartZ
                    val driftX = playerDx - dx
                    val driftY = playerDy - dy
                    val driftZ = playerDz - dz
                    val driftSq = driftX * driftX + driftY * driftY + driftZ * driftZ

                    logger.info("GATE_D_TRAIN_MOVED displacement_sq={} gate_e_player_pos={},{},{} gate_e_carriage_box={},{},{} -> {},{},{}",
                        displacementSq,
                        player.getX(), player.getY(), player.getZ(),
                        box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ)

                    val velocity = player.getDeltaMovement()
                    logger.info("GATE_D_GATE_E_SUPPORT_AFTER on_ground={} velocity={},{},{} vs_last_ship={} vs_drag_ticks={} vs_drag_active={}",
                        player.onGround(), velocity.x, velocity.y, velocity.z,
                        dragInfo?.lastShipStoodOn, dragInfo?.ticksSinceStoodOnShip,
                        dragInfo?.isEntityBeingDraggedByAShip())

                    if (playerOnEnvelopeAtStart) {
                        if (driftSq <= 0.5625) {
                            logger.info("GATE_D_GATE_E_PLAYER_CARRIED drift_sq={} player_delta={},{},{} carriage_delta={},{},{}",
                                driftSq, playerDx, playerDy, playerDz, dx, dy, dz)
                        } else {
                            logger.info("GATE_D_GATE_E_PLAYER_DRIFT drift_sq={} player_delta={},{},{} carriage_delta={},{},{}",
                                driftSq, playerDx, playerDy, playerDz, dx, dy, dz)
                        }
                    }

                    if (playerNearAtStart) {
                        val pdx = player.getX() - carriage.getX()
                        val pdy = player.getY() - carriage.getY()
                        val pdz = player.getZ() - carriage.getZ()
                        if (pdx * pdx + pdy * pdy + pdz * pdz <= 144.0) logger.info("GATE_D_PLAYER_NEAR_END")
                        else logger.info("GATE_D_PLAYER_FAR_END")
                    }
                }
            }
        }
    }
}
''', encoding="utf-8")

print("Phase 51: traced Create support state and VS2 drag acquisition alongside Gate E drift using read-only telemetry; no train controls, schedules, player motion, or VS2 physics are modified")
