#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Arm ServerPlayer only after the client explicitly enters the interaction phase.
# Production-world #201 showed server-tick-based arming still happens too early and can
# perturb the movement-measurement window. The same-JVM request is emitted by Phase101
# only once the client has a settled native ray at tick >=30. Restore remains gated by
# held-block dispatch completion plus five server ticks. Fixture-only, no direct placement.
vars_anchor = '''        var playerOnEnvelopeAtStart = false
'''
vars_insert = vars_anchor + '''        var phase138OriginalMainHand: net.minecraft.world.item.ItemStack? = null
        var phase138ServerHandArmed = false
        var phase138ServerHandRestored = false
        var phase138DispatchCompletedAtServerTick: Long? = null
'''
if "phase138OriginalMainHand" not in server:
    if vars_anchor not in server: raise SystemExit("Phase 136 could not find GateD fixture-state variable anchor")
    server = server.replace(vars_anchor, vars_insert, 1)

throttle = '''            if (ticks % 20L != 0L) return@register
'''
sync = '''            val phase138Player = server.playerList.players.firstOrNull()
            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture") && phase138Player != null) {
                if (!phase138ServerHandArmed
                        && java.lang.Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {
                    phase138OriginalMainHand = phase138Player.mainHandItem.copy()
                    phase138Player.setItemSlot(
                        net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                        net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1))
                    phase138ServerHandArmed = true
                    System.setProperty("vs2.productionHeldBlockServerArmed", "true")
                    logger.info("GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC player_tick={} item=stone armed=true request_observed=true fixture_only=true",
                        phase138Player.tickCount)
                }
                if (phase138ServerHandArmed
                        && phase138DispatchCompletedAtServerTick == null
                        && java.lang.Boolean.getBoolean("vs2.productionHeldBlockNativeDispatchCompleted")) {
                    phase138DispatchCompletedAtServerTick = ticks
                    logger.info("GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC player_tick={} dispatch_completed_observed=true server_tick={} fixture_only=true",
                        phase138Player.tickCount, ticks)
                }
                val phase138CompletedTick = phase138DispatchCompletedAtServerTick
                if (phase138ServerHandArmed && !phase138ServerHandRestored
                        && phase138CompletedTick != null && ticks >= phase138CompletedTick + 5L) {
                    phase138Player.setItemSlot(
                        net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                        phase138OriginalMainHand ?: net.minecraft.world.item.ItemStack.EMPTY)
                    phase138ServerHandRestored = true
                    logger.info("GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC player_tick={} restored=true server_tick={} after_dispatch_grace=true fixture_only=true",
                        phase138Player.tickCount, ticks)
                }
            }

            if (ticks % 20L != 0L) return@register
'''
if "GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC" not in server:
    if throttle not in server: raise SystemExit("Phase 136 could not find recurring GateD throttle")
    server = server.replace(throttle, sync, 1)
elif "vs2.productionHeldBlockServerArmRequested" not in server:
    old = '''                if (!phase138ServerHandArmed && phase138Player.tickCount >= 28) {
'''
    new = '''                if (!phase138ServerHandArmed
                        && java.lang.Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {
'''
    if old not in server: raise SystemExit("Phase 136 could not find old server-tick arming condition")
    server = server.replace(old, new, 1)
    armed_line = '''                    phase138ServerHandArmed = true
'''
    server = server.replace(armed_line, armed_line + '''                    System.setProperty("vs2.productionHeldBlockServerArmed", "true")
''', 1)
    server = server.replace('item=stone armed=true fixture_only=true', 'item=stone armed=true request_observed=true fixture_only=true', 1)

required = ["GATE_D_PHASE138_SERVER_HELD_BLOCK_SYNC","vs2.productionHeldBlockServerArmRequested","vs2.productionHeldBlockServerArmed","vs2.productionHeldBlockNativeDispatchCompleted","phase138CompletedTick + 5L","fixture_only=true"]
missing = [token for token in required if token not in server]
if missing: raise SystemExit("Phase 136 lost request/restore handshake anchors: " + ", ".join(missing))
for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in sync: raise SystemExit("Phase 136 found forbidden mutation: " + forbidden)

server_probe.write_text(server, encoding="utf-8")
print("Phase 136: arms ServerPlayer STONE only after client interaction readiness request, then restores after native dispatch plus five server ticks")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase137.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase138.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase139.py")), run_name="__main__")
