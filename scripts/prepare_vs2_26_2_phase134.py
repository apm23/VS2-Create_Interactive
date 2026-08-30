#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Instrument every authoritative native-right-click confirmation branch. The probe is
# fixture-only and now also signals the integrated server after the native held-block
# invocation actually returns, so the server-side fixture inventory is not restored on
# an unrelated faster server tick clock while the client render thread is still behind.
confirmation = '"GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=create_native_ray_settled"'
positions = []
search_from = 0
while True:
    pos = source.find(confirmation, search_from)
    if pos < 0:
        break
    positions.append(pos)
    search_from = pos + len(confirmation)

if not positions:
    raise SystemExit("Phase 134 could not find any authoritative native-right-click confirmation sites")

insertions = []
for index, marker_pos in enumerate(positions):
    logger_pos = source.rfind("LOGGER.info(", max(0, marker_pos - 600), marker_pos)
    if logger_pos < 0:
        raise SystemExit(f"Phase 134 could not find LOGGER.info start for confirmation site {index}")
    stmt_end = source.find(");", marker_pos)
    if stmt_end < 0 or stmt_end - marker_pos > 600:
        raise SystemExit(f"Phase 134 could not find LOGGER.info end for confirmation site {index}")
    stmt_end += 2
    nearby = source[stmt_end:stmt_end + 2800]
    if f"GATE_F_PHASE136_HELD_BLOCK_NATIVE_MULTI_ANCHOR site={index}" in nearby:
        continue
    line_start = source.rfind("\n", 0, logger_pos) + 1
    indent = source[line_start:logger_pos]
    i = index
    probe = f'''\n{indent}{{
{indent}    net.minecraft.world.item.ItemStack phase136OriginalMainHand{i} = player.getMainHandItem().copy();
{indent}    net.minecraft.world.item.ItemStack phase136ProbeStack{i} = new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1);
{indent}    Object phase136HeldBlockHandled{i} = null;
{indent}    String phase136HeldBlockError{i} = "none";
{indent}    try {{
{indent}        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase136ProbeStack{i});
{indent}        phase136HeldBlockHandled{i} = settledExactRightClickMethod.invoke(
{indent}            null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
{indent}        System.setProperty("vs2.productionHeldBlockNativeDispatchCompleted", "true");
{indent}    }} catch (ReflectiveOperationException | RuntimeException phase136Exception{i}) {{
{indent}        phase136HeldBlockError{i} = phase136Exception{i}.getClass().getSimpleName();
{indent}    }} finally {{
{indent}        player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase136OriginalMainHand{i});
{indent}    }}
{indent}    LOGGER.info(
{indent}        "GATE_F_PHASE136_HELD_BLOCK_NATIVE_MULTI_ANCHOR site={i} carriage_id={{}} player_tick={{}} invoked=true item=stone handled={{}} error={{}} confirmed_branch=true fixture_only=true restored_main_hand={{}} dispatch_completed_signal={{}}",
{indent}        carriage.getId(), player.tickCount, phase136HeldBlockHandled{i}, phase136HeldBlockError{i}, player.getMainHandItem(),
{indent}        Boolean.getBoolean("vs2.productionHeldBlockNativeDispatchCompleted"));
{indent}}}'''
    insertions.append((stmt_end, probe))

for stmt_end, probe in reversed(insertions):
    source = source[:stmt_end] + probe + source[stmt_end:]

if not insertions and "GATE_F_PHASE136_HELD_BLOCK_NATIVE_MULTI_ANCHOR" not in source:
    raise SystemExit("Phase 134 found confirmation sites but installed no multi-anchor probes")

required = [
    "GATE_F_PHASE136_HELD_BLOCK_NATIVE_MULTI_ANCHOR",
    "new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1)",
    "settledExactRightClickMethod.invoke(",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "EquipmentSlot.MAINHAND",
    "confirmed_branch=true",
    "fixture_only=true",
    "restored_main_hand={}",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 134 lost multi-anchor held-block probe requirements: " + ", ".join(missing))

for marker_pos in [p for p in range(len(source)) if source.startswith("GATE_F_PHASE136_HELD_BLOCK_NATIVE_MULTI_ANCHOR", p)]:
    probe_slice = source[max(0, marker_pos - 2400):marker_pos + 1000]
    for forbidden in [
        "player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(",
        ".put(", ".remove(", "setSchedule", "setTrain", "setVelocity",
    ]:
        if forbidden in probe_slice:
            raise SystemExit("Phase 134 found forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print(f"Phase 134: instrumented {len(insertions)} native confirmation site(s) and signals server only after held-block dispatch completes")
