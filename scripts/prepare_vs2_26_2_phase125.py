#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #124 proves the runtime client handler is Create Fly's real AllHandle,
# while Create Fly's onContraptionBlockChanged returns immediately when the local block map
# does not already contain packet.localPos(). That behavior can update existing cells but
# cannot replicate a newly-added contraption cell. In the disposable production smoke
# fixture only, test that exact missing-cell hypothesis by inserting the already-authoritative
# STONE cell into the exact client carriage map and refreshing Create's client contraption.
old = '''                            if (exactBlocks instanceof java.util.Map<?, ?> exactMap) {
                                exactEntry = exactMap.get(exactPos);
                            }
                            if (exactEntry != null) {'''
new = '''                            if (exactBlocks instanceof java.util.Map<?, ?> exactMap) {
                                exactEntry = exactMap.get(exactPos);
                                if (exactEntry == null
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementClientInsertHypothesisApplied")) {
                                    System.setProperty("vs2.productionNativePlacementClientInsertHypothesisApplied", "true");
                                    try {
                                        @SuppressWarnings("unchecked")
                                        java.util.Map<Object, Object> writableExactMap = (java.util.Map<Object, Object>) (java.util.Map<?, ?>) exactMap;
                                        net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo inserted =
                                            new net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate.StructureBlockInfo(
                                                exactPos, net.minecraft.world.level.block.Blocks.STONE.defaultBlockState(), null);
                                        writableExactMap.put(exactPos, inserted);
                                        exactEntry = writableExactMap.get(exactPos);
                                        java.lang.reflect.Method invalidateColliders = exactContraption.getClass().getMethod("invalidateColliders");
                                        invalidateColliders.invoke(exactContraption);
                                        Class<?> handleClass = Class.forName("com.zurrtum.create.AllClientHandle");
                                        Object handleInstance = handleClass.getField("INSTANCE").get(null);
                                        boolean resetInvoked = false;
                                        if (handleInstance != null) {
                                            for (java.lang.reflect.Method method : handleInstance.getClass().getMethods()) {
                                                if (!method.getName().equals("resetClientContraption") || method.getParameterCount() != 1) continue;
                                                method.invoke(handleInstance, exactContraption);
                                                resetInvoked = true;
                                                break;
                                            }
                                        }
                                        LOGGER.info(
                                            "GATE_F_NATIVE_PLACEMENT_CLIENT_INSERT_HYPOTHESIS carriage_id={} player_tick={} empty_local={} inserted={} reset_invoked={} fixture_only=true",
                                            exactCarriageId, player.tickCount, exactPos, exactEntry != null, resetInvoked);
                                    } catch (ReflectiveOperationException | RuntimeException insertionException) {
                                        LOGGER.info(
                                            "GATE_F_NATIVE_PLACEMENT_CLIENT_INSERT_HYPOTHESIS carriage_id={} player_tick={} empty_local={} inserted=false error={} fixture_only=true",
                                            exactCarriageId, player.tickCount, exactPos, insertionException.getClass().getSimpleName());
                                    }
                                }
                            }
                            if (exactEntry != null) {'''

if "GATE_F_NATIVE_PLACEMENT_CLIENT_INSERT_HYPOTHESIS" not in source:
    if old not in source:
        raise SystemExit("Phase 125 could not find exact missing-cell observation block")
    source = source.replace(old, new, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_CLIENT_INSERT_HYPOTHESIS',
    'productionNativePlacementClientInsertHypothesisApplied',
    'writableExactMap.put(exactPos, inserted)',
    'invalidateColliders',
    'resetClientContraption',
    'fixture_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 125 lost missing-cell hypothesis anchors: " + ", ".join(missing))

# This mutation is intentionally restricted to the disposable productionSmokeFixture path
# already enclosing the exact replication observer. It does not alter player motion,
# train controls, server/world blocks, inventories, or VS2 physics.
for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', 'setBlock(', '.useItemOn(', '.attack(']:
    if forbidden in new:
        raise SystemExit("Phase 125 found forbidden movement/gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 125: fixture-only proof for Create Fly missing-cell block-change replication; no production movement/physics mutation")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase126.py")), run_name="__main__")
