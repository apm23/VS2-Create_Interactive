#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #114 keeps the exact authoritative client carriage present after the
# verified server-side setBlock, but the exact empty cell remains absent. Before changing
# networking or placement behavior, determine whether Create applied the block-change to
# a sibling client carriage instead of the published entity id. This scan is fixture-only
# and read-only; it never mutates a contraption, world, player, inventory, or train.
anchor = '''                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_PENDING carriage_id={} player_tick={} empty_local={} entity_present={} entry_present={} state={} synced=false read_only=true",
                                exactCarriageId, player.tickCount, exactPos, exactEntity != null, exactEntry != null, exactState);'''
probe = anchor + '''
                            try {
                                java.lang.reflect.Method entitiesMethod = exactLevel.getClass().getMethod("entitiesForRendering");
                                Object renderedEntities = entitiesMethod.invoke(exactLevel);
                                int scanned = 0;
                                int contraptions = 0;
                                java.util.List<String> matches = new java.util.ArrayList<>();
                                if (renderedEntities instanceof java.lang.Iterable<?> iterable) {
                                    for (Object candidateObject : iterable) {
                                        if (!(candidateObject instanceof net.minecraft.world.entity.Entity candidateEntity)) continue;
                                        scanned++;
                                        try {
                                            java.lang.reflect.Method candidateGetContraption = candidateEntity.getClass().getMethod("getContraption");
                                            Object candidateContraption = candidateGetContraption.invoke(candidateEntity);
                                            if (candidateContraption == null) continue;
                                            contraptions++;
                                            java.lang.reflect.Method candidateGetBlocks = candidateContraption.getClass().getMethod("getBlocks");
                                            Object candidateBlocks = candidateGetBlocks.invoke(candidateContraption);
                                            if (!(candidateBlocks instanceof java.util.Map<?, ?> candidateMap)) continue;
                                            Object candidateEntry = candidateMap.get(exactPos);
                                            if (candidateEntry == null) continue;
                                            Object candidateState = candidateEntry.getClass().getMethod("state").invoke(candidateEntry);
                                            matches.add(candidateEntity.getId() + ":" + String.valueOf(candidateState));
                                        } catch (ReflectiveOperationException ignoredCandidate) {
                                            // Non-contraption client entity; read-only scan intentionally skips it.
                                        }
                                    }
                                }
                                LOGGER.info(
                                    "GATE_F_NATIVE_PLACEMENT_CLIENT_GLOBAL_SCAN carriage_id={} player_tick={} empty_local={} scanned={} contraptions={} matches={} read_only=true",
                                    exactCarriageId, player.tickCount, exactPos, scanned, contraptions, matches);
                            } catch (ReflectiveOperationException | RuntimeException globalScanException) {
                                LOGGER.info(
                                    "GATE_F_NATIVE_PLACEMENT_CLIENT_GLOBAL_SCAN carriage_id={} player_tick={} empty_local={} error={} read_only=true",
                                    exactCarriageId, player.tickCount, exactPos, globalScanException.getClass().getSimpleName());
                            }'''

if "GATE_F_NATIVE_PLACEMENT_CLIENT_GLOBAL_SCAN" not in source:
    if anchor not in source:
        raise SystemExit("Phase 121 could not find exact pending replication anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_CLIENT_GLOBAL_SCAN',
    'entitiesForRendering',
    'candidateMap.get(exactPos)',
    'matches.add(candidateEntity.getId()',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 121 lost global client replication anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'setPos(', 'setDeltaMovement(',
    '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 121 found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 121: scans every rendered client contraption for the verified placement cell to distinguish wrong-entity replication from missing packet application; read-only")
