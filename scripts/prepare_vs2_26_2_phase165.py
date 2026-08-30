#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #304 proved the carry/interaction/placement path remains healthy, but the
# twenty-tick walk fixture itself runs straight off the finite support surface: local X moves
# 2.500 -> 2.876 -> 3.485 and physical support is already gone before the later 2.238-block
# steps. Do not turn that harness-induced edge exit into a gameplay/physics workaround. Keep
# exercising ordinary movement keys for twenty ticks, but reverse the requested direction every
# tick so the fixture probes bounded locomotion instead of intentionally leaving the carriage.
# Validate accumulated local path length rather than final displacement, since a bounded
# oscillation can legitimately return near its start. This changes test input/proof only.
field_old = '''    private static net.minecraft.world.phys.Vec3 phase154WalkPreviousLocal;\n    private static boolean phase154WalkSupportHealthy = true;\n'''
field_new = '''    private static net.minecraft.world.phys.Vec3 phase154WalkPreviousLocal;\n    private static double phase165WalkPathDistance;\n    private static boolean phase154WalkSupportHealthy = true;\n'''
if "phase165WalkPathDistance" not in source:
    if field_old not in source:
        raise SystemExit("Phase 165 could not find Phase154 walk field anchor")
    source = source.replace(field_old, field_new, 1)

start_old = '''                            phase154WalkPreviousLocal = phase154Local;\n                            phase154WalkSupportHealthy = true;\n                            client.options.keyUp.setDown(true);\n'''
start_new = '''                            phase154WalkPreviousLocal = phase154Local;\n                            phase165WalkPathDistance = 0.0;\n                            phase154WalkSupportHealthy = true;\n                            client.options.keyUp.setDown(true);\n                            client.options.keyDown.setDown(false);\n'''
if "phase165WalkPathDistance = 0.0" not in source:
    if start_old not in source:
        raise SystemExit("Phase 165 could not find Phase154 walk-start input anchor")
    source = source.replace(start_old, start_new, 1)

sample_old = '''                            double phase154Step = phase154WalkPreviousLocal == null\n                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);\n                            phase154WalkPreviousLocal = phase154Local;\n                            if (player.tickCount <= phase154WalkStartTick + 20) {\n                                client.options.keyUp.setDown(true);\n                                LOGGER.info(\n                                    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE player_tick={} carriage_id={} local={} local_step={} on_ground={} broadphase={} support_healthy={} fixture_only=true",\n                                    player.tickCount, phase154Carriage.getId(), phase154Local, phase154Step,\n                                    player.onGround(), phase154Broadphase, phase154WalkSupportHealthy);\n                            } else {\n                                client.options.keyUp.setDown(false);\n                                double phase154LocalDistance = phase154WalkStartLocal == null\n                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);\n                                boolean phase154Confirmed = phase154WalkSupportHealthy\n                                    && phase154Carriage.getId() == phase154WalkCarriageId\n                                    && phase154Broadphase && player.onGround()\n                                    && phase154LocalDistance >= 0.20 && phase154LocalDistance <= 6.00;\n'''
sample_new = '''                            double phase154Step = phase154WalkPreviousLocal == null\n                                ? 0.0 : phase154Local.distanceTo(phase154WalkPreviousLocal);\n                            phase154WalkPreviousLocal = phase154Local;\n                            phase165WalkPathDistance += phase154Step;\n                            if (player.tickCount <= phase154WalkStartTick + 20) {\n                                boolean phase165Forward = ((player.tickCount - phase154WalkStartTick) & 1) == 0;\n                                client.options.keyUp.setDown(phase165Forward);\n                                client.options.keyDown.setDown(!phase165Forward);\n                                LOGGER.info(\n                                    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE player_tick={} carriage_id={} local={} local_step={} path_distance={} direction={} on_ground={} broadphase={} support_healthy={} fixture_only=true",\n                                    player.tickCount, phase154Carriage.getId(), phase154Local, phase154Step, phase165WalkPathDistance,\n                                    phase165Forward ? "forward" : "backward", player.onGround(), phase154Broadphase, phase154WalkSupportHealthy);\n                            } else {\n                                client.options.keyUp.setDown(false);\n                                client.options.keyDown.setDown(false);\n                                double phase154LocalDistance = phase154WalkStartLocal == null\n                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);\n                                boolean phase154Confirmed = phase154WalkSupportHealthy\n                                    && phase154Carriage.getId() == phase154WalkCarriageId\n                                    && phase154Broadphase && player.onGround()\n                                    && phase165WalkPathDistance >= 0.50 && phase165WalkPathDistance <= 8.00\n                                    && phase154LocalDistance <= 2.00;\n'''
if "path_distance={} direction={}" not in source:
    if sample_old not in source:
        raise SystemExit("Phase 165 could not find Phase154 walk-sample/proof anchor")
    source = source.replace(sample_old, sample_new, 1)

catch_old = '''                        client.options.keyUp.setDown(false);\n                        phase154WalkFinished = true;\n'''
catch_new = '''                        client.options.keyUp.setDown(false);\n                        client.options.keyDown.setDown(false);\n                        phase154WalkFinished = true;\n'''
if catch_new not in source:
    if catch_old not in source:
        raise SystemExit("Phase 165 could not find Phase154 exception cleanup anchor")
    source = source.replace(catch_old, catch_new, 1)

required = [
    "phase165WalkPathDistance",
    "phase165WalkPathDistance += phase154Step",
    "phase165Forward",
    "client.options.keyUp.setDown(phase165Forward)",
    "client.options.keyDown.setDown(!phase165Forward)",
    "path_distance={} direction={}",
    "phase165WalkPathDistance >= 0.50",
    "phase165WalkPathDistance <= 8.00",
    "phase154LocalDistance <= 2.00",
    "client.options.keyDown.setDown(false)",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 165 lost bounded-walk harness anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in sample_new:
        raise SystemExit("Phase 165 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 165: bounds fixture locomotion with alternating normal keys and path-distance proof")
