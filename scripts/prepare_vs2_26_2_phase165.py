#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #306 reached the real train and showed the alternating-key harness itself
# is still too aggressive for the finite fixture: the first visible locomotion response arrives
# several ticks after input starts, so opposite key requests overlap the delayed response and the
# walk proof sees multi-block local excursions despite grounded/broadphase support. Do not answer
# that with a gameplay/physics workaround. Emit exactly one ordinary forward-key pulse at walk
# start, release both horizontal keys on every following sample, and observe carry/support for the
# remaining twenty-tick window. This isolates a real player locomotion impulse from sustained test
# input while retaining the strict Phase156/160 frame guard. Harness only; no player position,
# velocity, collision, train/world state, or VS2 physics mutation is introduced.
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
input_new = '''                            if (player.tickCount <= phase154WalkStartTick + 20) {\n                                client.options.keyUp.setDown(false);\n                                client.options.keyDown.setDown(false);\n                                LOGGER.info(\n'''
if "phase165WalkPathDistance += phase154Step" in source and "client.options.keyDown.setDown(false);\n                                LOGGER.info(" not in source:
    if source.count(input_old) != 1:
        raise SystemExit("Phase 165 expected exactly one cumulative walk input branch")
    source = source.replace(input_old, input_new, 1)

proof_old = '''                            } else {\n                                client.options.keyUp.setDown(false);\n                                double phase154LocalDistance = phase154WalkStartLocal == null\n                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);\n                                boolean phase154Confirmed = phase154WalkSupportHealthy\n                                    && phase154Carriage.getId() == phase154WalkCarriageId\n                                    && phase154Broadphase && player.onGround()\n                                    && phase154LocalDistance >= 0.20 && phase154LocalDistance <= 6.00;\n'''
proof_new = '''                            } else {\n                                client.options.keyUp.setDown(false);\n                                client.options.keyDown.setDown(false);\n                                double phase154LocalDistance = phase154WalkStartLocal == null\n                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);\n                                boolean phase154Confirmed = phase154WalkSupportHealthy\n                                    && phase154Carriage.getId() == phase154WalkCarriageId\n                                    && phase154Broadphase && player.onGround()\n                                    && phase165WalkPathDistance >= 0.20 && phase165WalkPathDistance <= 4.00\n                                    && phase154LocalDistance <= 3.00;\n'''
if "phase165WalkPathDistance >= 0.20" not in source:
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
    "client.options.keyUp.setDown(false)",
    "client.options.keyDown.setDown(false)",
    "phase165WalkPathDistance >= 0.20",
    "phase165WalkPathDistance <= 4.00",
    "phase154LocalDistance <= 3.00",
    "GATE_E_PHASE156_WALK_FRAME_GUARD",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 165 lost single-pulse walk anchors: " + ", ".join(missing))

patch_text = field_new + start_new + path_new + input_new + proof_new + catch_new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 165 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 165: emits one normal forward-key pulse then observes twenty ticks of carry/support")
