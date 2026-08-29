#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #22 proved the settled eye ray can cross exact occupied contraption
# cells while vanilla still reports MISS. Tighten that evidence without interacting:
# clip the local-space segment against each occupied unit block AABB and record the
# nearest exact block hit point. This remains pure telemetry and does not synthesize or
# dispatch a Minecraft interaction.
anchor = '''                                        LOGGER.info(
                                            "GATE_F_CONTRAPTION_LOCAL_RAY carriage_id={} player_tick={} vanilla_hit_type={} envelope_hit={} state={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(), carriageEnvelopeHit.isPresent(), localRayState);'''
replacement = anchor + '''

                                        String exactLocalHitState = "unresolved";
                                        try {
                                            java.lang.reflect.Method toLocalExact = carriage.getClass().getMethod(
                                                "toLocalVector", net.minecraft.world.phys.Vec3.class, float.class);
                                            net.minecraft.world.phys.Vec3 exactLocalStart =
                                                (net.minecraft.world.phys.Vec3) toLocalExact.invoke(carriage, interactionRayStart, 0.0F);
                                            net.minecraft.world.phys.Vec3 exactLocalEnd =
                                                (net.minecraft.world.phys.Vec3) toLocalExact.invoke(carriage, interactionRayEnd, 0.0F);
                                            Object exactContraption = carriage.getClass().getMethod("getContraption").invoke(carriage);
                                            Object exactBlocksObject = exactContraption == null ? null
                                                : exactContraption.getClass().getMethod("getBlocks").invoke(exactContraption);
                                            if (exactBlocksObject instanceof java.util.Map<?, ?> exactBlocks) {
                                                net.minecraft.core.BlockPos nearestCell = null;
                                                net.minecraft.world.phys.Vec3 nearestLocalHit = null;
                                                double nearestDistanceSq = Double.POSITIVE_INFINITY;
                                                for (Object key : exactBlocks.keySet()) {
                                                    if (!(key instanceof net.minecraft.core.BlockPos cell)) continue;
                                                    net.minecraft.world.phys.AABB cellBox = new net.minecraft.world.phys.AABB(cell);
                                                    java.util.Optional<net.minecraft.world.phys.Vec3> hit = cellBox.clip(exactLocalStart, exactLocalEnd);
                                                    if (hit.isEmpty()) continue;
                                                    double distanceSq = hit.get().distanceToSqr(exactLocalStart);
                                                    if (distanceSq < nearestDistanceSq) {
                                                        nearestDistanceSq = distanceSq;
                                                        nearestCell = cell;
                                                        nearestLocalHit = hit.get();
                                                    }
                                                }
                                                Object nearestInfo = nearestCell == null ? null : exactBlocks.get(nearestCell);
                                                String nearestState = "none";
                                                if (nearestInfo != null) {
                                                    try {
                                                        Object state = nearestInfo.getClass().getMethod("state").invoke(nearestInfo);
                                                        nearestState = String.valueOf(state);
                                                    } catch (ReflectiveOperationException ignored) {
                                                        nearestState = nearestInfo.getClass().getName();
                                                    }
                                                }
                                                exactLocalHitState = "exact_hit=" + (nearestCell != null)
                                                    + ";cell=" + (nearestCell == null ? "none" : nearestCell.toShortString())
                                                    + ";local_hit=" + (nearestLocalHit == null ? "none"
                                                        : nearestLocalHit.x + "," + nearestLocalHit.y + "," + nearestLocalHit.z)
                                                    + ";distance_sq=" + nearestDistanceSq
                                                    + ";state=" + nearestState;
                                            } else {
                                                exactLocalHitState = "blocks_type=" + (exactBlocksObject == null ? "null" : exactBlocksObject.getClass().getName());
                                            }
                                        } catch (ReflectiveOperationException | RuntimeException exception) {
                                            exactLocalHitState = "error=" + exception.getClass().getSimpleName();
                                        }
                                        LOGGER.info(
                                            "GATE_F_CONTRAPTION_EXACT_LOCAL_HIT carriage_id={} player_tick={} vanilla_hit_type={} state={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(), exactLocalHitState);'''

if "GATE_F_CONTRAPTION_EXACT_LOCAL_HIT" not in source:
    if anchor not in source:
        raise SystemExit("Phase 92 could not find Phase 91 local-ray anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_EXACT_LOCAL_HIT',
    'new net.minecraft.world.phys.AABB(cell)',
    'cellBox.clip(exactLocalStart, exactLocalEnd)',
    'exact_hit=',
    'nearestCell',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 92 lost exact local-hit anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 92: resolved nearest exact occupied contraption block hit along settled local ray; read-only telemetry")
