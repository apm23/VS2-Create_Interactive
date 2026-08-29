#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #51 proved sustained Create-filtered carry (12 samples / 76.85 blocks),
# a stable Create-native ray target, an empty main hand, and the exact native Create
# right-click entrypoint on Copycats carriage structure. The next safe functional step is
# a single invocation in the disposable production-smoke world only. It is impossible in
# normal gameplay because productionSmokeFixture is false there. We do not synthesize
# packets or call block.use directly: Create remains the owner of interaction dispatch.
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
                                                                if (productionSmokeFixture
                                                                        && exactNativeRightClickEntrypoint
                                                                        && nativeRayState.contains("target_match=true;face_match=true")
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
                                                                            LOGGER.info("GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=true handled={} hand_empty_after={}",
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
    # Existing cumulative fixture code legitimately contains player setPos/delta movement,
    # so only reject direct gameplay mutation if it appears in the newly inserted probe body.
    if forbidden in replacement:
        raise SystemExit("Phase 101 found forbidden direct interaction/physics mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 101: invoked Create's native moving-contraption right-click entrypoint once in the disposable production-smoke fixture only; no normal-gameplay dispatch path changed")
