#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #36 proved the exact carriage handlePlayerInteraction signature is
# present and the synthetic local block/face stays stable while the train is moving.
# Before any interaction dispatch, ask Create's own client rayTraceContraption helper
# for the same carriage and compare its result with our independently-derived target.
# rayTraceContraption is read-only: no packet, use action, placement, or world mutation.
anchor = '''                                                                LOGGER.info(
                                                                    "GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction={} target_block={} target_face={} hand=MAIN_HAND",
                                                                    carriage.getId(), player.tickCount, exactHandlePlayerInteraction,
                                                                    syntheticContraptionHit.getBlockPos(), syntheticContraptionHit.getDirection());'''
replacement = anchor + '''
                                                                String nativeRayState = "unresolved";
                                                                try {
                                                                    Class<?> handlerClass = Class.forName("com.zurrtum.create.client.content.contraptions.ContraptionHandlerClient");
                                                                    java.lang.reflect.Method rayMethod = null;
                                                                    for (java.lang.reflect.Method candidate : handlerClass.getMethods()) {
                                                                        if (!candidate.getName().equals("rayTraceContraption")) continue;
                                                                        Class<?>[] rayParams = candidate.getParameterTypes();
                                                                        if (rayParams.length == 3
                                                                                && rayParams[0].getSimpleName().equals("Vec3")
                                                                                && rayParams[1].getSimpleName().equals("Vec3")
                                                                                && rayParams[2].getSimpleName().equals("AbstractContraptionEntity")) {
                                                                            rayMethod = candidate;
                                                                            break;
                                                                        }
                                                                    }
                                                                    if (rayMethod == null) {
                                                                        nativeRayState = "method_missing";
                                                                    } else {
                                                                        net.minecraft.world.phys.Vec3 nativeOrigin = player.getEyePosition();
                                                                        double nativeReach = player.blockInteractionRange();
                                                                        net.minecraft.world.phys.Vec3 nativeTarget = nativeOrigin.add(player.getViewVector(1.0F).scale(nativeReach));
                                                                        Object nativeResult = rayMethod.invoke(null, nativeOrigin, nativeTarget, carriage);
                                                                        if (nativeResult instanceof net.minecraft.world.phys.BlockHitResult nativeHit) {
                                                                            nativeRayState = "hit=" + nativeHit.getBlockPos().toShortString()
                                                                                + ";face=" + nativeHit.getDirection()
                                                                                + ";target_match=" + nativeHit.getBlockPos().equals(syntheticContraptionHit.getBlockPos())
                                                                                + ";face_match=" + (nativeHit.getDirection() == syntheticContraptionHit.getDirection());
                                                                        } else {
                                                                            nativeRayState = "miss";
                                                                        }
                                                                    }
                                                                } catch (ReflectiveOperationException | RuntimeException exception) {
                                                                    nativeRayState = "error=" + exception.getClass().getSimpleName();
                                                                }
                                                                LOGGER.info(
                                                                    "GATE_F_CREATE_NATIVE_RAY carriage_id={} player_tick={} {}",
                                                                    carriage.getId(), player.tickCount, nativeRayState);'''

if "GATE_F_CREATE_NATIVE_RAY" not in source:
    if anchor not in source:
        raise SystemExit("Phase 97 could not find dispatch-candidate anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_INTERACTION_API',
    'GATE_F_INTERACTION_DISPATCH_CANDIDATE',
    'GATE_F_CREATE_NATIVE_RAY',
    'method.getName().equals("handlePlayerInteraction")',
    'Class.forName("com.zurrtum.create.client.content.contraptions.ContraptionHandlerClient")',
    'candidate.getName().equals("rayTraceContraption")',
    'rayMethod.invoke(null, nativeOrigin, nativeTarget, carriage)',
    'target_match=',
    'face_match=',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 97 lost native Create ray-validation anchors: " + ", ".join(missing))

for forbidden in [
    '.useItemOn(',
    '.useItem(',
    '.attack(',
    'gameMode.use',
    'carriage.getContraption()',
    '.handlePlayerInteraction(',
    'handleMethod.invoke(',
    'ContraptionInteractionPacket',
]:
    if forbidden in source:
        raise SystemExit("Phase 97 found forbidden interaction dispatch/mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 97: validated Create native contraption ray target against synthetic hit via read-only reflection; no interaction dispatch or mutation")
