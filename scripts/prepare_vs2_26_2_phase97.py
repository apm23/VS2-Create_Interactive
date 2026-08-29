#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase 97 must remain cumulative because Phase 96 chains directly into it from a
# pristine prepared source. First restore the proven runtime interaction inventory,
# then extend it with Create's own read-only contraption ray helper. No interaction
# dispatch, packet, placement, or gameplay mutation is allowed here.
assign_anchor = '''                                                            LOGGER.info(
                                                                "GATE_F_SYNTHETIC_HIT_EPHEMERAL_ASSIGN carriage_id={} player_tick={} assigned_identity={} restored_identity={} original_type={} synthetic_type={}",
                                                                carriage.getId(), player.tickCount, assignedIdentity, restoredIdentity,
                                                                originalClientHit == null ? "null" : originalClientHit.getType(),
                                                                syntheticContraptionHit.getType());'''
api_block = assign_anchor + '''
                                                            if (player.tickCount <= 40) {
                                                                StringBuilder interactionApi = new StringBuilder();
                                                                java.util.LinkedHashSet<String> signatures = new java.util.LinkedHashSet<>();
                                                                boolean exactHandlePlayerInteraction = false;
                                                                Object apiOwner = carriage;
                                                                for (java.lang.reflect.Method method : apiOwner.getClass().getMethods()) {
                                                                    String lower = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                    if (!(lower.contains("interact") || lower.contains("use")
                                                                            || lower.contains("block") || lower.contains("hit")
                                                                            || lower.contains("handle") || lower.contains("place")
                                                                            || lower.contains("contraption"))) continue;
                                                                    Class<?>[] params = method.getParameterTypes();
                                                                    if (method.getName().equals("handlePlayerInteraction")
                                                                            && method.getReturnType() == boolean.class
                                                                            && params.length == 4
                                                                            && params[0].getSimpleName().equals("Player")
                                                                            && params[1].getSimpleName().equals("BlockPos")
                                                                            && params[2].getSimpleName().equals("Direction")
                                                                            && params[3].getSimpleName().equals("InteractionHand")) {
                                                                        exactHandlePlayerInteraction = true;
                                                                    }
                                                                    StringBuilder sig = new StringBuilder(apiOwner.getClass().getSimpleName())
                                                                        .append('.').append(method.getName()).append('(');
                                                                    for (int pi = 0; pi < params.length; pi++) {
                                                                        if (pi > 0) sig.append(',');
                                                                        sig.append(params[pi].getSimpleName());
                                                                    }
                                                                    sig.append("):").append(method.getReturnType().getSimpleName());
                                                                    signatures.add(sig.toString());
                                                                }
                                                                for (String sig : signatures) {
                                                                    if (interactionApi.length() > 0) interactionApi.append('|');
                                                                    interactionApi.append(sig);
                                                                }
                                                                LOGGER.info(
                                                                    "GATE_F_CONTRAPTION_INTERACTION_API carriage_id={} player_tick={} methods={}",
                                                                    carriage.getId(), player.tickCount,
                                                                    interactionApi.length() == 0 ? "none" : interactionApi.toString());
                                                                LOGGER.info(
                                                                    "GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction={} target_block={} target_face={} hand=MAIN_HAND",
                                                                    carriage.getId(), player.tickCount, exactHandlePlayerInteraction,
                                                                    syntheticContraptionHit.getBlockPos(), syntheticContraptionHit.getDirection());
                                                            }'''

if "GATE_F_CONTRAPTION_INTERACTION_API" not in source:
    if assign_anchor not in source:
        raise SystemExit("Phase 97 could not find Phase 96 ephemeral assignment anchor")
    source = source.replace(assign_anchor, api_block, 1)
elif "GATE_F_INTERACTION_DISPATCH_CANDIDATE" not in source:
    raise SystemExit("Phase 97 found incomplete interaction API telemetry")

dispatch_anchor = '''                                                                LOGGER.info(
                                                                    "GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction={} target_block={} target_face={} hand=MAIN_HAND",
                                                                    carriage.getId(), player.tickCount, exactHandlePlayerInteraction,
                                                                    syntheticContraptionHit.getBlockPos(), syntheticContraptionHit.getDirection());'''
native_block = dispatch_anchor + '''
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
    if dispatch_anchor not in source:
        raise SystemExit("Phase 97 could not find restored dispatch-candidate anchor")
    source = source.replace(dispatch_anchor, native_block, 1)

required = [
    'GATE_F_CONTRAPTION_INTERACTION_API',
    'GATE_F_INTERACTION_DISPATCH_CANDIDATE',
    'GATE_F_CREATE_NATIVE_RAY',
    'method.getName().equals("handlePlayerInteraction")',
    'candidate.getName().equals("rayTraceContraption")',
    'rayMethod.invoke(null, nativeOrigin, nativeTarget, carriage)',
    'target_match=',
    'face_match=',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 97 lost cumulative native ray anchors: " + ", ".join(missing))

for forbidden in [
    '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
    'carriage.getContraption()', '.handlePlayerInteraction(',
    'handleMethod.invoke(', 'ContraptionInteractionPacket',
]:
    if forbidden in source:
        raise SystemExit("Phase 97 found forbidden interaction dispatch/mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 97: restored cumulative interaction API inventory and added Create native ray validation; read-only, no dispatch or mutation")
