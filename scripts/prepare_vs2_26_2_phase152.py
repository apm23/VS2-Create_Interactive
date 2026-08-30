#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #250 proved the server-arm handshake and native Create ray are both
# healthy, but no held-block dispatch occurred: the arm request executed at one of the
# duplicate settled-ray sites while the historical Phase101/138 invocation lives at a
# different generated site. Phase142 already established that every identical settled-ray
# entrypoint can execute at runtime. Attach the same one-shot fixture-only native invocation
# to every executed settled-ray entrypoint, guarded by the authoritative server-arm property
# and nativeRightClickProbeDispatched. Production-world #254 then proved handled=true plus
# authoritative new-cell STONE replication while the disposable client fixture still held
# STONE after dispatch. Clear that fixture-only client hand immediately after a handled
# invocation; the authoritative server hand remains independently guarded/restored by
# Phase136. This changes no movement, collision, train state, VS2 physics, or normal gameplay.
entry_anchor = '''                                                LOGGER.info(
                                                    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact={} target_match_ready={} readiness_source=create_native_ray_settled",
                                                    carriage.getId(), player.tickCount, settledExactNativeRightClickEntrypoint,
                                                    settledExactNativeRightClickEntrypoint && settledCreateNativeRayReady);'''
entry_replacement = entry_anchor + '''
                                                if (productionSmokeFixture
                                                        && settledCreateNativeRayReady
                                                        && settledExactNativeRightClickEntrypoint
                                                        && Boolean.getBoolean("vs2.productionHeldBlockServerArmed")
                                                        && !nativeRightClickProbeDispatched) {
                                                    nativeRightClickProbeDispatched = true;
                                                    boolean phase152ClientMirrorInjected = !player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem());
                                                    if (phase152ClientMirrorInjected) {
                                                        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                                                            new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1));
                                                    }
                                                    Object phase152Handled = settledExactRightClickMethod.invoke(
                                                        null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                    System.setProperty("vs2.productionHeldBlockNativeDispatchCompleted", "true");
                                                    if (Boolean.TRUE.equals(phase152Handled)) {
                                                        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,
                                                            net.minecraft.world.item.ItemStack.EMPTY);
                                                    }
                                                    LOGGER.info(
                                                        "GATE_F_NATIVE_RIGHT_CLICK_PROBE carriage_id={} player_tick={} invoked=true handled={} hand_empty_after={} readiness_source=executed_settled_native_ray server_held_block_armed=true phase152_site_race_fix=true fixture_hand_cleared_after_handled=true",
                                                        carriage.getId(), player.tickCount, phase152Handled, player.getMainHandItem().isEmpty());
                                                    LOGGER.info(
                                                        "GATE_F_PHASE152_EXECUTED_SITE_HELD_BLOCK_DISPATCH carriage_id={} player_tick={} invoked=true handled={} client_mirror_injected={} item_after={} fixture_only=true",
                                                        carriage.getId(), player.tickCount, phase152Handled, phase152ClientMirrorInjected, player.getMainHandItem());
                                                    if (Boolean.TRUE.equals(phase152Handled)) {
                                                        LOGGER.info(
                                                            "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=executed_settled_native_ray",
                                                            carriage.getId(), player.tickCount);
                                                    }
                                                }'''

if "GATE_F_PHASE152_EXECUTED_SITE_HELD_BLOCK_DISPATCH" not in source:
    count = source.count(entry_anchor)
    if count == 0:
        raise SystemExit("Phase 152 could not find any executed settled-ray entrypoint")
    source = source.replace(entry_anchor, entry_replacement)
else:
    count = source.count("GATE_F_PHASE152_EXECUTED_SITE_HELD_BLOCK_DISPATCH")

required = [
    "GATE_F_PHASE152_EXECUTED_SITE_HELD_BLOCK_DISPATCH",
    "GATE_F_NATIVE_RIGHT_CLICK_PROBE",
    "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED",
    "vs2.productionHeldBlockServerArmed",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "nativeRightClickProbeDispatched",
    "readiness_source=executed_settled_native_ray",
    "phase152_site_race_fix=true",
    "fixture_hand_cleared_after_handled=true",
    "ItemStack.EMPTY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 152 lost executed-site dispatch anchors: " + ", ".join(missing))

for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in entry_replacement:
        raise SystemExit("Phase 152 introduced forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print(f"Phase 152: attached one-shot authoritative held-block native dispatch to {count} executed settled-ray site(s) and clears only the disposable client fixture hand after handled dispatch")
