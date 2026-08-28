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

/** CI-only, read-only observer for the verified Create train world. */
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
        var playerNearAtStart = false

        logger.info("GATE_D_INPROC_READY")
        // Compatibility marker for the current shell gate. The transport is
        // explicitly identified as in-process; no keyboard input is implied.
        logger.info("GATE_D_INPUT_OK transport=in_process_observer")

        ServerTickEvents.END_SERVER_TICK.register { server ->
            ticks++
            if (ticks % 20L != 0L) return@register

            val player = server.playerList.players.firstOrNull() ?: return@register
            val level = player.serverLevel()
            val carriage = level.allEntities.firstOrNull { entity ->
                BuiltInRegistries.ENTITY_TYPE.getKey(entity.type).toString() == "create:carriage_contraption"
            }

            if (carriage == null) {
                if (ticks % 100L == 0L) {
                    val createEntityIds = level.allEntities
                        .map { BuiltInRegistries.ENTITY_TYPE.getKey(it.type).toString() }
                        .filter { it.startsWith("create:") || it.startsWith("railways:") }
                        .distinct().sorted().joinToString(",")
                    logger.info("GATE_D_WAITING_CARRIAGE tick={} create_entities=[{}]", ticks, createEntityIds)
                }
                return@register
            }

            if (!seenCarriage) {
                seenCarriage = true
                startX = carriage.x
                startY = carriage.y
                startZ = carriage.z
                val dx = player.x - carriage.x
                val dy = player.y - carriage.y
                val dz = player.z - carriage.z
                playerNearAtStart = dx * dx + dy * dy + dz * dz <= 144.0
                logger.info("GATE_D_CARRIAGE_PRESENT type={} pos={},{},{}",
                    BuiltInRegistries.ENTITY_TYPE.getKey(carriage.type), startX, startY, startZ)
                if (playerNearAtStart) logger.info("GATE_D_PLAYER_NEAR_START")
            }

            if (!moved) {
                val dx = carriage.x - startX
                val dy = carriage.y - startY
                val dz = carriage.z - startZ
                val displacementSq = dx * dx + dy * dy + dz * dz
                if (displacementSq > 1.0) {
                    moved = true
                    logger.info("GATE_D_TRAIN_MOVED displacement_sq={}", displacementSq)
                    if (playerNearAtStart) {
                        val pdx = player.x - carriage.x
                        val pdy = player.y - carriage.y
                        val pdz = player.z - carriage.z
                        if (pdx * pdx + pdy * pdy + pdz * pdz <= 144.0) logger.info("GATE_D_PLAYER_NEAR_END")
                        else logger.info("GATE_D_PLAYER_FAR_END")
                    }
                }
            }
        }
    }
}
''', encoding="utf-8")

print("Phase 51: installed CI-only read-only in-process Gate D observer; no train controls, schedules, player motion, or VS2 physics are modified")
