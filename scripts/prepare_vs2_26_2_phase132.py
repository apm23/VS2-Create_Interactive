#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #186 proved the empty-hand Create native dispatch reaches handled=true,
# while the earlier Phase132 held-block marker never executed. Bind the disposable STONE
# probe directly to that confirmed handled=true branch so the probe cannot silently attach
# to an inactive duplicate invocation site. Restore the main hand in finally. This remains
# fixture-only and does not directly mutate the contraption map, train state, or physics.
if "GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE" not in source:
    anchor = '''                                                    if (Boolean.TRUE.equals(handled)) {
                                                        System.setProperty("vs2.productionNativeRightClickCarriageId", Integer.toString(carriage.getId()));'''
    if anchor not in source:
        raise SystemExit("Phase 132 could not find confirmed handled=true native right-click branch")
    replacement = '''                                                    if (Boolean.TRUE.equals(handled)) {
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
                                                            "GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE carriage_id={} player_tick={} invoked=true item=stone handled={} error={} restored_main_hand={} confirmed_branch=true fixture_only=true",
                                                            carriage.getId(), player.tickCount, phase132HeldBlockHandled, phase132HeldBlockError,
                                                            player.getMainHandItem());
                                                        System.setProperty("vs2.productionNativeRightClickCarriageId", Integer.toString(carriage.getId()));'''
    source = source.replace(anchor, replacement, 1)

# Production-world #185 proved the previous harness fix reached genuine Create contact
# and an exact Create-computed/filtered replay at tick 24 (relative drift ~0), but the
# following tick lost the simplified-collider/broadphase support predicate while Create's
# own contact state and onGround were still true. Do not create a new carry vector and do
# not allow an unsupported replay streak. Permit exactly one recovery replay immediately
# after a physically-supported replay, then require strict support again. This handles a
# one-tick moving-frame handoff without turning stale baseline identity into carry authority.
if "GATE_E_PHASE133_ONE_TICK_REPLAY_GRACE" not in source:
    replay_tick_token = "carryReplayPlayerTick != player.tickCount"
    replay_tick_pos = source.find(replay_tick_token)
    if replay_tick_pos < 0 or source.find(replay_tick_token, replay_tick_pos + 1) >= 0:
        raise SystemExit("Phase 132 expected one final Phase85 replay tick predicate")

    search_start = max(0, replay_tick_pos - 6000)
    prefix = source[search_start:replay_tick_pos]
    candidates = list(re.finditer(r'(?m)^(?P<indent>[ \t]*)if \(', prefix))
    replay_if_pos = None
    replay_indent = None
    replay_open_end = None
    for candidate in reversed(candidates):
        absolute = search_start + candidate.start()
        segment = source[absolute:replay_tick_pos]
        if "phase81PhysicalSupport" in segment and "collisionEligible" in segment:
            replay_if_pos = absolute
            replay_indent = candidate.group("indent")
            replay_open_end = replay_tick_pos
            break
    if replay_if_pos is None or replay_indent is None:
        raise SystemExit("Phase 132 could not locate final Phase85 replay guard")

    guard_segment = source[replay_if_pos:replay_tick_pos]
    if "phase81PhysicalSupport" not in guard_segment:
        raise SystemExit("Phase 132 final replay guard lost strict support predicate")

    grace_probe = (
        f'{replay_indent}String phase133GraceKey = "vs2.phase133GraceReplayTick." + carriage.getId();\n'
        f'{replay_indent}int phase133LastGraceReplayTick;\n'
        f'{replay_indent}try {{\n'
        f'{replay_indent}    phase133LastGraceReplayTick = Integer.parseInt(System.getProperty(phase133GraceKey, "-2147483648"));\n'
        f'{replay_indent}}} catch (NumberFormatException ignored) {{\n'
        f'{replay_indent}    phase133LastGraceReplayTick = Integer.MIN_VALUE;\n'
        f'{replay_indent}}}\n'
        f'{replay_indent}boolean phase133ReplayGrace = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}    && !phase81PhysicalSupport && player.onGround()\n'
        f'{replay_indent}    && carryReplayPlayerTick == player.tickCount - 1\n'
        f'{replay_indent}    && phase133LastGraceReplayTick != carryReplayPlayerTick;\n'
        f'{replay_indent}if (phase133ReplayGrace) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE133_ONE_TICK_REPLAY_GRACE carriage_id={{}} player_tick={{}} previous_replay_tick={{}} strict_support=false bounded_one_tick=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, carryReplayPlayerTick);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + grace_probe + source[replay_if_pos:]

    replay_tick_pos = source.find(replay_tick_token, replay_if_pos + len(grace_probe))
    replay_if_pos = source.rfind("if (", 0, replay_tick_pos)
    if replay_if_pos < 0:
        raise SystemExit("Phase 132 lost replay guard after grace insertion")
    guard_segment = source[replay_if_pos:replay_tick_pos]
    guard_rewritten = guard_segment.replace(
        "phase81PhysicalSupport",
        "(phase81PhysicalSupport || phase133ReplayGrace)",
        1,
    )
    if guard_rewritten == guard_segment:
        raise SystemExit("Phase 132 failed to widen replay guard with bounded grace")
    source = source[:replay_if_pos] + guard_rewritten + source[replay_tick_pos:]

    assignment = "carryReplayPlayerTick = player.tickCount;"
    assignment_pos = source.find(assignment, replay_tick_pos)
    if assignment_pos < 0:
        raise SystemExit("Phase 132 could not find replay tick assignment")
    assignment_end = assignment_pos + len(assignment)
    grace_consume = (
        f'\n{replay_indent}    if (phase133ReplayGrace) {{\n'
        f'{replay_indent}        System.setProperty(phase133GraceKey, Integer.toString(player.tickCount));\n'
        f'{replay_indent}    }}'
    )
    source = source[:assignment_end] + grace_consume + source[assignment_end:]

required = [
    "GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE",
    "new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1)",
    "settledExactRightClickMethod.invoke(",
    "EquipmentSlot.MAINHAND",
    "phase132OriginalMainHand",
    "confirmed_branch=true",
    "fixture_only=true",
    "GATE_E_PHASE133_ONE_TICK_REPLAY_GRACE",
    "phase133ReplayGrace",
    "phase133LastGraceReplayTick != carryReplayPlayerTick",
    "(phase81PhysicalSupport || phase133ReplayGrace)",
    "System.setProperty(phase133GraceKey, Integer.toString(player.tickCount))",
    "bounded_one_tick=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 132 lost held-block/replay-grace anchors: " + ", ".join(missing))

# No new carry vector, teleport, direct world mutation, or train/physics mutation is
# introduced here. The only added carry behavior is one reuse of the already existing
# Create-computed/collision-filtered Phase85 replay immediately after a strict-support tick.
held_probe_slice = source[source.index("GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE") - 2500:source.index("GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE") + 1200]
for forbidden in ["setBlock(", ".put(", ".remove(", "player.setPos(", "player.setDeltaMovement(", ".teleport"]:
    if forbidden in held_probe_slice:
        raise SystemExit("Phase 132 found forbidden direct mutation near native held-block probe: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 132: binds native held-block probe to confirmed handled=true dispatch and preserves one bounded post-support Create-filtered carry replay grace")
