#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #197 proved the client-side native Create held-STONE dispatch is handled,
# but with all direct setBlock/client-map shortcuts disabled no authoritative new cell appears.
# The held-block probe only equips LocalPlayer; integrated ServerPlayer can therefore still
# be empty-handed when Create's native interaction reaches the server. Synchronize only the
# disposable fixture inventory during the post-carry interaction window, then restore it.
# This does not place blocks directly and does not alter player motion, train control, or VS2 physics.

vars_anchor = '''        var playerOnEnvelopeAtStart = false
'''
vars_insert = vars_anchor + '''        var phase138OriginalMainHand: net.minecraft.world.item.ItemStack? = null
        var phase138ServerHandArmed = false
        var phase138ServerHandRestored = false
'''
if "phase138OriginalMainHand" not in server:
    if vars_anchor not in server:
        raise SystemExit("Phase 136 could not find GateD fixture-state variable anchor")
    server = server.replace(vars_anchor, vars_insert, 1)

throttle = '''            if (ticks % 20L != 0L) return@register
'''
sync = '''            val phase138Player = server.playerList.players.firstOrNull()
            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && phase138Player != null) {
                if (!phase138ServerHandArmed && phase138Player.tickCount >= 28 && phase138Player.tickCount <= 50) {
                    phase138OriginalMainHand = phase138Player.mainHandItem.copy()
                    phase138Player.setItemSlot(
                        net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                        net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1))
                    phase138ServerHandArmed = true
                    logger.info("GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC player_tick={} item=stone armed=true fixture_only=true",
                        phase138Player.tickCount)
                }
                if (phase138ServerHandArmed && !phase138ServerHandRestored && phase138Player.tickCount > 50) {
                    phase138Player.setItemSlot(
                        net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                        phase138OriginalMainHand ?: net.minecraft.world.item.ItemStack.EMPTY)
                    phase138ServerHandRestored = true
                    logger.info("GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC player_tick={} restored=true fixture_only=true",
                        phase138Player.tickCount)
                }
            }

            if (ticks % 20L != 0L) return@register
'''
if "GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC" not in server:
    if throttle not in server:
        raise SystemExit("Phase 136 could not find recurring GateD throttle")
    server = server.replace(throttle, sync, 1)

required = [
    "GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC",
    "phase138OriginalMainHand = phase138Player.mainHandItem.copy()",
    "Blocks.STONE, 1",
    "EquipmentSlot.MAINHAND",
    "phase138Player.tickCount >= 28",
    "phase138Player.tickCount > 50",
    "fixture_only=true",
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 136 lost server held-block sync anchors: " + ", ".join(missing))

for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in sync:
        raise SystemExit("Phase 136 found forbidden movement/world/train mutation: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
print("Phase 136: synchronizes ServerPlayer held STONE only during the disposable native-interaction window and restores the original hand; no direct placement or physics mutation")
