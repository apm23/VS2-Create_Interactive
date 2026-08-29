#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #54 proved sustained Create-filtered carry and a stable Create-native
# moving-carriage hit, but the older synthetic scanner selected a different local block.
# The high-level Create entrypoint performs its own native raycast, so synthetic equality
# must not gate this disposable-world-only functional probe. Require an exact method,
# a concrete Create-native hit+face, and an empty main hand; never synthesize packets or
# call block.use directly. Normal gameplay cannot enter this path because the fixture
# property is false there.
field_anchor = '''    private static boolean fixtureClientNormalized;\n'''
field_replacement = '''    private static boolean fixtureClientNormalized;\n    private static boolean nativeRightClickProbeDispatched;\n'''
if "nativeRightClickProbeDispatched" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 101 could not find Gate E fixture field anchor")
    source = source.replace(field_anchor, field_replacement, 1)

anchor = '''                                                                LOGGER.info(
                                                                    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact={} target_match_ready={}",
                                                                    carriage.getId(), player.tickCount, exactNativeRightClickEntrypoint,
                                                                    nativeRayState.contains("target_match=true;face_match=true"));'''
replacement = anchor + '''
                                                                boolean createNativeRayReady = nativeRayState.contains("hit=")
                                                                    && nativeRayState.contains("face=")
                                                                    && !nativeRayState.contains("miss");
                                                                if (exactNativeRightClickEntrypoint && createNativeRayReady) {
                                                                    LOGGER.info(
                                                                        "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact=true target_match_ready=true readiness_source=create_native_ray synthetic_match={}",
                                                                        carriage.getId(), player.tickCount,
                                                                        nativeRayState.contains("target_match=true;face_match=true"));
                                                                }
                                                                if (productionSmokeFixture
                                                                        && exactNativeRightClickEntrypoint
                                                                        && createNativeRayReady
                                                                        && player.getMainHandItem().isEmpty()
                                                                        && !nativeRightClickProbeDispatched) {
                                                                    nativeRightClickProbeDispatched = true;
                                                                    try {
                                                                        Class<?> nativeHandlerClass = Class.forName("com.zurrtum.create.client.content.contraptions.ContraptionHandlerClient");
                                                                        java.lang.reflect.Method exactMethod = null;
                                                                        for (java.lang.reflect.Method candidate : nativeHandlerClass.getMethods()) {
                                                                            Class<?>[] params = candidate.getParameterTypes();
                                                                            if (candidate.getName().equals("rightClickingOnContraptionsGetsHandledLocally")
                                                                                    && java.lang.reflect.Modifier.isStatic(candidate.getModifiers())
                                                                                    && candidate.getReturnType() == boolean.class
                                                                                    && params.length == 2
                                                                                    && params[0].getSimpleName().equals("Minecraft")
                                                                                    && params[1].getSimpleName().equals("InteractionHand")) {
                                                                                exactMethod = candidate;
                                                                                break;
                                                                            }
                                                                        }
                                                                        if (exactMethod == null) {
                                                                            LOGGER.info("GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=false reason=method_not_static_or_missing",
                                                                                carriage.getId(), player.tickCount);
                                                                        } else {
                                                                            Object handled = exactMethod.invoke(null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                                            LOGGER.info("GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=true handled={} hand_empty_after={} readiness_source=create_native_ray",
                                                                                carriage.getId(), player.tickCount, handled, player.getMainHandItem().isEmpty());
                                                                        }
                                                                    } catch (ReflectiveOperationException | RuntimeException exception) {
                                                                        LOGGER.info("GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=false error={}",
                                                                            carriage.getId(), player.tickCount, exception.getClass().getSimpleName());
                                                                    }
                                                                }'''

if "GATE_F_NATIVE_RIGHT_CLICK_PROBE" not in source:
    if anchor not in source:
        raise SystemExit("Phase 101 could not find Phase 98 native right-click readiness anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'nativeRightClickProbeDispatched',
    'GATE_F_NATIVE_RIGHT_CLICK_PROBE',
    'readiness_source=create_native_ray',
    'boolean createNativeRayReady',
    'productionSmokeFixture',
    'java.lang.reflect.Modifier.isStatic(candidate.getModifiers())',
    'exactMethod.invoke(null, client, net.minecraft.world.InteractionHand.MAIN_HAND)',
    'player.getMainHandItem().isEmpty()',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 101 lost native interaction probe anchors: " + ", ".join(missing))

# Keep the experiment narrow: exactly Create's native high-level entrypoint, one main-hand
# invocation, and only behind the disposable production-smoke fixture. No direct packet,
# block-use, attack, placement, train control, VS2 physics, or player carry mutation here.
for forbidden in [
    'ContraptionInteractionPacket', '.handlePlayerInteraction(',
    '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
    'player.setPos(', 'player.setDeltaMovement(',
]:
    if forbidden in replacement:
        raise SystemExit("Phase 101 found forbidden direct interaction/physics mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 101: gated one disposable-world Create native right-click probe on Create's own concrete moving-carriage ray target, independent of the synthetic scanner; no normal-gameplay dispatch path changed")
