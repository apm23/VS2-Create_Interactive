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

# Production-world #189 proved the marker above still attaches to an inactive duplicate
# handled=true site: the artifact contains GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED but no
# Phase132 held-block marker. Anchor a second, authoritative probe to the exact confirmation
# LOGGER statement that executed in #189. It reuses the already-resolved Create native
# right-click method, temporarily equips one STONE in the disposable fixture, restores the
# original hand in finally, and emits an unambiguous marker for the workflow_run gate.
if "GATE_F_PHASE135_HELD_BLOCK_NATIVE_CONFIRMED" not in source:
    confirmed_anchor = '''                                                        LOGGER.info(
                                                            "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=create_native_ray_settled",
                                                            carriage.getId(), player.tickCount);'''
    if confirmed_anchor not in source:
        raise SystemExit("Phase 132 could not find executed native right-click confirmation log")
    confirmed_probe = confirmed_anchor + '''
                                                        net.minecraft.world.item.ItemStack phase135OriginalMainHand = player.getMainHandItem().copy();
                                                        net.minecraft.world.item.ItemStack phase135ProbeStack = new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1);
                                                        Object phase135HeldBlockHandled = null;
                                                        String phase135HeldBlockError = "none";
                                                        try {
                                                            player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase135ProbeStack);
                                                            phase135HeldBlockHandled = settledExactRightClickMethod.invoke(
                                                                null, client, net.minecraft.world.InteractionHand.MAIN_HAND);
                                                        } catch (ReflectiveOperationException | RuntimeException phase135Exception) {
                                                            phase135HeldBlockError = phase135Exception.getClass().getSimpleName();
                                                        } finally {
                                                            player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase135OriginalMainHand);
                                                        }
                                                        LOGGER.info(
                                                            "GATE_F_PHASE135_HELD_BLOCK_NATIVE_CONFIRMED carriage_id={} player_tick={} invoked=true item=stone handled={} error={} confirmed_branch=true fixture_only=true",
                                                            carriage.getId(), player.tickCount, phase135HeldBlockHandled, phase135HeldBlockError);'''
    source = source.replace(confirmed_anchor, confirmed_probe, 1)

# Production-world #185 proved the previous harness fix reached genuine Create contact
# and an exact Create-computed/filtered replay at tick 24 (relative drift ~0), but the
# following tick lost the simplified-collider/broadphase support predicate while Create's
# own contact state and onGround were still true. Do not create a new carry vector and do
# not allow an unsupported replay streak. Permit exactly one recovery replay immediately
# after a physically-supported replay, then require strict support again. Run #283 further
# proved the first loss tick may follow healthy native carry rather than a compatibility
# replay. Accept that one transition only when the previous tick has an authoritative healthy
# native sample and broadphase still overlaps. Phase85 remains the only source of the replay
# vector and still applies Create collision filtering.
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
        f'{replay_indent}boolean phase159PreviousNativeHealthy = Boolean.parseBoolean(System.getProperty(\n'
        f'{replay_indent}    "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))\n'
        f'{replay_indent}    && Integer.toString(player.tickCount - 1).equals(System.getProperty(\n'
        f'{replay_indent}        "vs2.phase134NativeCarryHealthyTick." + carriage.getId()));\n'
        f'{replay_indent}boolean phase133ReplayGrace = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && carryBaselineCaptured && carryBaselineCarriageId == carriage.getId()\n'
        f'{replay_indent}    && !phase81PhysicalSupport && player.onGround()\n'
        f'{replay_indent}    && (carryReplayPlayerTick == player.tickCount - 1 || phase159PreviousNativeHealthy)\n'
        f'{replay_indent}    && (!phase159PreviousNativeHealthy || broadphaseOverlap)\n'
        f'{replay_indent}    && (phase159PreviousNativeHealthy || phase133LastGraceReplayTick != carryReplayPlayerTick);\n'
        f'{replay_indent}if (phase133ReplayGrace) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE133_ONE_TICK_REPLAY_GRACE carriage_id={{}} player_tick={{}} previous_replay_tick={{}} previous_native_healthy={{}} strict_support=false bounded_one_tick=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, carryReplayPlayerTick, phase159PreviousNativeHealthy);\n'
        f'{replay_indent}    if (phase159PreviousNativeHealthy) {{\n'
        f'{replay_indent}        LOGGER.info(\n'
        f'{replay_indent}            "GATE_E_PHASE159_NATIVE_LOSS_REPLAY_GRACE carriage_id={{}} player_tick={{}} previous_native_tick={{}} broadphase=true grounded=true bounded_one_tick=true existing_create_filtered_replay=true",\n'
        f'{replay_indent}            carriage.getId(), player.tickCount, player.tickCount - 1);\n'
        f'{replay_indent}    }}\n'
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

    # Production-world #286 proves the grace predicate itself becomes true at the first
    # native-support loss (tick 41), but Phase137's stale previous-healthy de-dup predicate
    # still suppresses Phase85 before it can consume that grace. Let this already-bounded
    # grace override only that de-dup suppression. All other replay predicates remain intact.
    native_suppression_pattern = re.compile(
        r'!\(productionSmoke && explicitCarryCompat && \(\s*'
        r'Boolean\.parseBoolean\(System\.getProperty\("vs2\.phase134NativeCarryHealthy\." \+ carriage\.getId\(\), "false"\)\)\s*'
        r'\|\| Integer\.toString\(player\.tickCount - 1\)\.equals\(System\.getProperty\("vs2\.phase134NativeCarryHealthyTick\." \+ carriage\.getId\(\)\)\)\)\)'
    )
    suppression_match = native_suppression_pattern.search(guard_rewritten)
    if suppression_match is None:
        raise SystemExit("Phase 132 could not find Phase137 native carry de-dup suppression")
    guard_rewritten = (
        guard_rewritten[:suppression_match.start()]
        + "(" + suppression_match.group(0) + " || phase133ReplayGrace)"
        + guard_rewritten[suppression_match.end():]
    )
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
    "GATE_F_PHASE135_HELD_BLOCK_NATIVE_CONFIRMED",
    "new net.minecraft.world.item.ItemStack(net.minecraft.world.level.block.Blocks.STONE, 1)",
    "settledExactRightClickMethod.invoke(",
    "EquipmentSlot.MAINHAND",
    "phase132OriginalMainHand",
    "phase135OriginalMainHand",
    "confirmed_branch=true",
    "fixture_only=true",
    "GATE_E_PHASE133_ONE_TICK_REPLAY_GRACE",
    "phase133ReplayGrace",
    "phase159PreviousNativeHealthy",
    "GATE_E_PHASE159_NATIVE_LOSS_REPLAY_GRACE",
    "(!phase159PreviousNativeHealthy || broadphaseOverlap)",
    "(phase159PreviousNativeHealthy || phase133LastGraceReplayTick != carryReplayPlayerTick)",
    "(phase81PhysicalSupport || phase133ReplayGrace)",
    "|| phase133ReplayGrace)",
    "System.setProperty(phase133GraceKey, Integer.toString(player.tickCount))",
    "existing_create_filtered_replay=true",
    "bounded_one_tick=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 132 lost held-block/replay-grace anchors: " + ", ".join(missing))

# No new carry vector, teleport, direct world mutation, or train/physics mutation is
# introduced here. The held-block probes only use Create's already-confirmed native handler
# and restore the disposable client hand immediately after invocation.
for marker in ["GATE_F_PHASE132_HELD_BLOCK_NATIVE_PROBE", "GATE_F_PHASE135_HELD_BLOCK_NATIVE_CONFIRMED"]:
    marker_pos = source.index(marker)
    held_probe_slice = source[max(0, marker_pos - 2500):marker_pos + 1200]
    for forbidden in ["setBlock(", ".put(", ".remove(", "player.setPos(", "player.setDeltaMovement(", ".teleport"]:
        if forbidden in held_probe_slice:
            raise SystemExit("Phase 132 found forbidden direct mutation near native held-block probe: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 132: lets the bounded native-loss grace bypass only stale native de-dup suppression while preserving Create-filtered replay")
