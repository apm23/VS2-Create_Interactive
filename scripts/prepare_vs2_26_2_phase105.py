#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Exercise Create's real CarriageContraptionEntity.setBlock surface only as a
# fixture-only same-cell/same-entry canary. Production-world #76 proved that the
# reflective method resolves, but invocation was wrapped in InvocationTargetException.
# Unwrap and report the actual Create-side cause before considering any placement.
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
                                                                    String rootType = "none";
                                                                    String rootMessage = "none";
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
                                                                        Throwable root = probeException;
                                                                        java.util.Set<Throwable> seen = java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>());
                                                                        while (root.getCause() != null && seen.add(root)) {
                                                                            root = root.getCause();
                                                                        }
                                                                        rootType = root.getClass().getName();
                                                                        rootMessage = String.valueOf(root.getMessage()).replace('\\n', ' ').replace('\\r', ' ');
                                                                    }
                                                                    boolean safe = invoked && sizeStable && stateStable;
                                                                    System.setProperty("vs2.productionNoopSetBlockProbed", "true");
                                                                    LOGGER.info(
                                                                        "GATE_F_CONTRAPTION_SETBLOCK_NOOP carriage_id={} player_tick={} hit_local={} method_found={} invoked={} before_size={} after_size={} size_stable={} state_stable={} same_entry_identity={} safe={} error={} root_type={} root_message={} fixture_only=true",
                                                                        carriage.getId(), player.tickCount, hitLocal, setBlockMethod != null, invoked,
                                                                        beforeSize, liveBlocks.size(), sizeStable, stateStable,
                                                                        beforeEntry == liveBlocks.get(hitLocal), safe, errorType, rootType, rootMessage);
                                                                }'''

if "root_type={} root_message={}" not in source:
    if "GATE_F_CONTRAPTION_SETBLOCK_NOOP" in source:
        start = source.find(anchor)
        if start < 0:
            raise SystemExit("Phase 105 could not find Phase 103 block-entry anchor for telemetry refresh")
        # Rebuild from the Phase 103 anchor through the existing no-op block by using
        # the source before Phase 105 if possible: remove the old injected block up to
        # its known closing indentation immediately before the surrounding scope closes.
        old_start = start + len(anchor)
        marker = '''                                                                }\n                                                            }'''
        old_end = source.find(marker, old_start)
        if old_end < 0:
            raise SystemExit("Phase 105 could not delimit prior no-op canary")
        source = source[:start] + probe + source[old_end + len('                                                                }'):]
    else:
        if anchor not in source:
            raise SystemExit("Phase 105 could not find Phase 103 block-entry log anchor")
        source = source.replace(anchor, probe, 1)

required = [
    'GATE_F_CONTRAPTION_SETBLOCK_NOOP',
    'method.getName().equals("setBlock")',
    'setBlockMethod.invoke(carriage, hitLocal.immutable(), hitEntry)',
    'rootType = root.getClass().getName()',
    'root_message={}',
    'boolean safe = invoked && sizeStable && stateStable',
    'fixture_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 105 lost no-op setBlock diagnostics: " + ", ".join(missing))

for forbidden in [
    'firstEmptyAdjacent, hitEntry', '.remove(', '.clear(', 'Blocks.STONE', 'Blocks.AIR',
    'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 105 found forbidden placement/mutation expansion: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 105: retained fixture-only same-cell setBlock canary and now unwraps the Create-side root cause; no new block placement or inventory/world mutation")
