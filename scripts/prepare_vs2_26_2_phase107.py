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
# same carriage/cells instead of guessing. Production-world #160 also proved Create's
# native ray may MISS while the independently validated exact contraption-local ray finds
# a real occupied cell. Publish that exact-local cell as the same fixture target fallback.
# This phase remains read-only: System properties are telemetry only; no contraption,
# world, inventory, player, train, or physics mutation is introduced on the client.
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
                                                                        "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED carriage_id={} player_tick={} hit_local={} empty_local={} hit_present={} empty_present={} source=native read_only=true",
                                                                        carriage.getId(), player.tickCount, hitLocal, firstEmptyAdjacent,
                                                                        liveBlocks.containsKey(hitLocal), liveBlocks.containsKey(firstEmptyAdjacent));
                                                                }'''

if "source=native read_only=true" not in source:
    if anchor not in source:
        raise SystemExit("Phase 107 could not find Phase 103 block-entry telemetry anchor")
    if "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED" in source:
        # Upgrade an earlier Phase107-generated block when the cumulative source already
        # contains it. Phase scripts are normally applied once, but this keeps reruns safe.
        source = source.replace("empty_present={} read_only=true", "empty_present={} source=native read_only=true", 1)
    else:
        source = source.replace(anchor, replacement, 1)

fallback_anchor = '''                                                exactLocalHitState = "exact_hit=" + (nearestCell != null)'''
fallback_publication = '''                                                if (productionSmokeFixture && nearestCell != null
                                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")) {
                                                    net.minecraft.core.BlockPos fallbackEmpty = null;
                                                    net.minecraft.core.Direction[] fallbackDirections = new net.minecraft.core.Direction[] {
                                                        net.minecraft.core.Direction.UP, net.minecraft.core.Direction.NORTH,
                                                        net.minecraft.core.Direction.SOUTH, net.minecraft.core.Direction.EAST,
                                                        net.minecraft.core.Direction.WEST, net.minecraft.core.Direction.DOWN
                                                    };
                                                    for (net.minecraft.core.Direction fallbackDirection : fallbackDirections) {
                                                        net.minecraft.core.BlockPos candidateEmpty = nearestCell.relative(fallbackDirection);
                                                        if (!exactBlocks.containsKey(candidateEmpty)) {
                                                            fallbackEmpty = candidateEmpty;
                                                            break;
                                                        }
                                                    }
                                                    if (fallbackEmpty != null) {
                                                        System.setProperty("vs2.productionNativePlacementCarriageId", Integer.toString(carriage.getId()));
                                                        System.setProperty("vs2.productionNativePlacementHitX", Integer.toString(nearestCell.getX()));
                                                        System.setProperty("vs2.productionNativePlacementHitY", Integer.toString(nearestCell.getY()));
                                                        System.setProperty("vs2.productionNativePlacementHitZ", Integer.toString(nearestCell.getZ()));
                                                        System.setProperty("vs2.productionNativePlacementEmptyX", Integer.toString(fallbackEmpty.getX()));
                                                        System.setProperty("vs2.productionNativePlacementEmptyY", Integer.toString(fallbackEmpty.getY()));
                                                        System.setProperty("vs2.productionNativePlacementEmptyZ", Integer.toString(fallbackEmpty.getZ()));
                                                        System.setProperty("vs2.productionNativePlacementTargetReady", "true");
                                                        LOGGER.info(
                                                            "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED carriage_id={} player_tick={} hit_local={} empty_local={} hit_present={} empty_present={} source=exact_local_fallback read_only=true",
                                                            carriage.getId(), player.tickCount, nearestCell, fallbackEmpty,
                                                            exactBlocks.containsKey(nearestCell), exactBlocks.containsKey(fallbackEmpty));
                                                    }
                                                }
                                                exactLocalHitState = "exact_hit=" + (nearestCell != null)'''
if "source=exact_local_fallback read_only=true" not in source:
    if fallback_anchor not in source:
        raise SystemExit("Phase 107 could not find Phase 92 exact-local hit assignment anchor")
    source = source.replace(fallback_anchor, fallback_publication, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED',
    'vs2.productionNativePlacementTargetReady',
    'vs2.productionNativePlacementCarriageId',
    'vs2.productionNativePlacementHitX',
    'vs2.productionNativePlacementEmptyX',
    'source=native read_only=true',
    'source=exact_local_fallback read_only=true',
    '!exactBlocks.containsKey(candidateEmpty)',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 107 lost placement-target publication anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'invalidateColliders(',
    'setPos(', 'setDeltaMovement(', 'setItemSlot(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in fallback_publication:
        raise SystemExit("Phase 107 found forbidden gameplay mutation/dispatch in fallback publication: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 107: publishes exact native or validated exact-local occupied/empty placement target read-only; no block, world, inventory, player, train, or physics mutation")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase108.py")), run_name="__main__")
