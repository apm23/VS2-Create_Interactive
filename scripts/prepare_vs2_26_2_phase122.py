#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #117 proved the authoritative CarriageContraptionEntity.setBlock mutation
# succeeds and the exact client carriage plus every rendered sibling still lack the new cell.
# Create Fly's own setBlock implementation sends ContraptionBlockChangedPacket through
# ServerChunkCache.sendToTrackingPlayers. Before touching networking or placement behavior,
# inspect the exact server tracking audience read-only at the successful fixture mutation.
anchor = '''                            logger.info("GATE_D_NATIVE_PLACEMENT_CREATE_SYNC carriage_id={} method_found={} invoked={} fixture_only=true",
                                carriageId, syncCarriage != null, syncInvoked)'''
probe = anchor + '''
                            if (!java.lang.Boolean.getBoolean("vs2.productionNativePlacementTrackingAudienceProbed")) {
                                System.setProperty("vs2.productionNativePlacementTrackingAudienceProbed", "true")
                                var trackingField = "none"
                                var trackingMethod = "none"
                                var trackingCount = -1
                                var trackingError = "none"
                                val carriageEntity = carriage as? net.minecraft.world.entity.Entity
                                val serverLevel = carriageEntity?.level() as? net.minecraft.server.level.ServerLevel
                                val chunkSource = serverLevel?.chunkSource
                                if (chunkSource != null && carriageEntity != null) {
                                    try {
                                        search@ for (field in chunkSource.javaClass.declaredFields) {
                                            try {
                                                field.isAccessible = true
                                                val value = field.get(chunkSource) ?: continue
                                                for (method in value.javaClass.methods) {
                                                    if (method.name != "getPlayers" || method.parameterCount != 2) continue
                                                    val params = method.parameterTypes
                                                    if (!net.minecraft.world.entity.Entity::class.java.isAssignableFrom(params[0])) continue
                                                    if (params[1] != java.lang.Boolean.TYPE && params[1] != java.lang.Boolean::class.java) continue
                                                    val result = method.invoke(value, carriageEntity, false)
                                                    trackingField = field.name + ":" + value.javaClass.name
                                                    trackingMethod = method.toGenericString()
                                                    trackingCount = when (result) {
                                                        is java.util.Collection<*> -> result.size()
                                                        is kotlin.collections.Iterable<*> -> {
                                                            var count = 0
                                                            for (ignored in result) count++
                                                            count
                                                        }
                                                        else -> -2
                                                    }
                                                    break@search
                                                }
                                            } catch (_: Throwable) {
                                                // Keep scanning other chunk-source fields; telemetry only.
                                            }
                                        }
                                    } catch (t: Throwable) {
                                        trackingError = t.javaClass.simpleName
                                    }
                                }
                                val levelPlayerCount = serverLevel?.players()?.size ?: -1
                                val nearestPlayerDistance = serverLevel?.players()
                                    ?.minOfOrNull { p -> p.position().distanceTo(carriageEntity!!.position()) } ?: -1.0
                                logger.info("GATE_D_NATIVE_PLACEMENT_TRACKING_AUDIENCE carriage_id={} level_players={} nearest_player_distance={} tracking_field={} tracking_method={} tracking_count={} error={} read_only=true",
                                    carriageId, levelPlayerCount, nearestPlayerDistance, trackingField, trackingMethod, trackingCount, trackingError)
                            }'''

if "GATE_D_NATIVE_PLACEMENT_TRACKING_AUDIENCE" not in server:
    if anchor not in server:
        raise SystemExit("Phase 122 could not find Phase 117 Create sync anchor")
    server = server.replace(anchor, probe, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_TRACKING_AUDIENCE',
    'productionNativePlacementTrackingAudienceProbed',
    'method.name != "getPlayers"',
    'tracking_count={}',
    'read_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 122 lost tracking-audience anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'setPos(', 'setDeltaMovement(',
    '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 122 found forbidden gameplay mutation: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
print("Phase 122: traces the exact server tracking audience used by Create block-change replication; read-only telemetry only")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase123.py")), run_name="__main__")
