#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"

source = client_probe.read_text(encoding="utf-8")

# Production-world #55 proved that publishing a world-space fixture target is still
# racy: the train can advance between LocalPlayer normalization and the integrated
# server consuming the coordinates, so the authoritative server teleport lands on
# stale world coordinates. Publish the exact carriage-local target and carriage id
# instead. The server transforms that local point through its current carriage frame,
# preserving the same physical surface even if the train moved in the meantime.
old_early_ready = '''fixtureClientNormalized = true;
                                if (productionSmokeFixture) {
                                    System.setProperty("vs2.productionClientFixtureReady", "true");
                                    LOGGER.info("GATE_E_PRODUCTION_FIXTURE_CLIENT_READY player_tick={}", player.tickCount);
                                }'''
if old_early_ready in source:
    source = source.replace(old_early_ready, 'fixtureClientNormalized = true;', 1)

old_world_publish = '''fixtureColliderNormalized = true;
                                if (productionSmokeFixture) {
                                    System.setProperty("vs2.productionClientFixtureX", Double.toString(worldTarget.x));
                                    System.setProperty("vs2.productionClientFixtureY", Double.toString(worldTarget.y));
                                    System.setProperty("vs2.productionClientFixtureZ", Double.toString(worldTarget.z));
                                    System.setProperty("vs2.productionClientFixtureReady", "true");
                                    LOGGER.info("GATE_E_PRODUCTION_FIXTURE_CLIENT_READY player_tick={} target={},{},{}",
                                        player.tickCount, worldTarget.x, worldTarget.y, worldTarget.z);
                                }'''
local_publish = '''fixtureColliderNormalized = true;
                                if (productionSmokeFixture) {
                                    System.setProperty("vs2.productionClientFixtureCarriageId", Integer.toString(carriage.getId()));
                                    System.setProperty("vs2.productionClientFixtureLocalX", Double.toString(localTarget.x));
                                    System.setProperty("vs2.productionClientFixtureLocalY", Double.toString(localTarget.y));
                                    System.setProperty("vs2.productionClientFixtureLocalZ", Double.toString(localTarget.z));
                                    System.setProperty("vs2.productionClientFixtureReady", "true");
                                    LOGGER.info("GATE_E_PRODUCTION_FIXTURE_CLIENT_READY player_tick={} carriage_id={} local_target={},{},{} world_target={},{},{}",
                                        player.tickCount, carriage.getId(), localTarget.x, localTarget.y, localTarget.z,
                                        worldTarget.x, worldTarget.y, worldTarget.z);
                                }'''
if old_world_publish in source:
    source = source.replace(old_world_publish, local_publish, 1)
elif 'vs2.productionClientFixtureLocalX' not in source:
    client_anchor = 'fixtureColliderNormalized = true;'
    if client_anchor not in source:
        raise SystemExit("Phase 100 could not find final client collider fixture anchor")
    source = source.replace(client_anchor, local_publish, 1)

client_probe.write_text(source, encoding="utf-8")

server = server_probe.read_text(encoding="utf-8")
server_tick14 = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 14)) && !fixturePlayerChecked) {'
server_tick20 = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 20)) && !fixturePlayerChecked) {'
server_plain = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")) && !fixturePlayerChecked) {'
server_synced = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && java.lang.Boolean.getBoolean("vs2.productionClientFixtureReady"))) && !fixturePlayerChecked) {'
if server_synced not in server:
    if server_tick14 in server:
        server = server.replace(server_tick14, server_synced, 1)
    elif server_tick20 in server:
        server = server.replace(server_tick20, server_synced, 1)
    elif server_plain in server:
        server = server.replace(server_plain, server_synced, 1)
    else:
        raise SystemExit("Phase 100 could not find production server fixture guard")

old_sync_body = '''
                if (java.lang.Boolean.getBoolean("vs2.productionSmoke") && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")) {
                    val syncX = System.getProperty("vs2.productionClientFixtureX")?.toDoubleOrNull()
                    val syncY = System.getProperty("vs2.productionClientFixtureY")?.toDoubleOrNull()
                    val syncZ = System.getProperty("vs2.productionClientFixtureZ")?.toDoubleOrNull()
                    if (syncX != null && syncY != null && syncZ != null) {
                        fixturePlayerChecked = true
                        player.setPos(syncX, syncY, syncZ)
                        player.setDeltaMovement(net.minecraft.world.phys.Vec3(0.0, -0.08, 0.0))
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT target={},{},{} gravity_probe_y=-0.08", syncX, syncY, syncZ)
                        return@register
                    }
                }
'''
local_sync_body = '''
                if (java.lang.Boolean.getBoolean("vs2.productionSmoke") && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")) {
                    val syncCarriageId = System.getProperty("vs2.productionClientFixtureCarriageId")?.toIntOrNull()
                    val syncLocalX = System.getProperty("vs2.productionClientFixtureLocalX")?.toDoubleOrNull()
                    val syncLocalY = System.getProperty("vs2.productionClientFixtureLocalY")?.toDoubleOrNull()
                    val syncLocalZ = System.getProperty("vs2.productionClientFixtureLocalZ")?.toDoubleOrNull()
                    val syncToGlobal = carriage.javaClass.methods.firstOrNull { method ->
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
                }
'''
if old_sync_body in server:
    server = server.replace(old_sync_body, local_sync_body, 1)
elif 'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT' not in server:
    if server_synced not in server:
        raise SystemExit("Phase 100 lost synchronized server fixture guard")
    server = server.replace(server_synced, server_synced + local_sync_body, 1)
elif '// Production smoke must never fall through to the legacy nearest-carriage' not in server:
    previous_local_tail = '''                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)
                        return@register
                    }
                }
'''
    replacement_local_tail = '''                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)
                        return@register
                    }
                    // Production smoke must never fall through to the legacy nearest-carriage
                    // fixture while waiting for the exact client-selected carriage.
                    return@register
                }
'''
    if previous_local_tail not in server:
        raise SystemExit("Phase 100 could not harden existing local-frame sync tail")
    server = server.replace(previous_local_tail, replacement_local_tail, 1)

required = [
    'vs2.productionClientFixtureCarriageId',
    'vs2.productionClientFixtureLocalX', 'vs2.productionClientFixtureLocalY', 'vs2.productionClientFixtureLocalZ',
    'GATE_E_PRODUCTION_FIXTURE_CLIENT_READY', 'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT',
    'syncToGlobal.invoke(carriage, syncLocal, 0.0f)',
    'Production smoke must never fall through to the legacy nearest-carriage',
]
combined = source + server
missing = [token for token in required if token not in combined]
if missing:
    raise SystemExit("Phase 100 lost local-frame synchronization anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")

print("Phase 100: synchronized the test-only integrated-server fixture in the exact carriage-local frame and blocked sibling-carriage fallback; no production gameplay, train, or physics mutation")

# A caller that only needs Phase 100's synchronization prerequisite can suppress the
# descendant interaction chain. This avoids recursive 100 -> 101 -> ... -> 108 -> 100
# execution when world/client smoke enters the later cumulative chain through Phase 108.
if not globals().get("PHASE100_PREREQUISITE_ONLY", False):
    # Keep the native interaction experiment chained after deterministic fixture sync.
    phase101 = Path(__file__).with_name("prepare_vs2_26_2_phase101.py")
    exec(compile(phase101.read_text(encoding="utf-8"), str(phase101), "exec"))

    # Resolve the exact client-published carriage entity after Phase 100 has installed its
    # local-frame fixture block. Phase 104 is production-smoke-fixture-only.
    phase104 = Path(__file__).with_name("prepare_vs2_26_2_phase104.py")
    exec(compile(phase104.read_text(encoding="utf-8"), str(phase104), "exec"))
