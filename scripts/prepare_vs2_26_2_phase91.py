#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #20 proved the settled vanilla ray reports MISS while the same
# world-space eye ray intersects the moving carriage entity envelope. Before attempting
# any interaction mutation, transform that same ray into Create contraption-local space
# and sample the contraption block map along it. This distinguishes a broad AABB overlap
# from a ray that actually crosses occupied contraption cells. Read-only telemetry only.
anchor = '''                                        LOGGER.info(
                                            "GATE_F_CARRIAGE_RAY_ENVELOPE carriage_id={} player_tick={} vanilla_hit_type={} envelope_hit={} ray_start={},{},{} ray_end={},{},{} carriage_aabb={} envelope_location={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(), carriageEnvelopeHit.isPresent(),
                                            interactionRayStart.x, interactionRayStart.y, interactionRayStart.z,
                                            interactionRayEnd.x, interactionRayEnd.y, interactionRayEnd.z,
                                            carriageInteractionBounds, carriageEnvelopeLocation);'''
replacement = anchor + '''

                                        String localRayState = "unresolved";
                                        try {
                                            java.lang.reflect.Method toLocalRay = carriage.getClass().getMethod(
                                                "toLocalVector", net.minecraft.world.phys.Vec3.class, float.class);
                                            net.minecraft.world.phys.Vec3 localRayStart =
                                                (net.minecraft.world.phys.Vec3) toLocalRay.invoke(carriage, interactionRayStart, 0.0F);
                                            net.minecraft.world.phys.Vec3 localRayEnd =
                                                (net.minecraft.world.phys.Vec3) toLocalRay.invoke(carriage, interactionRayEnd, 0.0F);
                                            Object localContraption = carriage.getClass().getMethod("getContraption").invoke(carriage);
                                            Object localBlocksObject = localContraption == null ? null
                                                : localContraption.getClass().getMethod("getBlocks").invoke(localContraption);
                                            if (localBlocksObject instanceof java.util.Map<?, ?> localBlocks) {
                                                java.util.LinkedHashSet<String> occupiedCells = new java.util.LinkedHashSet<>();
                                                net.minecraft.world.phys.Vec3 localDelta = localRayEnd.subtract(localRayStart);
                                                for (int sample = 0; sample <= 100; sample++) {
                                                    double t = sample / 100.0D;
                                                    net.minecraft.world.phys.Vec3 p = localRayStart.add(localDelta.scale(t));
                                                    net.minecraft.core.BlockPos cell = net.minecraft.core.BlockPos.containing(p);
                                                    if (localBlocks.containsKey(cell)) {
                                                        occupiedCells.add(cell.toShortString());
                                                    }
                                                }
                                                localRayState = "local_start=" + localRayStart.x + "," + localRayStart.y + "," + localRayStart.z
                                                    + ";local_end=" + localRayEnd.x + "," + localRayEnd.y + "," + localRayEnd.z
                                                    + ";occupied_count=" + occupiedCells.size()
                                                    + ";occupied_cells=" + String.join("|", occupiedCells);
                                            } else {
                                                localRayState = "blocks_type=" + (localBlocksObject == null ? "null" : localBlocksObject.getClass().getName());
                                            }
                                        } catch (ReflectiveOperationException | RuntimeException exception) {
                                            localRayState = "error=" + exception.getClass().getSimpleName();
                                        }
                                        LOGGER.info(
                                            "GATE_F_CONTRAPTION_LOCAL_RAY carriage_id={} player_tick={} vanilla_hit_type={} envelope_hit={} state={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(), carriageEnvelopeHit.isPresent(), localRayState);'''

if "GATE_F_CONTRAPTION_LOCAL_RAY" not in source:
    if anchor not in source:
        raise SystemExit("Phase 91 could not find Phase 90 carriage ray-envelope anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_LOCAL_RAY',
    'toLocalVector',
    'occupied_count=',
    'localBlocks.containsKey(cell)',
    'GATE_F_CARRIAGE_RAY_ENVELOPE',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 91 lost contraption local-ray anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 91: sampled settled interaction ray against exact contraption-local occupied cells; read-only telemetry")
