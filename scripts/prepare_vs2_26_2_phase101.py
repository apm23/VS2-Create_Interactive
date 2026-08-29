#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #58 proved sustained Create-filtered carry and concrete native
# settled-ray hits. Runs #59/#61/#62 then proved the high-level Create right-click
# entrypoint can be invoked on a moving carriage and returns handled=true. Keep that
# disposable-world-only probe, and after confirmation inventory the same native
# handler's public placement/item/use/interaction-shaped methods read-only. This is
# the next safe step before supplying an item or attempting block placement.
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
                                                        java.util.List<String> placementSurface = new java.util.ArrayList<>();
                                                        for (java.lang.reflect.Method candidate : nativeHandlerClass.getMethods()) {
                                                            String lowerName = candidate.getName().toLowerCase(java.util.Locale.ROOT);
                                                            if (!(lowerName.contains("place")
                                                                    || lowerName.contains("item")
                                                                    || lowerName.contains("use")
                                                                    || lowerName.contains("right")
                                                                    || lowerName.contains("interact"))) {
                                                                continue;
                                                            }
                                                            StringBuilder signature = new StringBuilder(candidate.getName()).append('(');
                                                            Class<?>[] params = candidate.getParameterTypes();
                                                            for (int index = 0; index < params.length; index++) {
                                                                if (index > 0) signature.append(',');
                                                                signature.append(params[index].getSimpleName());
                                                            }
                                                            signature.append("): ").append(candidate.getReturnType().getSimpleName());
                                                            placementSurface.add(signature.toString());
                                                        }
                                                        java.util.Collections.sort(placementSurface);
                                                        LOGGER.info(
                                                            "GATE_F_NATIVE_PLACEMENT_SURFACE carriage_id={} player_tick={} methods={} count={} read_only=true",
                                                            carriage.getId(), player.tickCount, placementSurface, placementSurface.size());
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
    'GATE_F_NATIVE_PLACEMENT_SURFACE',
    'readiness_source=create_native_ray_settled',
    'boolean settledCreateNativeRayReady',
    'productionSmokeFixture',
    'java.lang.reflect.Modifier.isStatic(candidate.getModifiers())',
    'settledExactRightClickMethod.invoke(',
    'Boolean.TRUE.equals(handled)',
    'player.getMainHandItem().isEmpty()',
    'placementSurface.add(signature.toString())',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 101 lost settled native interaction/placement-surface anchors: " + ", ".join(missing))

for forbidden in [
    '.handlePlayerInteraction(', '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
    'player.setPos(', 'player.setDeltaMovement(', 'player.setItemSlot(',
]:
    if forbidden in settled_replacement:
        raise SystemExit("Phase 101 found forbidden direct placement/physics mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 101: confirmed disposable-world native moving-train right click and inventories the native placement/item/use interaction surface read-only before any item or placement mutation")
