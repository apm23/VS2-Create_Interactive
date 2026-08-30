#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 64 proved the actual CarriageContraption exposes getBlocks(), bounds and
# invalidateColliders(), but no public one-block placement API. Before mutating the
# assembled train, inspect the exact Create-native settled hit cell and its six adjacent
# cells in the live contraption block map. Re-run the same read-only native ray here so
# Phase 102 does not depend on the narrower Phase 95 synthetic-hit local variable scope.
legacy_anchor = '''                                                        LOGGER.info(
                                                            "GATE_F_CONTRAPTION_MUTATION_SURFACE carriage_id={} player_tick={} contraption_class={} methods={} method_count={} fields={} field_count={} read_only=true",
                                                            carriage.getId(), player.tickCount, contraptionObject.getClass().getName(),
                                                            mutationMethods, mutationMethods.size(), mutationFields, mutationFields.size());'''
current_anchor = '''                                                        LOGGER.info("GATE_F_CONTRAPTION_MUTATION_SURFACE carriage_id={} player_tick={} contraption_class={} methods={} method_count={} fields={} field_count={} read_only=true",
                                                            carriage.getId(), player.tickCount, contraptionObject.getClass().getName(), mutationMethods, mutationMethods.size(), mutationFields, mutationFields.size());'''
anchor = legacy_anchor if legacy_anchor in source else current_anchor
replacement = anchor + '''
                                                        try {
                                                            java.lang.reflect.Method getBlocksMethod = contraptionObject.getClass().getMethod("getBlocks");
                                                            Object blocksObject = getBlocksMethod.invoke(contraptionObject);
                                                            java.util.Map<?, ?> liveBlocks = blocksObject instanceof java.util.Map<?, ?> map ? map : null;
                                                            net.minecraft.core.BlockPos hitLocal = null;
                                                            Class<?> settledHandlerClass = Class.forName("com.zurrtum.create.client.content.contraptions.ContraptionHandlerClient");
                                                            java.lang.reflect.Method settledRayMethod = null;
                                                            for (java.lang.reflect.Method candidate : settledHandlerClass.getMethods()) {
                                                                if (!candidate.getName().equals("rayTraceContraption")) continue;
                                                                Class<?>[] rayParams = candidate.getParameterTypes();
                                                                if (rayParams.length == 3
                                                                        && rayParams[0].getSimpleName().equals("Vec3")
                                                                        && rayParams[1].getSimpleName().equals("Vec3")
                                                                        && rayParams[2].getSimpleName().equals("AbstractContraptionEntity")) {
                                                                    settledRayMethod = candidate;
                                                                    break;
                                                                }
                                                            }
                                                            if (settledRayMethod != null) {
                                                                net.minecraft.world.phys.Vec3 nativeOrigin = player.getEyePosition();
                                                                double nativeReach = player.blockInteractionRange();
                                                                net.minecraft.world.phys.Vec3 nativeTarget = nativeOrigin.add(player.getViewVector(1.0F).scale(nativeReach));
                                                                Object nativeResult = settledRayMethod.invoke(null, nativeOrigin, nativeTarget, carriage);
                                                                if (nativeResult instanceof net.minecraft.world.phys.BlockHitResult nativeHit) {
                                                                    hitLocal = nativeHit.getBlockPos();
                                                                }
                                                            }
                                                            StringBuilder adjacent = new StringBuilder();
                                                            if (hitLocal != null) {
                                                                for (net.minecraft.core.Direction direction : net.minecraft.core.Direction.values()) {
                                                                    net.minecraft.core.BlockPos candidate = hitLocal.relative(direction);
                                                                    if (adjacent.length() > 0) adjacent.append(';');
                                                                    adjacent.append(direction).append('=')
                                                                        .append(candidate.toShortString()).append(':')
                                                                        .append(liveBlocks != null && liveBlocks.containsKey(candidate));
                                                                }
                                                            }
                                                            LOGGER.info(
                                                                "GATE_F_CONTRAPTION_BLOCK_MAP carriage_id={} player_tick={} map_class={} map_size={} hit_local={} hit_present={} adjacent={} bounds={} read_only=true",
                                                                carriage.getId(), player.tickCount,
                                                                liveBlocks == null ? "not_map" : liveBlocks.getClass().getName(),
                                                                liveBlocks == null ? -1 : liveBlocks.size(),
                                                                hitLocal, hitLocal != null && liveBlocks != null && liveBlocks.containsKey(hitLocal),
                                                                adjacent, String.valueOf(contraptionObject.getClass().getField("bounds").get(contraptionObject)));
                                                        } catch (ReflectiveOperationException | RuntimeException mapException) {
                                                            LOGGER.info(
                                                                "GATE_F_CONTRAPTION_BLOCK_MAP carriage_id={} player_tick={} error={} read_only=true",
                                                                carriage.getId(), player.tickCount, mapException.getClass().getSimpleName());
                                                        }'''

if "GATE_F_CONTRAPTION_BLOCK_MAP" not in source:
    if anchor not in source:
        raise SystemExit("Phase 102 could not find Phase 101 mutation-surface anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_BLOCK_MAP',
    'getBlocksMethod.invoke(contraptionObject)',
    'rayTraceContraption',
    'nativeHit.getBlockPos()',
    'liveBlocks.containsKey(candidate)',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 102 lost contraption block-map inspection anchors: " + ", ".join(missing))

for forbidden in ['.put(', '.remove(', '.clear(', '.setAccessible(', 'setPos(', 'setDeltaMovement(', 'setItemSlot(']:
    if forbidden in replacement:
        raise SystemExit("Phase 102 found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 102: inspected exact Create-native moving-train block-map occupancy and adjacent placement cells read-only")
