#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #107 proved Create syncCarriage() is found and invoked after the
# authoritative fixture-only placement, but Phase 113 emitted neither pending nor synced
# telemetry. Phase 113 was coupled to whichever carriage the surrounding support loop
# happened to be processing. Resolve the exact published carriage id from ClientLevel
# directly so replication observation cannot be skipped by sibling-carriage iteration.
# Keep this exact observer on its own completion flag: Phase 113's generic observer may
# see the same STONE first, but that must not suppress the stronger exact id/cell proof.
anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
probe = '''            if (productionSmokeFixture
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationSucceeded")
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementSyncInvoked")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementExactClientObserved")) {
                String exactCarriageIdText = System.getProperty("vs2.productionNativePlacementCarriageId");
                String exactEmptyXText = System.getProperty("vs2.productionNativePlacementEmptyX");
                String exactEmptyYText = System.getProperty("vs2.productionNativePlacementEmptyY");
                String exactEmptyZText = System.getProperty("vs2.productionNativePlacementEmptyZ");
                net.minecraft.client.multiplayer.ClientLevel exactLevel = net.minecraft.client.Minecraft.getInstance().level;
                if (exactLevel != null && exactCarriageIdText != null && exactEmptyXText != null
                        && exactEmptyYText != null && exactEmptyZText != null) {
                    try {
                        int exactCarriageId = Integer.parseInt(exactCarriageIdText);
                        net.minecraft.world.entity.Entity exactEntity = exactLevel.getEntity(exactCarriageId);
                        net.minecraft.core.BlockPos exactPos = new net.minecraft.core.BlockPos(
                            Integer.parseInt(exactEmptyXText), Integer.parseInt(exactEmptyYText), Integer.parseInt(exactEmptyZText));
                        Object exactEntry = null;
                        Object exactState = null;
                        if (exactEntity != null) {
                            java.lang.reflect.Method exactGetContraption = exactEntity.getClass().getMethod("getContraption");
                            Object exactContraption = exactGetContraption.invoke(exactEntity);
                            java.lang.reflect.Method exactGetBlocks = exactContraption.getClass().getMethod("getBlocks");
                            Object exactBlocks = exactGetBlocks.invoke(exactContraption);
                            if (exactBlocks instanceof java.util.Map<?, ?> exactMap) {
                                exactEntry = exactMap.get(exactPos);
                            }
                            if (exactEntry != null) {
                                java.lang.reflect.Method exactStateMethod = exactEntry.getClass().getMethod("state");
                                exactState = exactStateMethod.invoke(exactEntry);
                            }
                        }
                        boolean exactSynced = java.util.Objects.equals(
                            exactState, net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
                        if (exactSynced) {
                            System.setProperty("vs2.productionNativePlacementClientObserved", "true");
                            System.setProperty("vs2.productionNativePlacementExactClientObserved", "true");
                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC carriage_id={} player_tick={} empty_local={} entity_present={} entry_present={} state={} synced=true read_only=true",
                                exactCarriageId, player.tickCount, exactPos, exactEntity != null, exactEntry != null, exactState);
                        } else if (player.tickCount % 10 == 0) {
                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_PENDING carriage_id={} player_tick={} empty_local={} entity_present={} entry_present={} state={} synced=false read_only=true",
                                exactCarriageId, player.tickCount, exactPos, exactEntity != null, exactEntry != null, exactState);
                        }
                    } catch (ReflectiveOperationException | RuntimeException exactReplicationException) {
                        LOGGER.info(
                            "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_PENDING player_tick={} synced=false error={} read_only=true",
                            player.tickCount, exactReplicationException.getClass().getSimpleName());
                    }
                }
            }

''' + anchor

if "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC" not in source:
    if anchor not in source:
        raise SystemExit("Phase 118 could not find Gate E client-state anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC',
    'GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_PENDING',
    'exactLevel.getEntity(exactCarriageId)',
    'vs2.productionNativePlacementMutationSucceeded',
    'vs2.productionNativePlacementSyncInvoked',
    'vs2.productionNativePlacementExactClientObserved',
    'synced=true read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 118 lost exact client replication anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'setPos(', 'setDeltaMovement(',
    '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 118 found forbidden client mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 118: resolves the exact published client carriage id with an independent exact-sync completion flag; read-only replication telemetry only")

# Run the production-smoke-only collider recovery after all earlier fixture transforms
# have been installed, so it patches the final generated Gate E source without changing
# normal production gameplay or the existing CI harness path.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase119.py")), run_name="__main__")
