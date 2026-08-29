#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #97 proved the authoritative ServerLevel setBlock mutation succeeds
# (+1 map entry, STONE state, source identity stable) on the exact native empty cell.
# Before any inventory/useItem dispatch, prove Create propagates that mutation back to
# the moving client carriage. Poll only the already-published exact carriage/cell and
# read its contraption map; no client/world/train/player/inventory mutation is allowed.
anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
probe = '''            if (productionSmokeFixture
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementClientObserved")) {
                String placementCarriageId = System.getProperty("vs2.productionNativePlacementCarriageId");
                String placementEmptyX = System.getProperty("vs2.productionNativePlacementEmptyX");
                String placementEmptyY = System.getProperty("vs2.productionNativePlacementEmptyY");
                String placementEmptyZ = System.getProperty("vs2.productionNativePlacementEmptyZ");
                if (placementCarriageId != null && placementEmptyX != null && placementEmptyY != null && placementEmptyZ != null
                        && Integer.parseInt(placementCarriageId) == carriage.getId()) {
                    try {
                        net.minecraft.core.BlockPos replicatedPos = new net.minecraft.core.BlockPos(
                            Integer.parseInt(placementEmptyX), Integer.parseInt(placementEmptyY), Integer.parseInt(placementEmptyZ));
                        java.lang.reflect.Method getContraptionMethod = carriage.getClass().getMethod("getContraption");
                        Object contraptionObject = getContraptionMethod.invoke(carriage);
                        java.lang.reflect.Method getBlocksMethod = contraptionObject.getClass().getMethod("getBlocks");
                        Object blocksObject = getBlocksMethod.invoke(contraptionObject);
                        Object replicatedEntry = blocksObject instanceof java.util.Map<?, ?> blockMap ? blockMap.get(replicatedPos) : null;
                        Object replicatedState = null;
                        if (replicatedEntry != null) {
                            java.lang.reflect.Method stateMethod = replicatedEntry.getClass().getMethod("state");
                            replicatedState = stateMethod.invoke(replicatedEntry);
                        }
                        boolean synced = java.util.Objects.equals(
                            replicatedState, net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
                        if (synced) {
                            System.setProperty("vs2.productionNativePlacementClientObserved", "true");
                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_SYNC carriage_id={} player_tick={} empty_local={} entry_present={} state={} synced=true read_only=true",
                                carriage.getId(), player.tickCount, replicatedPos, replicatedEntry != null, replicatedState);
                        }
                    } catch (ReflectiveOperationException | RuntimeException replicationException) {
                        LOGGER.info(
                            "GATE_F_NATIVE_PLACEMENT_CLIENT_SYNC carriage_id={} player_tick={} synced=false error={} read_only=true",
                            carriage.getId(), player.tickCount, replicationException.getClass().getSimpleName());
                    }
                }
            }

''' + anchor

if "GATE_F_NATIVE_PLACEMENT_CLIENT_SYNC" not in source:
    if anchor not in source:
        raise SystemExit("Phase 113 could not find Gate E client-state anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_CLIENT_SYNC',
    'vs2.productionNativePlacementMutationProbed',
    'vs2.productionNativePlacementClientObserved',
    'Blocks.STONE.defaultBlockState()',
    'blockMap.get(replicatedPos)',
    'synced=true read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 113 lost client replication anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'invalidateColliders(',
    'setPos(', 'setDeltaMovement(', 'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 113 found forbidden mutation/dispatch: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 113: observes authoritative empty-cell STONE replication on the exact moving client carriage read-only; no block, inventory, player, train, or physics mutation")

# Production-world #99 showed the native target may be published after the one-shot
# server fixture callback has already completed. Chain a fixture-only recurring server
# retry so the placement cannot be skipped by that ordering race.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase114.py")), run_name="__main__")

# Production-world #101 proved the retry mutation succeeds server-side but the client
# observation was absent. Add read-only replication-gap and networking-surface telemetry
# after both the mutation retry and client replication observer have been installed.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase115.py")), run_name="__main__")
