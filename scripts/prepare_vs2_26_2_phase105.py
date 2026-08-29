#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #74 proved sustained production carry and exposed the exact Create
# block mutation surface: CarriageContraptionEntity.setBlock(BlockPos, StructureBlockInfo),
# while Phase 103 identified the live StructureBlockInfo value at the native hit cell.
# Exercise that mutator only as a test-fixture no-op by writing the *existing entry back
# to the same occupied position once*. This proves the real Create path is callable before
# attempting an empty-cell placement. No new block/state/NBT is introduced and the probe
# verifies map size/state remain unchanged.
anchor = '''                                                                LOGGER.info(
                                                                    "GATE_F_CONTRAPTION_BLOCK_ENTRY carriage_id={} player_tick={} entry_class={} constructors={} methods={} first_empty_adjacent={} map_size={} read_only=true",
                                                                    carriage.getId(), player.tickCount, entryClass, entryConstructors, entryMethods,
                                                                    firstEmptyAdjacent, liveBlocks.size());'''
probe = anchor + '''
                                                                if (productionSmokeFixture && hitEntry != null
                                                                        && !java.lang.Boolean.getBoolean("vs2.productionNoopSetBlockProbed")) {
                                                                    java.lang.reflect.Method setBlockMethod = null;
                                                                    for (java.lang.reflect.Method method : carriage.getClass().getMethods()) {
                                                                        Class<?>[] params = method.getParameterTypes();
                                                                        if (method.getName().equals("setBlock") && params.length == 2
                                                                                && params[0] == net.minecraft.core.BlockPos.class
                                                                                && params[1].isAssignableFrom(hitEntry.getClass())) {
                                                                            setBlockMethod = method;
                                                                            break;
                                                                        }
                                                                    }
                                                                    int beforeSize = liveBlocks.size();
                                                                    Object beforeEntry = liveBlocks.get(hitLocal);
                                                                    Object beforeState = null;
                                                                    try {
                                                                        beforeState = hitEntry.getClass().getMethod("state").invoke(hitEntry);
                                                                    } catch (ReflectiveOperationException ignored) {
                                                                    }
                                                                    boolean invoked = false;
                                                                    boolean sizeStable = false;
                                                                    boolean stateStable = false;
                                                                    String errorType = "none";
                                                                    try {
                                                                        if (setBlockMethod != null) {
                                                                            setBlockMethod.invoke(carriage, hitLocal.immutable(), hitEntry);
                                                                            invoked = true;
                                                                            Object afterEntry = liveBlocks.get(hitLocal);
                                                                            Object afterState = null;
                                                                            if (afterEntry != null) {
                                                                                try {
                                                                                    afterState = afterEntry.getClass().getMethod("state").invoke(afterEntry);
                                                                                } catch (ReflectiveOperationException ignored) {
                                                                                }
                                                                            }
                                                                            sizeStable = liveBlocks.size() == beforeSize;
                                                                            stateStable = java.util.Objects.equals(beforeState, afterState);
                                                                        }
                                                                    } catch (ReflectiveOperationException | RuntimeException probeException) {
                                                                        errorType = probeException.getClass().getSimpleName();
                                                                    }
                                                                    System.setProperty("vs2.productionNoopSetBlockProbed", "true");
                                                                    LOGGER.info(
                                                                        "GATE_F_CONTRAPTION_SETBLOCK_NOOP carriage_id={} player_tick={} hit_local={} method_found={} invoked={} before_size={} after_size={} size_stable={} state_stable={} same_entry_identity={} error={} fixture_only=true",
                                                                        carriage.getId(), player.tickCount, hitLocal, setBlockMethod != null, invoked,
                                                                        beforeSize, liveBlocks.size(), sizeStable, stateStable,
                                                                        beforeEntry == liveBlocks.get(hitLocal), errorType);
                                                                }'''

if "GATE_F_CONTRAPTION_SETBLOCK_NOOP" not in source:
    if anchor not in source:
        raise SystemExit("Phase 105 could not find Phase 103 block-entry log anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_F_CONTRAPTION_SETBLOCK_NOOP',
    'method.getName().equals("setBlock")',
    'setBlockMethod.invoke(carriage, hitLocal.immutable(), hitEntry)',
    'vs2.productionNoopSetBlockProbed',
    'fixture_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 105 lost no-op setBlock anchors: " + ", ".join(missing))

# This phase must remain a same-cell/same-entry canary. Empty-cell writes, removals,
# inventory consumption and world-level placement are deliberately forbidden here.
for forbidden in [
    'firstEmptyAdjacent, hitEntry', '.remove(', '.clear(', 'Blocks.STONE', 'Blocks.AIR',
    'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 105 found forbidden placement/mutation expansion: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 105: exercised Create CarriageContraptionEntity.setBlock as a fixture-only same-cell/same-entry no-op canary; no new block placement or inventory/world mutation")
