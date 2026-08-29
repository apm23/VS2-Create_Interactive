#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #80 proved the server-side same-cell/same-entry setBlock path is
# safe, but that canary ran on the fixture carriage while the settled native interaction
# ray later targeted a sibling carriage. Publish the exact client-native occupied hit
# and first empty adjacent local cell so the next server-side experiment can resolve the
# same carriage/cells instead of guessing. This phase is read-only: System properties
# are telemetry only; no contraption/world/inventory/player mutation is introduced.
anchor = '''                                                                    firstEmptyAdjacent, liveBlocks.size());'''
replacement = anchor + '''
                                                                if (productionSmokeFixture && firstEmptyAdjacent != null
                                                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")) {
                                                                    System.setProperty("vs2.productionNativePlacementCarriageId", Integer.toString(carriage.getId()));
                                                                    System.setProperty("vs2.productionNativePlacementHitX", Integer.toString(hitLocal.getX()));
                                                                    System.setProperty("vs2.productionNativePlacementHitY", Integer.toString(hitLocal.getY()));
                                                                    System.setProperty("vs2.productionNativePlacementHitZ", Integer.toString(hitLocal.getZ()));
                                                                    System.setProperty("vs2.productionNativePlacementEmptyX", Integer.toString(firstEmptyAdjacent.getX()));
                                                                    System.setProperty("vs2.productionNativePlacementEmptyY", Integer.toString(firstEmptyAdjacent.getY()));
                                                                    System.setProperty("vs2.productionNativePlacementEmptyZ", Integer.toString(firstEmptyAdjacent.getZ()));
                                                                    System.setProperty("vs2.productionNativePlacementTargetReady", "true");
                                                                    LOGGER.info(
                                                                        "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED carriage_id={} player_tick={} hit_local={} empty_local={} hit_present={} empty_present={} read_only=true",
                                                                        carriage.getId(), player.tickCount, hitLocal, firstEmptyAdjacent,
                                                                        liveBlocks.containsKey(hitLocal), liveBlocks.containsKey(firstEmptyAdjacent));
                                                                }'''

if "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED" not in source:
    if anchor not in source:
        raise SystemExit("Phase 107 could not find Phase 103 block-entry telemetry anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED',
    'vs2.productionNativePlacementTargetReady',
    'vs2.productionNativePlacementCarriageId',
    'vs2.productionNativePlacementHitX',
    'vs2.productionNativePlacementEmptyX',
    'liveBlocks.containsKey(firstEmptyAdjacent)',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 107 lost native placement-target publication anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'invalidateColliders(',
    'setPos(', 'setDeltaMovement(', 'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in replacement:
        raise SystemExit("Phase 107 found forbidden gameplay mutation/dispatch: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 107: published the exact Create-native occupied hit and empty adjacent placement target read-only; no block, world, inventory, player, train, or physics mutation")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase105.py")), run_name="__main__")
