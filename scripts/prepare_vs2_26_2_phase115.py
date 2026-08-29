#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server = server_probe.read_text(encoding="utf-8")
client = client_probe.read_text(encoding="utf-8")

# Production-world #101 proved the late-target ServerLevel setBlock mutation succeeds,
# but Phase 113 never observed the new STONE in the client carriage map. Do not guess
# Create networking. Instrument the exact post-mutation server/client surfaces read-only
# so the next real-world run tells us whether the client map stays absent/stale and which
# public carriage methods plausibly own block/update/sync/packet propagation.
server_anchor = '''                        logger.info("GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION carriage_id={} hit_local={} empty_local={} invoked={} before_size={} after_size={} state_match={} source_identity_stable={} success={} fixture_only=true",
                            carriageId, hitPos, emptyPos, invoked, beforeSize, afterSize,
                            java.util.Objects.equals(placedState, stoneState), sourceBefore === sourceAfter, success)'''
server_probe_text = server_anchor + '''
                        if (success && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementReplicationSurfaceProbed")) {
                            System.setProperty("vs2.productionNativePlacementReplicationSurfaceProbed", "true")
                            val carriageMethods = carriage?.javaClass?.methods
                                ?.filter { method ->
                                    val name = method.name.lowercase()
                                    name.contains("block") || name.contains("sync") || name.contains("update")
                                        || name.contains("packet") || name.contains("send") || name.contains("contraption")
                                }
                                ?.map { method ->
                                    method.name + "(" + method.parameterTypes.joinToString(",") { it.simpleName } + "):" + method.returnType.simpleName
                                }
                                ?.distinct()?.sorted()?.joinToString(";") ?: ""
                            val contraptionMethods = contraption?.javaClass?.methods
                                ?.filter { method ->
                                    val name = method.name.lowercase()
                                    name.contains("block") || name.contains("sync") || name.contains("update")
                                        || name.contains("packet") || name.contains("send")
                                }
                                ?.map { method ->
                                    method.name + "(" + method.parameterTypes.joinToString(",") { it.simpleName } + "):" + method.returnType.simpleName
                                }
                                ?.distinct()?.sorted()?.joinToString(";") ?: ""
                            logger.info("GATE_D_NATIVE_PLACEMENT_REPLICATION_SURFACE carriage_id={} carriage_methods=[{}] contraption_methods=[{}] read_only=true",
                                carriageId, carriageMethods, contraptionMethods)
                        }'''
if "GATE_D_NATIVE_PLACEMENT_REPLICATION_SURFACE" not in server:
    if server_anchor not in server:
        raise SystemExit("Phase 115 could not find Phase 114 mutation log anchor")
    server = server.replace(server_anchor, server_probe_text, 1)

client_anchor = '''                        if (synced) {
                            System.setProperty("vs2.productionNativePlacementClientObserved", "true");
                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_SYNC carriage_id={} player_tick={} empty_local={} entry_present={} state={} synced=true read_only=true",
                                carriage.getId(), player.tickCount, replicatedPos, replicatedEntry != null, replicatedState);
                        }'''
client_probe_text = '''                        if (synced) {
                            System.setProperty("vs2.productionNativePlacementClientObserved", "true");
                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_SYNC carriage_id={} player_tick={} empty_local={} entry_present={} state={} synced=true read_only=true",
                                carriage.getId(), player.tickCount, replicatedPos, replicatedEntry != null, replicatedState);
                        } else if (player.tickCount % 20 == 0) {
                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_PENDING carriage_id={} player_tick={} empty_local={} entry_present={} state={} synced=false read_only=true",
                                carriage.getId(), player.tickCount, replicatedPos, replicatedEntry != null, replicatedState);
                        }'''
if "GATE_F_NATIVE_PLACEMENT_CLIENT_PENDING" not in client:
    if client_anchor not in client:
        raise SystemExit("Phase 115 could not find Phase 113 client replication branch")
    client = client.replace(client_anchor, client_probe_text, 1)

required_server = [
    'GATE_D_NATIVE_PLACEMENT_REPLICATION_SURFACE',
    'productionNativePlacementReplicationSurfaceProbed',
    'name.contains("sync")',
    'name.contains("packet")',
    'read_only=true',
]
required_client = [
    'GATE_F_NATIVE_PLACEMENT_CLIENT_PENDING',
    'entry_present={}',
    'synced=false read_only=true',
]
missing = [token for token in required_server if token not in server] + [token for token in required_client if token not in client]
if missing:
    raise SystemExit("Phase 115 lost replication telemetry anchors: " + ", ".join(missing))

for forbidden in ['.put(', '.remove(', '.clear(', 'setBlock(', 'setPos(', 'setDeltaMovement(', '.useItemOn(', '.useItem(', '.attack(']:
    if forbidden in client_probe_text:
        raise SystemExit("Phase 115 client telemetry contains forbidden mutation: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
client_probe.write_text(client, encoding="utf-8")
print("Phase 115: instruments exact post-placement server replication surface and client pending/synced state read-only; no gameplay, train, inventory, world, or physics mutation")

# Production-world #103 proved the first direct carry delta can be sampled during the
# fixture transition and permanently close the read-only observer before later stable
# carriage motion. Keep measuring after transient fixture-only failures.
phase116 = Path(__file__).with_name("prepare_vs2_26_2_phase116.py")
exec(compile(phase116.read_text(encoding="utf-8"), str(phase116), "exec"))
