#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #257 proves stationary carriage-local continuity, native Create interaction,
# and authoritative moving-cell placement. The next safe gap is functional walking: drive the
# normal client forward key for a short bounded interval after the exact authoritative moving
# cell is visibly present on the client, then verify the player actually changed position in
# the same moving carriage-local frame without losing ground/support. Phase118 intentionally
# delays only its final exact-sync completion marker for eight ticks, giving this normal-key
# fixture a bounded observation window before the workflow terminates the client. This is
# smoke-fixture input only; it does not set player position/velocity, alter collision response,
# train state, world blocks, or VS2/Create physics.
field_anchor = '''    private static boolean nativeRightClickProbeDispatched;\n'''
field_insert = field_anchor + '''    private static boolean phase154WalkStarted;\n    private static boolean phase154WalkFinished;\n    private static int phase154WalkStartTick = -1;\n    private static int phase154WalkCarriageId = -1;\n    private static net.minecraft.world.phys.Vec3 phase154WalkStartLocal;\n    private static net.minecraft.world.phys.Vec3 phase154WalkPreviousLocal;\n    private static boolean phase154WalkSupportHealthy = true;\n'''
if "phase154WalkStarted" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 154 could not find fixture field anchor")
    source = source.replace(field_anchor, field_insert, 1)

anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
probe = '''            if (productionSmokeFixture
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementExactCellPresent")
                    && !phase154WalkFinished) {
                net.minecraft.world.entity.Entity phase154Carriage = null;
                if (carryBaselineCarriageId != Integer.MIN_VALUE) {
                    phase154Carriage = client.level.getEntity(carryBaselineCarriageId);
                }
                if (phase154Carriage != null
                        && "create:carriage_contraption".equals(
                            net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(phase154Carriage.getType()).toString())) {
                    try {
                        java.lang.reflect.Method phase154ToLocal = phase154Carriage.getClass().getMethod(
                            "toLocalVector", net.minecraft.world.phys.Vec3.class, float.class);
                        net.minecraft.world.phys.Vec3 phase154Local = (net.minecraft.world.phys.Vec3) phase154ToLocal.invoke(
                            phase154Carriage, player.position(), 0.0f);
                        boolean phase154Broadphase = phase154Carriage.getBoundingBox().inflate(2.0)
                            .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                        boolean phase154SupportNow = phase154Broadphase && player.onGround()
                            && phase154Carriage.getId() == carryBaselineCarriageId;

                        if (!phase154WalkStarted && phase154SupportNow) {
                            phase154WalkStarted = true;
                            phase154WalkStartTick = player.tickCount;
                            phase154WalkCarriageId = phase154Carriage.getId();
                            phase154WalkStartLocal = phase154Local;
                            phase154WalkPreviousLocal = phase154Local;
                            phase154WalkSupportHealthy = true;
                            client.options.keyUp.setDown(true);
                            LOGGER.info(
                                "GATE_E_PHASE154_FIXTURE_WALK_START player_tick={} carriage_id={} local_start={} on_ground=true broadphase=true exact_cell_present=true fixture_only=true",
                                player.tickCount, phase154WalkCarriageId, phase154WalkStartLocal);
                        } else if (phase154WalkStarted) {
                            if (phase154Carriage.getId() != phase154WalkCarriageId || !phase154SupportNow) {
                                phase154WalkSupportHealthy = false;
                            }
                            double phase154Step = phase154WalkPreviousLocal == null
                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);
                            phase154WalkPreviousLocal = phase154Local;
                            if (player.tickCount <= phase154WalkStartTick + 5) {
                                client.options.keyUp.setDown(true);
                                LOGGER.info(
                                    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE player_tick={} carriage_id={} local={} local_step={} on_ground={} broadphase={} support_healthy={} fixture_only=true",
                                    player.tickCount, phase154Carriage.getId(), phase154Local, phase154Step,
                                    player.onGround(), phase154Broadphase, phase154WalkSupportHealthy);
                            } else {
                                client.options.keyUp.setDown(false);
                                double phase154LocalDistance = phase154WalkStartLocal == null
                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);
                                boolean phase154Confirmed = phase154WalkSupportHealthy
                                    && phase154Carriage.getId() == phase154WalkCarriageId
                                    && phase154Broadphase && player.onGround()
                                    && phase154LocalDistance >= 0.05 && phase154LocalDistance <= 1.50;
                                phase154WalkFinished = true;
                                System.setProperty("vs2.productionFixtureWalkConfirmed", Boolean.toString(phase154Confirmed));
                                LOGGER.info(
                                    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED player_tick={} carriage_id={} local_start={} local_end={} local_distance={} on_ground={} broadphase={} support_healthy={} confirmed={} fixture_only=true",
                                    player.tickCount, phase154Carriage.getId(), phase154WalkStartLocal, phase154Local,
                                    phase154LocalDistance, player.onGround(), phase154Broadphase,
                                    phase154WalkSupportHealthy, phase154Confirmed);
                            }
                        }
                    } catch (ReflectiveOperationException | RuntimeException phase154Exception) {
                        client.options.keyUp.setDown(false);
                        phase154WalkFinished = true;
                        System.setProperty("vs2.productionFixtureWalkConfirmed", "false");
                        LOGGER.info(
                            "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED player_tick={} confirmed=false error={} fixture_only=true",
                            player.tickCount, phase154Exception.getClass().getSimpleName());
                    }
                }
            }

''' + anchor
if "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED" not in source:
    if anchor not in source:
        raise SystemExit("Phase 154 could not find Gate E client-state anchor")
    source = source.replace(anchor, probe, 1)

required = [
    "phase154WalkStarted",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "vs2.productionNativePlacementExactCellPresent",
    "vs2.productionFixtureWalkConfirmed",
    "client.options.keyUp.setDown(true)",
    "client.options.keyUp.setDown(false)",
    "phase154LocalDistance >= 0.05",
    "phase154LocalDistance <= 1.50",
    "phase154WalkSupportHealthy",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 154 lost bounded walk-fixture anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in probe:
        raise SystemExit("Phase 154 introduced forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 154: drives a bounded fixture-only forward-key walk once the authoritative client cell is present and verifies same-carriage local movement without support loss")
