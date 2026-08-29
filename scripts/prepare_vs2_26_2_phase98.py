#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #41 proved sustained carry plus a stable Create-native ray target,
# and Phase 97 proved that target matches the independently-derived local block/face.
# Before invoking any interaction path, pin the exact high-level Create right-click
# entrypoint that owns dispatch. Reflection only: do not call it, handle interaction,
# send packets, mutate inventory, world, train, or physics state.
anchor = '''                                                                LOGGER.info(
                                                                    "GATE_F_CREATE_NATIVE_RAY carriage_id={} player_tick={} {}",
                                                                    carriage.getId(), player.tickCount, nativeRayState);'''
replacement = anchor + '''
                                                                boolean exactNativeRightClickEntrypoint = false;
                                                                try {
                                                                    Class<?> nativeHandlerClass = Class.forName("com.zurrtum.create.client.content.contraptions.ContraptionHandlerClient");
                                                                    for (java.lang.reflect.Method candidate : nativeHandlerClass.getMethods()) {
                                                                        Class<?>[] params = candidate.getParameterTypes();
                                                                        if (candidate.getName().equals("rightClickingOnContraptionsGetsHandledLocally")
                                                                                && candidate.getReturnType() == boolean.class
                                                                                && params.length == 2
                                                                                && params[0].getSimpleName().equals("Minecraft")
                                                                                && params[1].getSimpleName().equals("InteractionHand")) {
                                                                            exactNativeRightClickEntrypoint = true;
                                                                            break;
                                                                        }
                                                                    }
                                                                } catch (ReflectiveOperationException | RuntimeException exception) {
                                                                    LOGGER.info(
                                                                        "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact=false error={}",
                                                                        carriage.getId(), player.tickCount, exception.getClass().getSimpleName());
                                                                }
                                                                LOGGER.info(
                                                                    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact={} target_match_ready={}",
                                                                    carriage.getId(), player.tickCount, exactNativeRightClickEntrypoint,
                                                                    nativeRayState.contains("target_match=true;face_match=true"));'''

if "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT" not in source:
    if anchor not in source:
        raise SystemExit("Phase 98 could not find Phase 97 deep native-ray anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT',
    'candidate.getName().equals("rightClickingOnContraptionsGetsHandledLocally")',
    'params[0].getSimpleName().equals("Minecraft")',
    'params[1].getSimpleName().equals("InteractionHand")',
    'nativeRayState.contains("target_match=true;face_match=true")',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 98 lost native right-click readiness anchors: " + ", ".join(missing))

for forbidden in [
    'rightClickingOnContraptionsGetsHandledLocally(client',
    '.handlePlayerInteraction(',
    'handleMethod.invoke(',
    'ContraptionInteractionPacket',
    '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
]:
    if forbidden in source:
        raise SystemExit("Phase 98 found forbidden interaction dispatch/mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 98: pinned Create native right-click entrypoint and exact-match readiness via reflection only; no interaction dispatch or mutation")
