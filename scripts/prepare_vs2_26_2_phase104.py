#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
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
                        System.setProperty("vs2.productionServerFixtureReady", "true")
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                            syncCarriageId, syncLocalX, syncLocalY, syncLocalZ, syncWorld.x, syncWorld.y, syncWorld.z)
                        return@register
                    }
                    logger.info("GATE_D_PRODUCTION_FIXTURE_WAITING_FOR_CLIENT_CARRIAGE carriage_id={} level_resolved={} entity_resolved={} transform_resolved={}",
                        syncCarriageId, syncLevel != null, syncCarriage != null, syncToGlobal != null)
                    return@register
'''
if old in server:
    server = server.replace(old, new, 1)
elif 'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true' not in server:
    raise SystemExit("Phase 104 could not find Phase 100 carriage-match fixture block")
elif 'vs2.productionServerFixtureReady' not in server:
    ready_anchor = '''                        fixturePlayerChecked = true
                        player.setPos(syncWorld.x, syncWorld.y, syncWorld.z)
                        player.setDeltaMovement(net.minecraft.world.phys.Vec3(0.0, -0.08, 0.0))
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true'''
    ready_replacement = '''                        fixturePlayerChecked = true
                        player.setPos(syncWorld.x, syncWorld.y, syncWorld.z)
                        player.setDeltaMovement(net.minecraft.world.phys.Vec3(0.0, -0.08, 0.0))
                        System.setProperty("vs2.productionServerFixtureReady", "true")
                        logger.info("GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true'''
    if ready_anchor not in server:
        raise SystemExit("Phase 104 could not add server-ready handshake")
    server = server.replace(ready_anchor, ready_replacement, 1)

required = [
    'GATE_D_PRODUCTION_FIXTURE_SYNCED_TO_CLIENT carriage_id={} resolved_by_id=true',
    'GATE_D_PRODUCTION_FIXTURE_WAITING_FOR_CLIENT_CARRIAGE',
    'method.name == "getEntity"',
    'syncGetEntity.invoke(syncLevel, syncCarriageId)',
    'syncToGlobal.invoke(syncCarriage, syncLocal, 0.0f)',
    'vs2.productionServerFixtureReady',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 104 lost exact-carriage fixture anchors: " + ", ".join(missing))
server_probe.write_text(server, encoding="utf-8")

# Production-world #73 proved the exact-id server resolver works, but also exposed a
# second harness race: the server consumed the local target roughly one second later,
# after the moving train had advanced about 41 blocks. The LocalPlayer was therefore
# still standing at the client frame from publication time while the ServerPlayer was
# correctly rebased to the same local cell in the later server frame. Once the server
# announces that it consumed the target, rebase LocalPlayer exactly once from the same
# published local coordinates using the *current client carriage frame*. This avoids
# world-coordinate staleness while keeping all mutation test-fixture-only.
client = client_probe.read_text(encoding="utf-8")
anchor = '''            boolean phase81PhysicalSupport = false;
            double phase81VerticalGap = Double.NaN;'''
rebase = '''            if (productionSmokeFixture
                    && java.lang.Boolean.getBoolean("vs2.productionServerFixtureReady")
                    && !java.lang.Boolean.getBoolean("vs2.productionClientServerFrameApplied")) {
                int syncCarriageId = java.lang.Integer.getInteger("vs2.productionClientFixtureCarriageId", Integer.MIN_VALUE);
                if (carriage.getId() == syncCarriageId) {
                    String syncLocalXText = System.getProperty("vs2.productionClientFixtureLocalX");
                    String syncLocalYText = System.getProperty("vs2.productionClientFixtureLocalY");
                    String syncLocalZText = System.getProperty("vs2.productionClientFixtureLocalZ");
                    try {
                        double syncLocalX = Double.parseDouble(syncLocalXText);
                        double syncLocalY = Double.parseDouble(syncLocalYText);
                        double syncLocalZ = Double.parseDouble(syncLocalZText);
                        java.lang.reflect.Method syncToGlobal = null;
                        for (java.lang.reflect.Method method : carriage.getClass().getMethods()) {
                            Class<?>[] params = method.getParameterTypes();
                            if (method.getName().equals("toGlobalVector") && params.length == 2
                                    && params[0] == net.minecraft.world.phys.Vec3.class
                                    && params[1] == float.class) {
                                syncToGlobal = method;
                                break;
                            }
                        }
                        if (syncToGlobal != null) {
                            net.minecraft.world.phys.Vec3 syncLocal = new net.minecraft.world.phys.Vec3(syncLocalX, syncLocalY, syncLocalZ);
                            net.minecraft.world.phys.Vec3 syncWorld = (net.minecraft.world.phys.Vec3) syncToGlobal.invoke(carriage, syncLocal, 0.0f);
                            player.setPos(syncWorld.x, syncWorld.y, syncWorld.z);
                            player.setDeltaMovement(new net.minecraft.world.phys.Vec3(0.0, -0.08, 0.0));
                            System.setProperty("vs2.productionClientServerFrameApplied", "true");
                            LOGGER.info(
                                "GATE_E_PRODUCTION_FIXTURE_REBASED_AFTER_SERVER carriage_id={} player_tick={} local_target={},{},{} world_target={},{},{} gravity_probe_y=-0.08",
                                syncCarriageId, player.tickCount, syncLocalX, syncLocalY, syncLocalZ,
                                syncWorld.x, syncWorld.y, syncWorld.z);
                        }
                    } catch (ReflectiveOperationException | RuntimeException syncException) {
                        LOGGER.info(
                            "GATE_E_PRODUCTION_FIXTURE_REBASE_ERROR carriage_id={} player_tick={} type={}",
                            syncCarriageId, player.tickCount, syncException.getClass().getSimpleName());
                    }
                }
            }

            boolean phase81PhysicalSupport = false;
            double phase81VerticalGap = Double.NaN;'''
if 'GATE_E_PRODUCTION_FIXTURE_REBASED_AFTER_SERVER' not in client:
    if anchor not in client:
        raise SystemExit("Phase 104 could not find Phase 81 support-continuity anchor for client rebase")
    client = client.replace(anchor, rebase, 1)

client_required = [
    'GATE_E_PRODUCTION_FIXTURE_REBASED_AFTER_SERVER',
    'vs2.productionClientServerFrameApplied',
    'java.lang.Boolean.getBoolean("vs2.productionServerFixtureReady")',
    'carriage.getId() == syncCarriageId',
    'syncToGlobal.invoke(carriage, syncLocal, 0.0f)',
]
client_missing = [token for token in client_required if token not in client]
if client_missing:
    raise SystemExit("Phase 104 lost client frame-rebase anchors: " + ", ".join(client_missing))
client_probe.write_text(client, encoding="utf-8")

print("Phase 104: resolved the exact client-selected carriage by id and rebased the test-only LocalPlayer after authoritative server fixture sync; no production gameplay, train, or physics mutation")

# Production-world #77 proved Create's setBlock path is server-only. Chain the exact
# ServerLevel same-cell/same-entry canary only after Phase 104 has installed the
# authoritative exact-carriage server fixture block.
phase106 = Path(__file__).with_name("prepare_vs2_26_2_phase106.py")
exec(compile(phase106.read_text(encoding="utf-8"), str(phase106), "exec"))

# The exact native placement target can only be resolved after Phase 104 created the
# authoritative ServerLevel entity resolver and Phase 106 installed its same-cell
# server canary. Keep this read-only probe ordered after both prerequisites.
phase109 = Path(__file__).with_name("prepare_vs2_26_2_phase109.py")
exec(compile(phase109.read_text(encoding="utf-8"), str(phase109), "exec"))
