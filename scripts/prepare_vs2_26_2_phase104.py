#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #71 proved the Phase 100 mismatch guard prevented the bad sibling
# fallback, but return@register also exited the whole server tick callback on the first
# non-matching carriage. Resolve the exact client-published entity id from the server
# level instead, then apply the published local fixture point through that entity's
# current Create frame. This remains production-smoke-fixture-only.
old = '''                    val syncToGlobal = carriage.javaClass.methods.firstOrNull { method ->
                        method.name == "toGlobalVector" && method.parameterCount == 2
                            && method.parameterTypes[0] == net.minecraft.world.phys.Vec3::class.java
                            && method.parameterTypes[1] == java.lang.Float.TYPE
                    }
                    if (syncCarriageId != null && syncLocalX != null && syncLocalY != null && syncLocalZ != null
                            && carriage.id == syncCarriageId && syncToGlobal != null) {
                        val syncLocal = net.minecraft.world.phys.Vec3(syncLocalX, syncLocalY, syncLocalZ)
                        val syncWorld = syncToGlobal.invoke(carriage, syncLocal, 0.0f) as net.minecraft.world.phys.Vec3
                        fixturePlayerChecked = true
                        player.setPos(syncWorld.x, syncWorld.y, syncWorld.z)
                        player.setDeltaMovement(net.minecraft.world.phys.Vec3(0.0, -0.08, 0.0))
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)
                        return@register
                    }
                    // Production smoke must never fall through to the legacy nearest-carriage
                    // fixture while waiting for the exact client-selected carriage. Run #70
                    // showed that fallback can teleport the ServerPlayer onto a sibling carriage,
                    // immediately breaking the client/server support frame. Leave the fixture
                    // unchecked and wait for the callback for the matching carriage instead.
                    return@register
'''
new = '''                    val syncLevelMethod = player.javaClass.methods.firstOrNull { method ->
                        method.name == "level" && method.parameterCount == 0
                    }
                    val syncLevel = syncLevelMethod?.invoke(player)
                    val syncGetEntity = syncLevel?.javaClass?.methods?.firstOrNull { method ->
                        method.name == "getEntity" && method.parameterCount == 1
                            && method.parameterTypes[0] == java.lang.Integer.TYPE
                    }
                    val syncCarriage = if (syncCarriageId != null && syncGetEntity != null) {
                        syncGetEntity.invoke(syncLevel, syncCarriageId)
                    } else null
                    val syncToGlobal = syncCarriage?.javaClass?.methods?.firstOrNull { method ->
                        method.name == "toGlobalVector" && method.parameterCount == 2
                            && method.parameterTypes[0] == net.minecraft.world.phys.Vec3::class.java
                            && method.parameterTypes[1] == java.lang.Float.TYPE
                    }
                    if (syncCarriageId != null && syncLocalX != null && syncLocalY != null && syncLocalZ != null
                            && syncCarriage != null && syncToGlobal != null) {
                        val syncLocal = net.minecraft.world.phys.Vec3(syncLocalX, syncLocalY, syncLocalZ)
                        val syncWorld = syncToGlobal.invoke(syncCarriage, syncLocal, 0.0f) as net.minecraft.world.phys.Vec3
                        fixturePlayerChecked = true
                        player.setPos(syncWorld.x, syncWorld.y, syncWorld.z)
                        player.setDeltaMovement(net.minecraft.world.phys.Vec3(0.0, -0.08, 0.0))
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)
                        return@register
                    }
                    logger.info("GATE_D_PRODUCTION_FIXTURE_WAITING_FOR_CLIENT_CARRIAGE carriage_id={} level_resolved={} entity_resolved={} transform_resolved={}",
                        syncCarriageId, syncLevel != null, syncCarriage != null, syncToGlobal != null)
                    return@register
'''
if old not in server:
    raise SystemExit("Phase 104 could not find Phase 100 carriage-match fixture block")
server = server.replace(old, new, 1)

required = [
    'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true',
    'GATE_D_PRODUCTION_FIXTURE_WAITING_FOR_CLIENT_CARRIAGE',
    'method.name == "getEntity"',
    'syncGetEntity.invoke(syncLevel, syncCarriageId)',
    'syncToGlobal.invoke(syncCarriage, syncLocal, 0.0f)',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 104 lost exact-carriage fixture anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
print("Phase 104: resolved the exact client-selected carriage entity by id for production smoke fixture sync; no production gameplay, train, or physics mutation")
