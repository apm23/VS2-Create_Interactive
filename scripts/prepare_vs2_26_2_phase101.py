#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #58 proved sustained Create-filtered carry (14 valid replay samples)
# and repeatedly produced concrete Create-native settled-ray hits, while the older
# Phase 101 probe emitted no entrypoint marker at all. The reason is structural: that
# probe was attached to the deeper synthetic-hit branch, which is not guaranteed to run
# even when Create's own earlier settled ray already has a valid moving-carriage target.
# Attach the disposable-world-only native right-click readiness/probe to that settled
# native-ray seam instead. No normal gameplay path can enter because productionSmokeFixture
# is false there; no packet, direct block use, train control, VS2 physics, or carry code is
# changed here.
field_anchor = '''    private static boolean fixtureClientNormalized;\n'''
field_replacement = '''    private static boolean fixtureClientNormalized;\n    private static boolean nativeRightClickProbeDispatched;\n'''
if "nativeRightClickProbeDispatched" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 101 could not find Gate E fixture field anchor")
    source = source.replace(field_anchor, field_replacement, 1)

settled_anchor = '''                                        LOGGER.info(
                                            "GATE_F_CREATE_NATIVE_RAY_SETTLED carriage_id={} player_tick={} {}",
                                            carriage.getId(), player.tickCount, settledNativeRayState);'''
settled_replacement = settled_anchor + '''
                                        boolean settledCreateNativeRayReady = settledNativeRayState.contains("hit=")
                                            && settledNativeRayState.contains("face=")
                                            && !settledNativeRayState.contains("miss");
                                        if (settledCreateNativeRayReady) {
                                            try {
                                                Class<?> nativeHandlerClass = Class.forName("com.zurrtum.create.client.content.contraptions.ContraptionHandlerClient");
                                                java.lang.reflect.Method settledExactRightClickMethod = null;
                                                for (java.lang.reflect.Method candidate : nativeHandlerClass.getMethods()) {
                                                    Class<?>[] params = candidate.getParameterTypes();
                                                    if (candidate.getName().equals("rightClickingOnContraptionsGetsHandledLocally")
                                                            && java.lang.reflect.Modifier.isStatic(candidate.getModifiers())
                                                            && candidate.getReturnType() == boolean.class
                                                            && params.length == 2
                                                            && params[0].getSimpleName().equals("Minecraft")
                                                            && params[1].getSimpleName().equals("InteractionHand")) {
                                                        settledExactRightClickMethod = candidate;
                                                        break;
                                                    }
                                                }
                                                boolean settledExactNativeRightClickEntrypoint = settledExactRightClickMethod != null;
                                                LOGGER.info(
                                                    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact={} target_match_ready={} readiness_source=create_native_ray_settled",
                                                    carriage.getId(), player.tickCount, settledExactNativeRightClickEntrypoint,
                                                    settledExactNativeRightClickEntrypoint && settledCreateNativeRayReady);
                                                if (productionSmokeFixture
                                                        && settledExactNativeRightClickEntrypoint
                                                        && player.getMainHandItem().isEmpty()
                                                        && !nativeRightClickProbeDispatched) {
                                                    nativeRightClickProbeDispatched = true;
                                                    Object handled = settledExactRightClickMethod.invoke(
                                                        null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                    LOGGER.info(
                                                        "GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=true handled={} hand_empty_after={} readiness_source=create_native_ray_settled",
                                                        carriage.getId(), player.tickCount, handled, player.getMainHandItem().isEmpty());
                                                    if (Boolean.TRUE.equals(handled)) {
                                                        LOGGER.info(
                                                            "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=create_native_ray_settled",
                                                            carriage.getId(), player.tickCount);
                                                    }
                                                }
                                            } catch (ReflectiveOperationException | RuntimeException exception) {
                                                LOGGER.info(
                                                    "GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=false error={} readiness_source=create_native_ray_settled",
                                                    carriage.getId(), player.tickCount, exception.getClass().getSimpleName());
                                            }
                                        }'''

if "readiness_source=create_native_ray_settled" not in source:
    if settled_anchor not in source:
        raise SystemExit("Phase 101 could not find Phase 97 settled native-ray anchor")
    source = source.replace(settled_anchor, settled_replacement, 1)

required = [
    'nativeRightClickProbeDispatched',
    'GATE_F_NATIVE_RIGHT_CLICK_PROBE',
    'GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED',
    'readiness_source=create_native_ray_settled',
    'boolean settledCreateNativeRayReady',
    'productionSmokeFixture',
    'java.lang.reflect.Modifier.isStatic(candidate.getModifiers())',
    'settledExactRightClickMethod.invoke(',
    'Boolean.TRUE.equals(handled)',
    'player.getMainHandItem().isEmpty()',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 101 lost settled native interaction probe anchors: " + ", ".join(missing))

for forbidden in [
    'ContraptionInteractionPacket', '.handlePlayerInteraction(',
    '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
    'player.setPos(', 'player.setDeltaMovement(',
]:
    if forbidden in settled_replacement:
        raise SystemExit("Phase 101 found forbidden direct interaction/physics mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 101: moved the disposable-world native right-click probe to Create's proven settled native-ray seam and emits an explicit confirmation only when Create returns handled=true; no normal-gameplay dispatch, train, carry, or VS2 physics path changed")
