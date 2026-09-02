#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
source = client_probe.read_text(encoding="utf-8")
cumulative_prepared = "GATE_E_PHASE130_REPLAY_GUARD" in source

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

# Profile the exact native target and main hand read-only. Also inventory the exact
# vanilla client held-item placement entrypoint so the next fixture can exercise the
# player's normal block-use path instead of mutating the contraption map directly.
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
                                                                                targetStateProfile, player.getMainHandItem().isEmpty(), player.getMainHandItem());
                                                                            boolean exactHeldBlockUseEntrypoint = false;
                                                                            String heldBlockUseSignature = "missing";
                                                                            Object gameModeObject = client.gameMode;
                                                                            if (gameModeObject != null) {
                                                                                for (java.lang.reflect.Method candidate : gameModeObject.getClass().getMethods()) {
                                                                                    Class<?>[] params = candidate.getParameterTypes();
                                                                                    if (candidate.getName().equals("useItemOn")
                                                                                            && params.length == 3
                                                                                            && params[0].getSimpleName().equals("LocalPlayer")
                                                                                            && params[1].getSimpleName().equals("InteractionHand")
                                                                                            && params[2].getSimpleName().equals("BlockHitResult")) {
                                                                                        exactHeldBlockUseEntrypoint = true;
                                                                                        heldBlockUseSignature = candidate.getName() + "("
                                                                                            + params[0].getSimpleName() + ","
                                                                                            + params[1].getSimpleName() + ","
                                                                                            + params[2].getSimpleName() + "):"
                                                                                            + candidate.getReturnType().getSimpleName();
                                                                                        break;
                                                                                    }
                                                                                }
                                                                            }
                                                                            LOGGER.info(
                                                                                "GATE_F_PLAYER_BLOCK_PLACEMENT_ENTRYPOINT carriage_id={} player_tick={} exact={} signature={} target_ready={} main_hand_empty={} read_only=true",
                                                                                carriage.getId(), player.tickCount, exactHeldBlockUseEntrypoint, heldBlockUseSignature,
                                                                                nativeHit.getBlockPos() != null, player.getMainHandItem().isEmpty());'''
if "GATE_F_INTERACTION_TARGET_PROFILE" not in source:
    if profile_anchor not in source:
        raise SystemExit("Phase 98 could not find Phase 97 native-hit profile anchor")
    source = source.replace(profile_anchor, profile_replacement, 1)

# On the first cumulative pass, narrow the production-only fixture to tick 14. A later
# explicit production-world Phase 98 pass can occur after Phase 130 has structurally
# rewritten these guards; in that state the Phase 98 telemetry is already installed and
# the fixed-tick guard must not be searched/reapplied.
old_client_fixture_20 = 'if ((ciHarness || (productionSmokeFixture && player.tickCount >= 20)) && !fixtureClientNormalized'
new_client_fixture = 'if ((ciHarness || (productionSmokeFixture && player.tickCount >= 14)) && !fixtureClientNormalized'
old_client_fixture = 'if ((ciHarness || productionSmokeFixture) && !fixtureClientNormalized'
old_collider_fixture_20 = 'if ((ciHarness || (productionSmokeFixture && player.tickCount >= 20)) && !fixtureColliderNormalized'
new_collider_fixture = 'if ((ciHarness || (productionSmokeFixture && player.tickCount >= 14)) && !fixtureColliderNormalized'
old_collider_fixture = 'if ((ciHarness || productionSmokeFixture) && !fixtureColliderNormalized'
if not cumulative_prepared:
    if new_client_fixture not in source:
        if old_client_fixture_20 in source:
            source = source.replace(old_client_fixture_20, new_client_fixture, 1)
        elif old_client_fixture in source:
            source = source.replace(old_client_fixture, new_client_fixture, 1)
        else:
            raise SystemExit("Phase 98 could not find production client fixture guard")
    if new_collider_fixture not in source:
        if old_collider_fixture_20 in source:
            source = source.replace(old_collider_fixture_20, new_collider_fixture, 1)
        elif old_collider_fixture in source:
            source = source.replace(old_collider_fixture, new_collider_fixture, 1)
        else:
            raise SystemExit("Phase 98 could not find production collider fixture guard")

required = [
    'GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT',
    'GATE_F_INTERACTION_TARGET_PROFILE',
    'GATE_F_PLAYER_BLOCK_PLACEMENT_ENTRYPOINT',
    'candidate.getName().equals("rightClickingOnContraptionsGetsHandledLocally")',
    'candidate.getName().equals("useItemOn")',
    'params[0].getSimpleName().equals("Minecraft")',
    'params[1].getSimpleName().equals("InteractionHand")',
    'params[2].getSimpleName().equals("BlockHitResult")',
    'nativeRayState.contains("target_match=true;face_match=true")',
    'getContraptionMethod.invoke(carriage)',
    'blockMap.get(nativeHit.getBlockPos())',
    'player.getMainHandItem().isEmpty()',
    'read_only=true',
]
if not cumulative_prepared:
    required.append('(productionSmokeFixture && player.tickCount >= 14)')
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 98 lost native right-click/held-block-entrypoint/target-profile/fixture anchors: " + ", ".join(missing))

# The production workflow deliberately reruns Phase 98 after all cumulative phases are
# installed. On that second pass, later read-only packet telemetry (Phase 140+) is expected
# to contain names such as ContraptionInteractionPacket. Keep the original whole-source
# audit on the first pass; on the cumulative re-entry audit only Phase 98's own injected
# snippets so later telemetry cannot masquerade as a Phase 98 mutation.
audit_source = source if not cumulative_prepared else replacement + profile_replacement
for forbidden in [
    'rightClickingOnContraptionsGetsHandledLocally(client',
    '.handlePlayerInteraction(',
    'handleMethod.invoke(',
    'ContraptionInteractionPacket',
    '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
]:
    if forbidden in audit_source:
        raise SystemExit("Phase 98 found forbidden interaction dispatch/mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")

server = server_probe.read_text(encoding="utf-8")
old_server_fixture_20 = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 20)) && !fixturePlayerChecked) {'
new_server_fixture = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 14)) && !fixturePlayerChecked) {'
old_server_fixture = 'if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")) && !fixturePlayerChecked) {'
if not cumulative_prepared:
    if new_server_fixture not in server:
        if old_server_fixture_20 in server:
            server = server.replace(old_server_fixture_20, new_server_fixture, 1)
        elif old_server_fixture in server:
            server = server.replace(old_server_fixture, new_server_fixture, 1)
        else:
            raise SystemExit("Phase 98 could not find production server fixture guard")
    if 'java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && player.tickCount >= 14' not in server:
        raise SystemExit("Phase 98 lost narrowed production server fixture anchor")
server_probe.write_text(server, encoding="utf-8")

if cumulative_prepared:
    print("Phase 98: cumulative Phase 130 already prepared; retained existing native interaction/held-block entrypoint telemetry without reapplying obsolete fixed-tick fixture guards")
    runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_m1_input_timing.py")), run_name="__main__")
    runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_m1_wall_fixture_window.py")), run_name="__main__")
    runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase132.py")), run_name="__main__")
else:
    print("Phase 98: retained read-only native interaction/held-block entrypoint profiling and narrowed the one-shot production fixture to tick 14 after startup discontinuity; no interaction dispatch or gameplay mutation")
