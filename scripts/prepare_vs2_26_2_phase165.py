#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #304 proved the carry/interaction/placement path remains healthy, but the
# twenty-tick walk fixture itself runs straight off the finite support surface. Bound the test
# input by alternating ordinary forward/backward keys and validate accumulated local path length.
# Phase156/160 rewrites the walk frame guard before this phase runs, so patch only stable Phase154
# seams instead of matching the pre-Phase156 walk block wholesale. Test harness only; no player
# position/vector, collision, train/world, or VS2 physics mutation is introduced.
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

path_old = '''                            phase154WalkPreviousLocal = phase154Local;\n                            if (player.tickCount <= phase154WalkStartTick + 20) {\n'''
path_new = '''                            phase154WalkPreviousLocal = phase154Local;\n                            phase165WalkPathDistance += phase154Step;\n                            if (player.tickCount <= phase154WalkStartTick + 20) {\n'''
if "phase165WalkPathDistance += phase154Step" not in source:
    if source.count(path_old) != 1:
        raise SystemExit("Phase 165 expected exactly one cumulative walk-sample tail")
    source = source.replace(path_old, path_new, 1)

input_old = '''                            if (player.tickCount <= phase154WalkStartTick + 20) {\n                                client.options.keyUp.setDown(true);\n                                LOGGER.info(\n'''
input_new = '''                            if (player.tickCount <= phase154WalkStartTick + 20) {\n                                boolean phase165Forward = ((player.tickCount - phase154WalkStartTick) & 1) == 0;\n                                client.options.keyUp.setDown(phase165Forward);\n                                client.options.keyDown.setDown(!phase165Forward);\n                                LOGGER.info(\n'''
if "boolean phase165Forward" not in source:
    if source.count(input_old) != 1:
        raise SystemExit("Phase 165 expected exactly one cumulative walk input branch")
    source = source.replace(input_old, input_new, 1)

proof_old = '''                            } else {\n                                client.options.keyUp.setDown(false);\n                                double phase154LocalDistance = phase154WalkStartLocal == null\n                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);\n                                boolean phase154Confirmed = phase154WalkSupportHealthy\n                                    && phase154Carriage.getId() == phase154WalkCarriageId\n                                    && phase154Broadphase && player.onGround()\n                                    && phase154LocalDistance >= 0.20 && phase154LocalDistance <= 6.00;\n'''
proof_new = '''                            } else {\n                                client.options.keyUp.setDown(false);\n                                client.options.keyDown.setDown(false);\n                                double phase154LocalDistance = phase154WalkStartLocal == null\n                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);\n                                boolean phase154Confirmed = phase154WalkSupportHealthy\n                                    && phase154Carriage.getId() == phase154WalkCarriageId\n                                    && phase154Broadphase && player.onGround()\n                                    && phase165WalkPathDistance >= 0.50 && phase165WalkPathDistance <= 8.00\n                                    && phase154LocalDistance <= 2.00;\n'''
if "phase165WalkPathDistance >= 0.50" not in source:
    if source.count(proof_old) != 1:
        raise SystemExit("Phase 165 expected exactly one cumulative walk completion branch")
    source = source.replace(proof_old, proof_new, 1)

catch_old = '''                        client.options.keyUp.setDown(false);\n                        phase154WalkFinished = true;\n'''
catch_new = '''                        client.options.keyUp.setDown(false);\n                        client.options.keyDown.setDown(false);\n                        phase154WalkFinished = true;\n'''
if catch_new not in source:
    if source.count(catch_old) != 1:
        raise SystemExit("Phase 165 expected exactly one Phase154 exception cleanup anchor")
    source = source.replace(catch_old, catch_new, 1)

required = [
    "phase165WalkPathDistance",
    "phase165WalkPathDistance = 0.0",
    "phase165WalkPathDistance += phase154Step",
    "boolean phase165Forward",
    "client.options.keyUp.setDown(phase165Forward)",
    "client.options.keyDown.setDown(!phase165Forward)",
    "phase165WalkPathDistance >= 0.50",
    "phase165WalkPathDistance <= 8.00",
    "phase154LocalDistance <= 2.00",
    "client.options.keyDown.setDown(false)",
    "GATE_E_PHASE156_WALK_FRAME_GUARD",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 165 lost bounded-walk cumulative anchors: " + ", ".join(missing))

patch_text = field_new + start_new + path_new + input_new + proof_new + catch_new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 165 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 165: bounds fixture locomotion with alternating normal keys and cumulative-guard-safe path proof")
