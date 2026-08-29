#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"

source = client_probe.read_text(encoding="utf-8")

# Production-world #53 proved that a boolean-only barrier is still nondeterministic:
# the client completed its real simplified-collider fixture, then the integrated-server
# fixture independently selected a different carriage surface and its authoritative
# reposition invalidated physical support after the first carry sample. Publish the
# exact client collider target through test-only JVM properties and make the server use
# that same target. This only runs with productionSmokeFixture and never changes normal
# gameplay, train controls, VS2 physics, or the production carry algorithm.
old_early_ready = '''fixtureClientNormalized = true;
                                if (productionSmokeFixture) {
                                    System.setProperty("vs2.productionClientFixtureReady", "true");
                                    LOGGER.info("GATE_E_PRODUCTION_FIXTURE_CLIENT_READY player_tick={}", player.tickCount);
                                }'''
if old_early_ready in source:
    source = source.replace(old_early_ready, 'fixtureClientNormalized = true;', 1)

client_anchor = 'fixtureColliderNormalized = true;'
client_replacement = '''fixtureColliderNormalized = true;
                                if (productionSmokeFixture) {
                                    System.setProperty("vs2.productionClientFixtureX", Double.toString(worldTarget.x));
                                    System.setProperty("vs2.productionClientFixtureY", Double.toString(worldTarget.y));
                                    System.setProperty("vs2.productionClientFixtureZ", Double.toString(worldTarget.z));
                                    System.setProperty("vs2.productionClientFixtureReady", "true");
                                    LOGGER.info("GATE_E_PRODUCTION_FIXTURE_CLIENT_READY player_tick={} target={},{},{}",
                                        player.tickCount, worldTarget.x, worldTarget.y, worldTarget.z);
                                }'''
if 'vs2.productionClientFixtureX' not in source:
    if client_anchor not in source:
        raise SystemExit("Phase 100 could not find final client collider fixture anchor")
    source = source.replace(client_anchor, client_replacement, 1)

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

sync_body = '''
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
if 'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT' not in server:
    if server_synced not in server:
        raise SystemExit("Phase 100 lost synchronized server fixture guard")
    server = server.replace(server_synced, server_synced + sync_body, 1)

required = [
    'vs2.productionClientFixtureX', 'vs2.productionClientFixtureY', 'vs2.productionClientFixtureZ',
    'GATE_E_PRODUCTION_FIXTURE_CLIENT_READY', 'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT',
]
combined = source + server
missing = [token for token in required if token not in combined]
if missing:
    raise SystemExit("Phase 100 lost coordinate synchronization anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")

print("Phase 100: synchronized the test-only integrated-server fixture to the exact LocalPlayer collider target; no production gameplay, train, or physics mutation")

# Keep the native interaction experiment chained after deterministic fixture sync.
phase101 = Path(__file__).with_name("prepare_vs2_26_2_phase101.py")
exec(compile(phase101.read_text(encoding="utf-8"), str(phase101), "exec"))
