#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #312 proved the first post-pulse discontinuity is not compatibility replay:
# carryReplayPlayerTick was still 16 while tick 28 moved the LocalPlayer 8.889862 blocks and the
# carriage itself moved only 3.389730 blocks. Existing Create collider telemetry simultaneously
# reported a 5.500132-block requested/allowed horizontal collision vector. Before changing any
# gameplay behavior, correlate the active carriage's own getContactPointMotion() with that Create
# collider request and the player's vanilla delta movement on every bounded walk sample. This is
# read-only diagnostics only; no player, collision, train, world, or VS2/Create physics mutation.
anchor = '''                            if (player.tickCount <= phase154WalkStartTick + 20) {
                                LOGGER.info(
                                    "GATE_E_PHASE163_WALK_WORLD_FRAME'''
insert = '''                            if (player.tickCount <= phase154WalkStartTick + 20) {
                                String phase167ContactMotionState = "unresolved";
                                try {
                                    java.lang.reflect.Method phase167ContactMotionMethod = null;
                                    Class<?> phase167ContactOwner = phase154Carriage.getClass();
                                    while (phase167ContactOwner != null && phase167ContactMotionMethod == null) {
                                        try {
                                            phase167ContactMotionMethod = phase167ContactOwner.getDeclaredMethod(
                                                "getContactPointMotion", net.minecraft.world.phys.Vec3.class);
                                        } catch (NoSuchMethodException ignored) {
                                            phase167ContactOwner = phase167ContactOwner.getSuperclass();
                                        }
                                    }
                                    if (phase167ContactMotionMethod == null) {
                                        phase167ContactMotionState = "missing";
                                    } else {
                                        phase167ContactMotionMethod.setAccessible(true);
                                        Object phase167MotionObject = phase167ContactMotionMethod.invoke(
                                            phase154Carriage, player.position());
                                        if (phase167MotionObject instanceof net.minecraft.world.phys.Vec3 phase167Motion) {
                                            phase167ContactMotionState = phase167Motion.x + "," + phase167Motion.y + "," + phase167Motion.z;
                                        } else {
                                            phase167ContactMotionState = "unexpected=" + String.valueOf(phase167MotionObject);
                                        }
                                    }
                                } catch (ReflectiveOperationException | RuntimeException phase167Exception) {
                                    phase167ContactMotionState = "error=" + phase167Exception.getClass().getSimpleName();
                                }
                                LOGGER.info(
                                    "GATE_E_PHASE167_WALK_NATIVE_MOTION player_tick={} carriage_id={} contact_point_motion={} player_delta={} local_step={} replay_tick={} key_up={} key_down={} on_ground={} broadphase={} read_only=true",
                                    player.tickCount, phase154Carriage.getId(), phase167ContactMotionState,
                                    player.getDeltaMovement(), phase154Step, carryReplayPlayerTick,
                                    client.options.keyUp.isDown(), client.options.keyDown.isDown(), player.onGround(), phase154Broadphase);
                                LOGGER.info(
                                    "GATE_E_PHASE163_WALK_WORLD_FRAME'''

if "GATE_E_PHASE167_WALK_NATIVE_MOTION" not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Phase 167 expected exactly one Phase163 walk world-frame sample anchor")
    source = source.replace(anchor, insert, 1)

required = [
    "GATE_E_PHASE167_WALK_NATIVE_MOTION",
    "getContactPointMotion",
    "phase154Carriage",
    "player.position()",
    "player.getDeltaMovement()",
    "carryReplayPlayerTick",
    "GATE_E_PHASE163_WALK_WORLD_FRAME",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 167 lost native-motion correlation anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in insert:
        raise SystemExit("Phase 167 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 167: traces active-carriage contact motion beside walk discontinuities read-only")
