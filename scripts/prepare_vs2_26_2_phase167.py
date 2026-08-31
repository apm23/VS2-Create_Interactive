#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #312 added read-only native-motion correlation to the bounded walk sample.
# Phase165 now holds ordinary forward input through one input-sampling interval and bounds the
# finite-world proof to twelve ticks, so this diagnostic must follow that harness seam instead of
# rewriting it back to the historical +20/keyUp=false form. Telemetry remains read-only.
anchor = '''                            if (player.tickCount <= phase154WalkStartTick + 12) {
                                boolean phase165InputPulse = player.tickCount <= phase154WalkStartTick + 1;
                                client.options.keyUp.setDown(phase165InputPulse);
                                client.options.keyDown.setDown(false);
                                LOGGER.info(
                                    "GATE_E_PHASE163_WALK_WORLD_FRAME'''
insert = '''                            if (player.tickCount <= phase154WalkStartTick + 12) {
                                boolean phase165InputPulse = player.tickCount <= phase154WalkStartTick + 1;
                                client.options.keyUp.setDown(phase165InputPulse);
                                client.options.keyDown.setDown(false);
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
        raise SystemExit("Phase 167 expected exactly one final Phase165/163 sampled-input walk anchor")
    source = source.replace(anchor, insert, 1)

required = [
    "GATE_E_PHASE167_WALK_NATIVE_MOTION",
    "getContactPointMotion",
    "phase154Carriage",
    "player.position()",
    "player.getDeltaMovement()",
    "carryReplayPlayerTick",
    "phase154WalkStartTick + 12",
    "phase165InputPulse",
    "client.options.keyUp.setDown(phase165InputPulse)",
    "client.options.keyDown.setDown(false)",
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
print("Phase 167: traces active-carriage contact motion beside the sampled-input walk window; read-only only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase168.py")), run_name="__main__")
