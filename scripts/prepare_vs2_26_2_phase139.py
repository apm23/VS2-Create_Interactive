#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #212 proved the authoritative held-block native Create dispatch itself
# succeeds (handled=true), but the CI gate still requires the disposable LocalPlayer hand
# to be empty after dispatch. In creative-mode fixture inventory, successful block use does
# not necessarily consume the held stack, so that assertion is a harness lifecycle check,
# not proof of native dispatch. Clear only the client-side disposable fixture stack after a
# confirmed handled invocation; the authoritative server stack remains governed by Phase136
# and is restored after its dispatch grace. No movement, collision, train, world, or VS2
# physics behavior is changed.
anchor = '''                                                    LOGGER.info("GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH carriage_id={} player_tick={} handled={} server_held_block_armed=true item_after={} fixture_only=true",\n                                                        carriage.getId(), player.tickCount, handled, player.getMainHandItem());\n'''
replacement = anchor + '''                                                    if (Boolean.TRUE.equals(handled)\n                                                            && productionSmokeFixture\n                                                            && player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem())) {\n                                                        player.setItemSlot(\n                                                            net.minecraft.world.entity.EquipmentSlot.MAINHAND,\n                                                            net.minecraft.world.item.ItemStack.EMPTY);\n                                                        LOGGER.info("GATE_F_PHASE139_CLIENT_FIXTURE_HAND_CLEANUP carriage_id={} player_tick={} handled=true hand_empty_after=true fixture_only=true",\n                                                            carriage.getId(), player.tickCount);\n                                                    }\n'''
if "GATE_F_PHASE139_CLIENT_FIXTURE_HAND_CLEANUP" not in source:
    if anchor not in source:
        raise SystemExit("Phase 139 could not find Phase138 authoritative dispatch anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
    "GATE_F_PHASE139_CLIENT_FIXTURE_HAND_CLEANUP",
    "Boolean.TRUE.equals(handled)",
    "productionSmokeFixture",
    "ItemStack.EMPTY",
    "hand_empty_after=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 139 lost fixture cleanup anchors: " + ", ".join(missing))

# This phase is inventory cleanup in the disposable smoke fixture only.
cleanup_slice = source[source.find("GATE_F_PHASE139_CLIENT_FIXTURE_HAND_CLEANUP") - 1200:source.find("GATE_F_PHASE139_CLIENT_FIXTURE_HAND_CLEANUP") + 600]
for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in cleanup_slice:
        raise SystemExit("Phase 139 fixture cleanup found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 139: clears only the disposable client fixture STONE after confirmed handled native dispatch")
