#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #210 proved the server-arm handshake itself works, but also exposed
# a fixture deadlock: once the authoritative ServerPlayer is armed with one STONE, that
# inventory state synchronizes to LocalPlayer, while Phase101 still requires an empty
# client hand before native dispatch. Consume the synchronized held block instead. This
# changes only the disposable production-smoke interaction fixture; movement/collision,
# train state, VS2 physics, and normal gameplay remain untouched.
old_guard = '''                                                        && settledServerHeldBlockArmed
                                                        && player.getMainHandItem().isEmpty()
                                                        && !nativeRightClickProbeDispatched) {'''
new_guard = '''                                                        && settledServerHeldBlockArmed
                                                        && player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem())
                                                        && !nativeRightClickProbeDispatched) {'''
if old_guard in source:
    source = source.replace(old_guard, new_guard, 1)
elif "settledServerHeldBlockArmed\n                                                        && player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem())" not in source:
    raise SystemExit("Phase 138 could not find server-armed native dispatch guard")

# Mark completion immediately after the authoritative held-block native invocation returns.
# Phase136 uses this same-JVM signal only to delay restoration of the fixture inventory.
invoke_pattern = re.compile(
    r'(?m)^(?P<indent>[ \t]*)Object handled = settledExactRightClickMethod\.invoke\(\n'
    r'(?P=indent)[ \t]+null, client, net\.minecraft\.world\.InteractionHand\.MAIN_HAND\);\n'
)
if "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH" not in source:
    match = invoke_pattern.search(source)
    if match is None:
        raise SystemExit("Phase 138 could not find Phase101 native invocation")
    indent = match.group("indent")
    addition = (
        match.group(0)
        + f'{indent}System.setProperty("vs2.productionHeldBlockNativeDispatchCompleted", "true");\n'
        + f'{indent}LOGGER.info("GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH carriage_id={{}} player_tick={{}} handled={{}} server_held_block_armed=true item_after={{}} fixture_only=true",\n'
        + f'{indent}    carriage.getId(), player.tickCount, handled, player.getMainHandItem());\n'
    )
    source = source[:match.start()] + addition + source[match.end():]

# Phase134 predates the authoritative server-arm handshake and historically performed a
# second held-block probe after the empty-hand confirmation. Once Phase138 has already
# dispatched the synchronized STONE, suppress that duplicate invocation while retaining
# its telemetry. We only skip the fixture probe; no production interaction path is changed.
probe_pattern = re.compile(
    r'(?m)^(?P<indent>[ \t]*)player\.setItemSlot\(net\.minecraft\.world\.entity\.EquipmentSlot\.MAINHAND, phase136ProbeStack(?P<idx>\d+)\);\n'
    r'(?P=indent)phase136HeldBlockHandled(?P=idx) = settledExactRightClickMethod\.invoke\(\n'
    r'(?P=indent)[ \t]+null, client, net\.minecraft\.world\.InteractionHand\.MAIN_HAND\);\n'
    r'(?P=indent)System\.setProperty\("vs2\.productionHeldBlockNativeDispatchCompleted", "true"\);\n'
)
replaced = 0

def replace_probe(match):
    global replaced
    replaced += 1
    indent = match.group("indent")
    idx = match.group("idx")
    return (
        f'{indent}if (!Boolean.getBoolean("vs2.productionHeldBlockNativeDispatchCompleted")) {{\n'
        f'{indent}    player.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, phase136ProbeStack{idx});\n'
        f'{indent}    phase136HeldBlockHandled{idx} = settledExactRightClickMethod.invoke(\n'
        f'{indent}        null, client, net.minecraft.world.InteractionHand.MAIN_HAND);\n'
        f'{indent}    System.setProperty("vs2.productionHeldBlockNativeDispatchCompleted", "true");\n'
        f'{indent}}} else {{\n'
        f'{indent}    phase136HeldBlockHandled{idx} = Boolean.TRUE;\n'
        f'{indent}    phase136HeldBlockError{idx} = "already_dispatched_phase138";\n'
        f'{indent}}}\n'
    )

source, replaced = probe_pattern.subn(replace_probe, source)
if replaced == 0 and "already_dispatched_phase138" not in source:
    raise SystemExit("Phase 138 could not find Phase134 duplicate held-block probe")

required = [
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
    "player.getMainHandItem().is(net.minecraft.world.level.block.Blocks.STONE.asItem())",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "already_dispatched_phase138",
    "settledServerHeldBlockArmed",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 138 lost held-block handshake anchors: " + ", ".join(missing))

# Fixture synchronization only: no movement, train control, direct world/contraption mutation.
for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in source[source.find("GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH") - 1800:source.find("GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH") + 1800]:
        raise SystemExit("Phase 138 native dispatch patch found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 138: dispatches only after authoritative STONE sync and suppresses duplicate held-block probe")
