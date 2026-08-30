#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #252 proved the exact Create-native ray can be a single tick. The ray at
# player tick 17 published the authoritative server-arm request, the integrated server armed
# STONE immediately afterwards, but there was no second settled-ray callback in which Phase152
# could observe the armed flag. Preserve that already-validated exact Method as a pending
# fixture target and consume it on the first later same-carriage stable-support sample after
# the authoritative server-arm flag becomes true. Production-world #255 then proved this retry
# path reaches handled=true, but unlike the direct Phase152 path it still left the disposable
# client fixture STONE in hand. Clear only that client fixture hand after handled dispatch so
# both native-dispatch paths expose the same postcondition; the authoritative server hand
# remains independently guarded/restored by Phase136.
#
# Production-world #340 proved a pending ray can be stale by the time the server arm becomes
# visible: tick 19 had an exact Create ray, tick 20 was a MISS, and the retry returned
# handled=false. Do not consume the global one-shot dispatch/completion latch for that
# unhandled attempt. This leaves the authoritative server arm alive and permits a later fresh
# exact settled ray (the same run observed fresh exact rays again at ticks 30/31) to use the
# normal Phase152 path. This is fixture-only handshake state; no movement, collision, train,
# world/contraption, schedule, or VS2 physics mutation is introduced.
field_anchor = '''    private static boolean nativeRightClickProbeDispatched;\n'''
field_insert = field_anchor + '''    private static java.lang.reflect.Method phase153PendingHeldBlockRightClickMethod;\n    private static int phase153PendingHeldBlockCarriageId = -1;\n    private static int phase153PendingHeldBlockRayTick = -1;\n'''
if "phase153PendingHeldBlockRightClickMethod" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 153 could not find native right-click fixture field anchor")
    source = source.replace(field_anchor, field_insert, 1)

entry_anchor = '''                                                LOGGER.info(
                                                    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact={} target_match_ready={} readiness_source=create_native_ray_settled",
                                                    carriage.getId(), player.tickCount, settledExactNativeRightClickEntrypoint,
                                                    settledExactNativeRightClickEntrypoint && settledCreateNativeRayReady);'''
entry_insert = entry_anchor + '''
                                                if (productionSmokeFixture
                                                        && settledCreateNativeRayReady
                                                        && settledExactNativeRightClickEntrypoint
                                                        && !nativeRightClickProbeDispatched) {
                                                    phase153PendingHeldBlockRightClickMethod = settledExactRightClickMethod;
                                                    phase153PendingHeldBlockCarriageId = carriage.getId();
                                                    phase153PendingHeldBlockRayTick = player.tickCount;
                                                    LOGGER.info("GATE_F_PHASE153_PENDING_NATIVE_RAY carriage_id={} player_tick={} pending=true server_armed={} fixture_only=true",
                                                        carriage.getId(), player.tickCount, Boolean.getBoolean("vs2.productionHeldBlockServerArmed"));
                                                }'''
if "GATE_F_PHASE153_PENDING_NATIVE_RAY" not in source:
    count = source.count(entry_anchor)
    if count == 0:
        raise SystemExit("Phase 153 could not find executed settled-ray entrypoint")
    source = source.replace(entry_anchor, entry_insert)

continuity_anchor = '''                    LOGGER.info(
                        "GATE_E_CARRIAGE_LOCAL_CONTINUITY player_tick={} carriage_id={} local_feet={} world_distance_sq={} broadphase={} on_ground={} baseline_frame={} read_only=true",'''
retry = '''                    if (productionSmokeFixture
                            && phase153PendingHeldBlockRightClickMethod != null
                            && phase153PendingHeldBlockCarriageId == localFrameCarriage.getId()
                            && baselineFrame
                            && broadphase
                            && player.onGround()
                            && Boolean.getBoolean("vs2.productionHeldBlockServerArmed")
                            && !nativeRightClickProbeDispatched) {
                        try {
                            boolean phase153ClientMirrorInjected = !player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem());
                            if (phase153ClientMirrorInjected) {
                                player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                                    new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1));
                            }
                            Object phase153Handled = phase153PendingHeldBlockRightClickMethod.invoke(
                                null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                            if (Boolean.TRUE.equals(phase153Handled)) {
                                nativeRightClickProbeDispatched = true;
                                System.setProperty("vs2.productionHeldBlockNativeDispatchCompleted", "true");
                                player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                                    net.minecraft.world.item.ItemStack.EMPTY);
                            }
                            LOGGER.info(
                                "GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=true handled={} hand_empty_after={} readiness_source=server_arm_retry server_held_block_armed=true pending_ray_tick={} phase153_retry=true fixture_hand_cleared_after_handled=true retry_remains_open_after_unhandled=true",
                                localFrameCarriage.getId(), player.tickCount, phase153Handled, player.getMainHandItem().isEmpty(), phase153PendingHeldBlockRayTick);
                            LOGGER.info(
                                "GATE_F_PHASE153_SERVER_ARM_RETRY_DISPATCH carriage_id={} player_tick={} pending_ray_tick={} invoked=true handled={} client_mirror_injected={} item_after={} one_shot_consumed={} fixture_only=true",
                                localFrameCarriage.getId(), player.tickCount, phase153PendingHeldBlockRayTick, phase153Handled, phase153ClientMirrorInjected, player.getMainHandItem(), Boolean.TRUE.equals(phase153Handled));
                            if (Boolean.TRUE.equals(phase153Handled)) {
                                LOGGER.info(
                                    "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=server_arm_retry",
                                    localFrameCarriage.getId(), player.tickCount);
                            }
                        } catch (ReflectiveOperationException | RuntimeException exception) {
                            LOGGER.info(
                                "GATE_F_PHASE153_SERVER_ARM_RETRY_DISPATCH carriage_id={} player_tick={} pending_ray_tick={} invoked=false error={} fixture_only=true",
                                localFrameCarriage.getId(), player.tickCount, phase153PendingHeldBlockRayTick, exception.getClass().getSimpleName());
                        } finally {
                            phase153PendingHeldBlockRightClickMethod = null;
                            phase153PendingHeldBlockCarriageId = -1;
                            phase153PendingHeldBlockRayTick = -1;
                        }
                    }
                    LOGGER.info(
                        "GATE_E_CARRIAGE_LOCAL_CONTINUITY player_tick={} carriage_id={} local_feet={} world_distance_sq={} broadphase={} on_ground={} baseline_frame={} read_only=true",'''
if "GATE_F_PHASE153_SERVER_ARM_RETRY_DISPATCH" not in source:
    if continuity_anchor not in source:
        raise SystemExit("Phase 153 could not find carriage continuity retry anchor")
    source = source.replace(continuity_anchor, retry, 1)

required = [
    "phase153PendingHeldBlockRightClickMethod",
    "GATE_F_PHASE153_PENDING_NATIVE_RAY",
    "GATE_F_PHASE153_SERVER_ARM_RETRY_DISPATCH",
    "GATE_F_NATIVE_RIGHT_CLICK_PROBE",
    "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED",
    "readiness_source=server_arm_retry",
    "vs2.productionHeldBlockServerArmed",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "phase153PendingHeldBlockCarriageId == localFrameCarriage.getId()",
    "baselineFrame",
    "broadphase",
    "player.onGround()",
    "nativeRightClickProbeDispatched",
    "fixture_hand_cleared_after_handled=true",
    "retry_remains_open_after_unhandled=true",
    "ItemStack.EMPTY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 153 lost pending-ray retry anchors: " + ", ".join(missing))

for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in retry:
        raise SystemExit("Phase 153 introduced forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 153: retries a pending exact Create ray after authoritative server arm without consuming the one-shot latch on handled=false, then permits a later fresh exact ray; fixture handshake only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase154.py")), run_name="__main__")
