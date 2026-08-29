#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #68 proved sustained carry, Create-native ray targeting and a live
# CarriageContraption HashMap with a concrete occupied hit cell and empty adjacent cells.
# Before any assembled-train block mutation, inventory the runtime value type stored in
# Contraption.blocks, its public constructors/accessors, and one empty adjacent candidate.
# Read-only only: no map writes, collider invalidation, packets, inventory edits or world mutation.
anchor = '''                                                            LOGGER.info(
                                                                "GATE_F_CONTRAPTION_BLOCK_MAP carriage_id={} player_tick={} map_class={} map_size={} hit_local={} hit_present={} adjacent={} bounds={} read_only=true",
                                                                carriage.getId(), player.tickCount,
                                                                liveBlocks == null ? "not_map" : liveBlocks.getClass().getName(),
                                                                liveBlocks == null ? -1 : liveBlocks.size(),
                                                                hitLocal, hitLocal != null && liveBlocks != null && liveBlocks.containsKey(hitLocal),
                                                                adjacent, String.valueOf(contraptionObject.getClass().getField("bounds").get(contraptionObject)));'''
replacement = anchor + '''
                                                            if (hitLocal != null && liveBlocks != null) {
                                                                Object hitEntry = liveBlocks.get(hitLocal);
                                                                net.minecraft.core.BlockPos firstEmptyAdjacent = null;
                                                                for (net.minecraft.core.Direction direction : net.minecraft.core.Direction.values()) {
                                                                    net.minecraft.core.BlockPos candidate = hitLocal.relative(direction);
                                                                    if (!liveBlocks.containsKey(candidate)) {
                                                                        firstEmptyAdjacent = candidate;
                                                                        break;
                                                                    }
                                                                }
                                                                String entryClass = hitEntry == null ? "null" : hitEntry.getClass().getName();
                                                                java.util.List<String> entryConstructors = new java.util.ArrayList<>();
                                                                java.util.List<String> entryMethods = new java.util.ArrayList<>();
                                                                if (hitEntry != null) {
                                                                    for (java.lang.reflect.Constructor<?> constructor : hitEntry.getClass().getConstructors()) {
                                                                        StringBuilder signature = new StringBuilder("(");
                                                                        Class<?>[] params = constructor.getParameterTypes();
                                                                        for (int index = 0; index < params.length; index++) {
                                                                            if (index > 0) signature.append(',');
                                                                            signature.append(params[index].getSimpleName());
                                                                        }
                                                                        signature.append(')');
                                                                        entryConstructors.add(signature.toString());
                                                                    }
                                                                    for (java.lang.reflect.Method method : hitEntry.getClass().getMethods()) {
                                                                        String lower = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                        if (!(lower.contains("state") || lower.contains("nbt") || lower.contains("tag")
                                                                                || lower.contains("pos") || lower.contains("block"))) continue;
                                                                        StringBuilder signature = new StringBuilder(method.getName()).append('(');
                                                                        Class<?>[] params = method.getParameterTypes();
                                                                        for (int index = 0; index < params.length; index++) {
                                                                            if (index > 0) signature.append(',');
                                                                            signature.append(params[index].getSimpleName());
                                                                        }
                                                                        signature.append("): ").append(method.getReturnType().getSimpleName());
                                                                        entryMethods.add(signature.toString());
                                                                    }
                                                                }
                                                                java.util.Collections.sort(entryConstructors);
                                                                java.util.Collections.sort(entryMethods);
                                                                LOGGER.info(
                                                                    "GATE_F_CONTRAPTION_BLOCK_ENTRY carriage_id={} player_tick={} entry_class={} constructors={} methods={} first_empty_adjacent={} map_size={} read_only=true",
                                                                    carriage.getId(), player.tickCount, entryClass, entryConstructors, entryMethods,
                                                                    firstEmptyAdjacent, liveBlocks.size());
                                                            }'''

if "GATE_F_CONTRAPTION_BLOCK_ENTRY" not in source:
    if anchor not in source:
        raise SystemExit("Phase 103 could not find Phase 102 block-map log anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_BLOCK_ENTRY',
    'Object hitEntry = liveBlocks.get(hitLocal)',
    'hitEntry.getClass().getConstructors()',
    'firstEmptyAdjacent',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 103 lost block-entry inspection anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'invalidateColliders(', '.setAccessible(',
    'setPos(', 'setDeltaMovement(', 'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in replacement:
        raise SystemExit("Phase 103 found forbidden mutation/dispatch: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 103: inventoried Create contraption block-entry value shape and first empty adjacent placement cell read-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase105.py")), run_name="__main__")
