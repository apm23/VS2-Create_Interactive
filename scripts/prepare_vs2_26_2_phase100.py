#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"

source = client_probe.read_text(encoding="utf-8")

# Production-world #49 proved that a fixed tick threshold is not a reliable
# synchronization barrier under Xvfb: the integrated server can advance the train
# several seconds before the Render-thread LocalPlayer reaches the same fixture tick.
# The client and integrated server share one JVM, so use a test-only system property
# as an explicit barrier. The LocalPlayer still normalizes only once; it merely signals
# that it has completed before the server-side fixture is allowed to normalize.
client_anchor = 'fixtureClientNormalized = true;'
client_replacement = '''fixtureClientNormalized = true;
                                if (productionSmokeFixture) {
                                    System.setProperty("vs2.productionClientFixtureReady", "true");
                                    LOGGER.info("GATE_E_PRODUCTION_FIXTURE_CLIENT_READY player_tick={}", player.tickCount);
                                }'''
if 'vs2.productionClientFixtureReady' not in source:
    if client_anchor not in source:
        raise SystemExit("Phase 100 could not find client fixture completion anchor")
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

if 'java.lang.Boolean.getBoolean("vs2.productionClientFixtureReady")' not in server:
    raise SystemExit("Phase 100 lost client/server production fixture barrier")
server_probe.write_text(server, encoding="utf-8")

print("Phase 100: synchronized the test-only integrated-server production fixture behind LocalPlayer fixture completion; no production gameplay or interaction mutation")

# Production-world #51 is green through sustained moving-train carry and exact native
# interaction targeting. Chain the next disposable-world-only native interaction probe
# after this synchronization barrier so production-world's final explicit Phase 98 pass
# actually installs it. Normal gameplay remains untouched because Phase 101 is guarded
# by vs2.productionSmokeFixture at runtime.
phase101 = Path(__file__).with_name("prepare_vs2_26_2_phase101.py")
exec(compile(phase101.read_text(encoding="utf-8"), str(phase101), "exec"))
