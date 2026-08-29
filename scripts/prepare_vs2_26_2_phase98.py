#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
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

# Production-world #44 proved the delayed fixture restores sustained carry and that
# Create's native ray, our independently-derived synthetic target, and the exact
# high-level right-click entrypoint all agree on a moving carriage block. Before any
# dispatch experiment, profile that exact native target and the player's main hand so
# we know whether the fixture is pointing at inert structure or an interactive block.
# Reflection only reads contraption block metadata; it never invokes interaction code.
profile_anchor = '''                                                                            nativeRayState = "hit=" + nativeHit.getBlockPos().toShortString()
                                                                                + ";face=" + nativeHit.getDirection()
                                                                                + ";target_match=" + nativeHit.getBlockPos().equals(syntheticContraptionHit.getBlockPos())
                                                                                + ";face_match=" + (nativeHit.getDirection() == syntheticContraptionHit.getDirection());'''
profile_replacement = profile_anchor + '''
                                                                            String targetStateProfile = "unresolved";
                                                                            try {
                                                                                java.lang.reflect.Method getContraptionMethod = carriage.getClass().getMethod("getContraption");
                                                                                Object contraptionObject = getContraptionMethod.invoke(carriage);
                                                                                java.lang.reflect.Method getBlocksMethod = contraptionObject.getClass().getMethod("getBlocks");
                                                                                Object blocksObject = getBlocksMethod.invoke(contraptionObject);
                                                                                Object blockInfoObject = blocksObject instanceof java.util.Map<?, ?> blockMap
                                                                                    ? blockMap.get(nativeHit.getBlockPos()) : null;
                                                                                if (blockInfoObject == null) {
                                                                                    targetStateProfile = "missing_block_info";
                                                                                } else {
                                                                                    java.lang.reflect.Method stateMethod = blockInfoObject.getClass().getMethod("state");
                                                                                    Object stateObject = stateMethod.invoke(blockInfoObject);
                                                                                    targetStateProfile = String.valueOf(stateObject);
                                                                                }
                                                                            } catch (ReflectiveOperationException | RuntimeException profileException) {
                                                                                targetStateProfile = "error=" + profileException.getClass().getSimpleName();
                                                                            }
                                                                            LOGGER.info(
                                                                                "GATE_F_INTERACTION_TARGET_PROFILE carriage_id={} player_tick={} target_block={} target_face={} state={} main_hand_empty={} main_hand={}",
                                                                                carriage.getId(), player.tickCount, nativeHit.getBlockPos(), nativeHit.getDirection(),
                                                                                targetStateProfile, player.getMainHandItem().isEmpty(), player.getMainHandItem());'''
if "GATE_F_INTERACTION_TARGET_PROFILE" not in source:
    if profile_anchor not in source:
        raise SystemExit("Phase 98 could not find Phase 97 native-hit profile anchor")
    source = source.replace(profile_anchor, profile_replacement, 1)

# Production-world #43 exposed a harness race rather than a carry regression: the
# one-shot support fixture was installed while the autonomous train was still in its
# stationary startup frame. At player tick 12 the saved carriage still reported zero
# motion; by tick 13 Create had advanced to sibling carriage entities roughly 14 blocks
# away, before Phase 85 had any non-zero motion sample to replay. Delay only the
# explicitly test-only production fixture until player tick 20 so normalization occurs
# after that startup discontinuity. Normal CI and all production gameplay paths are
# unchanged; this does not repeat/pin the player during movement.
old_client_fixture = 'if ((ciHarness || productionSmokeFixture) && !fixtureClientNormalized'
new_client_fixture = 'if ((ciHarness || (productionSmokeFixture && player.tickCount >= 20)) && !fixtureClientNormalized'
old_collider_fixture = 'if ((ciHarness || productionSmokeFixture) && !fixtureColliderNormalized'
new_collider_fixture = 'if ((ciHarness || (productionSmokeFixture && player.tickCount >= 20)) && !fixtureColliderNormalized'
if new_client_fixture not in source:
    if old_client_fixture not in source:
        raise SystemExit("Phase 98 could not find production client fixture guard")
    source = source.replace(old_client_fixture, new_client_fixture, 1)
if new_collider_fixture not in source:
    if old_collider_fixture not in source:
        raise SystemExit("Phase 98 could not find production collider fixture guard")
    source = source.replace(old_collider_fixture, new_collider_fixture, 1)

required = [
    'GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT',
    'GATE_F_INTERACTION_TARGET_PROFILE',
    'candidate.getName().equals("rightClickingOnContraptionsGetsHandledLocally")',
    'params[0].getSimpleName().equals("Minecraft")',
    'params[1].getSimpleName().equals("InteractionHand")',
    'nativeRayState.contains("target_match=true;face_match=true")',
    'getContraptionMethod.invoke(carriage)',
    'blockMap.get(nativeHit.getBlockPos())',
    'player.getMainHandItem().isEmpty()',
    '(productionSmokeFixture && player.tickCount >= 20)',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 98 lost native right-click/target-profile/fixture anchors: " + ", ".join(missing))

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

server = server_probe.read_text(encoding="utf-8")
old_server_fixture = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")) && !fixturePlayerChecked) {'
new_server_fixture = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 20)) && !fixturePlayerChecked) {'
if new_server_fixture not in server:
    if old_server_fixture not in server:
        raise SystemExit("Phase 98 could not find production server fixture guard")
    server = server.replace(old_server_fixture, new_server_fixture, 1)
if 'java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 20' not in server:
    raise SystemExit("Phase 98 lost delayed production server fixture anchor")
server_probe.write_text(server, encoding="utf-8")

print("Phase 98: pinned native right-click readiness, profiled the exact moving-train target read-only, and retained delayed test fixture timing; no interaction dispatch or gameplay mutation")
