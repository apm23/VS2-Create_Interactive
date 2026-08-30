#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #182 proved the exact vanilla held-block entrypoint exists and the
# Create-native moving-contraption right-click handler is already handled=true with an
# empty hand. Exercise the same native Create handler once with a disposable STONE stack
# in the production smoke fixture only. Restore the original main-hand stack immediately
# after invocation. This is a bounded functional probe, not production inventory/carry/
# physics behavior, and it does not directly mutate the contraption block map.
if "GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE" not in source:
    anchor = '''                                                    Object handled = settledExactRightClickMethod.invoke(
                                                        null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                    LOGGER.info(
                                                        "GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=true handled={} hand_empty_after={} readiness_source=create_native_ray_settled",
                                                        carriage.getId(), player.tickCount, handled, player.getMainHandItem().isEmpty());'''
    if anchor not in source:
        raise SystemExit("Phase 132 could not find confirmed native right-click invocation anchor")
    replacement = anchor + '''
                                                    net.minecraft.world.item.ItemStack phase132OriginalMainHand = player.getMainHandItem().copy();
                                                    net.minecraft.world.item.ItemStack phase132ProbeStack = new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1);
                                                    Object phase132HeldBlockHandled = null;
                                                    String phase132HeldBlockError = "none";
                                                    try {
                                                        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase132ProbeStack);
                                                        phase132HeldBlockHandled = settledExactRightClickMethod.invoke(
                                                            null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                    } catch (ReflectiveOperationException | RuntimeException phase132Exception) {
                                                        phase132HeldBlockError = phase132Exception.getClass().getSimpleName();
                                                    } finally {
                                                        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase132OriginalMainHand);
                                                    }
                                                    LOGGER.info(
                                                        "GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE carriage_id={} player_tick={} invoked=true item=stone handled={} error={} restored_main_hand={} fixture_only=true",
                                                        carriage.getId(), player.tickCount, phase132HeldBlockHandled, phase132HeldBlockError,
                                                        player.getMainHandItem());'''
    source = source.replace(anchor, replacement, 1)

required = [
    "GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE",
    "new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1)",
    "settledExactRightClickMethod.invoke(",
    "EquipmentSlot.MAINHAND",
    "phase132OriginalMainHand",
    "fixture_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 132 lost held-block native probe anchors: " + ", ".join(missing))

# No direct contraption/world mutation is allowed in this probe. The only mutation is the
# temporary fixture main-hand stack around Create's own native interaction handler.
for forbidden in ["setBlock(", ".put(", ".remove(", "player.setPos(", "player.setDeltaMovement(", ".teleport"]:
    if forbidden in source[source.index("GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE") - 2500:source.index("GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE") + 1200]:
        raise SystemExit("Phase 132 found forbidden direct mutation near native held-block probe: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 132: probes Create native moving-contraption interaction once with fixture-only held STONE and restores main hand; no direct block/physics mutation")
