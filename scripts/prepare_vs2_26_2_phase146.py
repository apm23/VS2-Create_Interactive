#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #234 proved the authoritative ServerPlayer was armed with STONE before
# the exact Create native ray, and later telemetry in the same client tick also saw STONE,
# yet the Phase138 dispatch guard was skipped. The only remaining guard unique to that path
# is the client inventory mirror check. Remove that timing-sensitive mirror prerequisite and
# mirror one STONE into LocalPlayer immediately before the fixture-only reflective dispatch.
# The authoritative server-arm handshake remains mandatory. No movement, train, world, or
# physics behavior is changed; Phase139/136 retain fixture inventory cleanup/restoration.
old_guard = '''                                                        && settledServerHeldBlockArmed
                                                        && player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem())
                                                        && !nativeRightClickProbeDispatched) {'''
new_guard = '''                                                        && settledServerHeldBlockArmed
                                                        && !nativeRightClickProbeDispatched) {'''
if old_guard in source:
    source = source.replace(old_guard, new_guard, 1)
elif "&& settledServerHeldBlockArmed\n                                                        && !nativeRightClickProbeDispatched)" not in source:
    raise SystemExit("Phase 146 could not find Phase138 held-block dispatch guard")

invoke = '''                                                    nativeRightClickProbeDispatched = true;
                                                    Object handled = settledExactRightClickMethod.invoke(
                                                        null, client, net.minecraft.world.InteractionHand.MAIN_HAND);'''
replacement = '''                                                    nativeRightClickProbeDispatched = true;
                                                    boolean phase146ClientMirrorInjected = !player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem());
                                                    if (phase146ClientMirrorInjected) {
                                                        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                                                            new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1));
                                                    }
                                                    Object handled = settledExactRightClickMethod.invoke(
                                                        null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                    LOGGER.info("GATE_F_PHASE146_HELD_BLOCK_NATIVE_DISPATCH carriage_id={} player_tick={} invoked=true handled={} client_mirror_injected={} item_after={} server_held_block_armed=true fixture_only=true",
                                                        carriage.getId(), player.tickCount, handled, phase146ClientMirrorInjected, player.getMainHandItem());'''
if "GATE_F_PHASE146_HELD_BLOCK_NATIVE_DISPATCH" not in source:
    if invoke not in source:
        raise SystemExit("Phase 146 could not find authoritative native invocation")
    source = source.replace(invoke, replacement, 1)

required = [
    "GATE_F_PHASE146_HELD_BLOCK_NATIVE_DISPATCH",
    "settledServerHeldBlockArmed",
    "phase146ClientMirrorInjected",
    "new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1)",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "nativeRightClickProbeDispatched",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 146 lost held-block dispatch anchors: " + ", ".join(missing))

for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in replacement:
        raise SystemExit("Phase 146 found forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 146: removes client inventory-sync race from fixture dispatch and mirrors STONE only immediately before exact native Create invocation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase147.py")), run_name="__main__")
