#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = client_probe.read_text(encoding="utf-8")

old = '''            Entity carriage = client.level.getEntitiesOfClass(
                    Entity.class,
                    player.getBoundingBox().inflate(64.0),
                    entity -> "create:carriage_contraption".equals(
                            BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString()))
                .stream()
                .min(Comparator.comparingDouble(entity -> entity.distanceToSqr(player)))
                .orElse(null);'''

new = '''            var carriageCandidates = client.level.getEntitiesOfClass(
                    Entity.class,
                    player.getBoundingBox().inflate(64.0),
                    entity -> "create:carriage_contraption".equals(
                            BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString()));
            StringBuilder candidateState = new StringBuilder();
            int candidateIndex = 0;
            for (Entity candidate : carriageCandidates) {
                if (candidateState.length() > 0) candidateState.append(" || ");
                double nearestTopDistanceSq = Double.POSITIVE_INFINITY;
                int blockCount = -1;
                String localFeetState = "unresolved";
                try {
                    java.lang.reflect.Method toLocalCandidate = candidate.getClass().getMethod("toLocalVector", Vec3.class, float.class);
                    Vec3 candidateLocalFeet = (Vec3) toLocalCandidate.invoke(candidate, player.position(), 0.0f);
                    localFeetState = candidateLocalFeet.x + "," + candidateLocalFeet.y + "," + candidateLocalFeet.z;
                    java.lang.reflect.Method getContraptionCandidate = candidate.getClass().getMethod("getContraption");
                    Object candidateContraption = getContraptionCandidate.invoke(candidate);
                    if (candidateContraption != null) {
                        java.lang.reflect.Method getBlocksCandidate = candidateContraption.getClass().getMethod("getBlocks");
                        Object candidateBlocksObject = getBlocksCandidate.invoke(candidateContraption);
                        if (candidateBlocksObject instanceof Map<?, ?> candidateBlocks) {
                            blockCount = candidateBlocks.size();
                            for (Object candidateKey : candidateBlocks.keySet()) {
                                if (!(candidateKey instanceof net.minecraft.core.BlockPos candidatePos)) continue;
                                double cdx = (candidatePos.getX() + 0.5) - candidateLocalFeet.x;
                                double cdy = (candidatePos.getY() + 1.0) - candidateLocalFeet.y;
                                double cdz = (candidatePos.getZ() + 0.5) - candidateLocalFeet.z;
                                double candidateDistanceSq = cdx * cdx + cdy * cdy + cdz * cdz;
                                if (candidateDistanceSq < nearestTopDistanceSq) nearestTopDistanceSq = candidateDistanceSq;
                            }
                        }
                    }
                } catch (ReflectiveOperationException | RuntimeException exception) {
                    localFeetState = "error=" + exception.getClass().getSimpleName();
                }
                boolean candidateBroadphase = candidate.getBoundingBox().inflate(2.0)
                    .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                candidateState.append('#').append(candidateIndex++)
                    .append("@pos=").append(candidate.getX()).append(',').append(candidate.getY()).append(',').append(candidate.getZ())
                    .append(";center_d2=").append(candidate.distanceToSqr(player))
                    .append(";broadphase=").append(candidateBroadphase)
                    .append(";local_feet=").append(localFeetState)
                    .append(";nearest_top_d2=").append(nearestTopDistanceSq)
                    .append(";blocks=").append(blockCount);
            }
            LOGGER.info("GATE_E_CARRIAGE_CANDIDATES count={} state={}", carriageCandidates.size(), candidateState);

            Entity carriage = carriageCandidates.stream()
                .min(Comparator.comparingDouble(entity -> entity.distanceToSqr(player)))
                .orElse(null);'''

if old not in source:
    raise SystemExit("Phase 55 could not find Gate E carriage selection anchor")
source = source.replace(old, new, 1)
client_probe.write_text(source, encoding="utf-8")
print("Phase 55: traced every nearby Create carriage candidate and local block-support distance; read-only telemetry only")

# Chain Phase 56 so workflows that currently terminate preparation at Phase 54 still
# receive the exact coordinate transform comparison used by Create's own collider.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase56.py")), run_name="__main__")
