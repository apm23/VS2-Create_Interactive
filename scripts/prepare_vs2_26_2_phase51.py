#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
initializer = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/ValkyrienSkiesModFabric.kt"
probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
fabric_mod = ROOT / "fabric/src/main/resources/fabric.mod.json"

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

client_probe.parent.mkdir(parents=True, exist_ok=True)
client_probe.write_text(r'''package org.valkyrienskies.mod.fabric.client;

import java.lang.reflect.Field;
import java.util.Comparator;
import java.util.Map;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/** CI-only client observer. Create handles the local player collision on the client and skips ServerPlayer. */
public final class GateEClientProbe implements ClientModInitializer {
    private static final Logger LOGGER = LogManager.getLogger("VS2-GateE-Client");
    private long ticks;

    @Override
    public void onInitializeClient() {
        boolean enabled = Boolean.getBoolean("vs2.gateD") || "true".equals(System.getenv("GITHUB_ACTIONS"));
        if (!enabled) return;

        LOGGER.info("GATE_E_CLIENT_READY");
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            ticks++;
            if (ticks % 20L != 0L || client.player == null || client.level == null) return;

            var player = client.player;
            Entity carriage = client.level.getEntitiesOfClass(
                    Entity.class,
                    player.getBoundingBox().inflate(64.0),
                    entity -> "create:carriage_contraption".equals(
                            BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString()))
                .stream()
                .min(Comparator.comparingDouble(entity -> entity.distanceToSqr(player)))
                .orElse(null);
            if (carriage == null) {
                LOGGER.info("GATE_E_CLIENT_WAITING_CARRIAGE player_pos={},{},{} on_ground={}",
                    player.getX(), player.getY(), player.getZ(), player.onGround());
                return;
            }

            boolean createRegisteredContact = false;
            String contactFieldState = "missing";
            try {
                Field field = carriage.getClass().getDeclaredField("collidingEntities");
                field.setAccessible(true);
                Object value = field.get(carriage);
                if (value instanceof Map<?, ?> map) {
                    createRegisteredContact = map.containsKey(player);
                    contactFieldState = "map_size=" + map.size();
                } else {
                    contactFieldState = "type=" + (value == null ? "null" : value.getClass().getName());
                }
            } catch (ReflectiveOperationException | RuntimeException exception) {
                contactFieldState = "error=" + exception.getClass().getSimpleName();
            }

            Vec3 velocity = player.getDeltaMovement();
            var box = carriage.getBoundingBox();
            LOGGER.info(
                "GATE_E_CLIENT_STATE player_pos={},{},{} on_ground={} velocity={},{},{} carriage_pos={},{},{} carriage_box={},{},{} -> {},{},{} create_registered_contact={} contact_field={}",
                player.getX(), player.getY(), player.getZ(), player.onGround(),
                velocity.x, velocity.y, velocity.z,
                carriage.getX(), carriage.getY(), carriage.getZ(),
                box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ,
                createRegisteredContact, contactFieldState);
        });
    }
}
''', encoding="utf-8")

metadata = json.loads(fabric_mod.read_text(encoding="utf-8"))
client_entrypoint = "org.valkyrienskies.mod.fabric.client.GateEClientProbe"
client_entrypoints = metadata.setdefault("entrypoints", {}).setdefault("client", [])
if client_entrypoint not in client_entrypoints:
    client_entrypoints.append(client_entrypoint)
fabric_mod.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 51: traced server drift/VS2 drag plus Create's client-side local-player contact path using read-only telemetry; no train controls, schedules, player motion, collision response, or VS2 physics are modified")
