#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = probe.read_text(encoding="utf-8")

# The exact admitted/current artifacts now prove that Phase55 nearest-center arbitration
# feeds both Phase71's first native-contact baseline and Phase107's placement target.
# Before changing fixture selection, inspect every nearby carriage with the same strict
# simplified-collider support semantics used by Phase81. Telemetry only: do not change
# carriage selection, baseline capture, placement target, input, timing, player/train state,
# collision, or production physics.
anchor = '''                boolean candidateBroadphase = candidate.getBoundingBox().inflate(2.0)
                    .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                candidateState.append('#').append(candidateIndex++)'''
insert = '''                boolean candidateBroadphase = candidate.getBoundingBox().inflate(2.0)
                    .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                if (productionSmokeFixture && player.tickCount >= 12 && player.tickCount <= 28) {
                    boolean candidateXzInside = false;
                    boolean candidateStrictSupport = false;
                    double candidateVerticalGap = Double.NaN;
                    int candidateSupportCollider = -1;
                    try {
                        java.lang.reflect.Method supportGetContraption = candidate.getClass().getMethod("getContraption");
                        Object supportContraption = supportGetContraption.invoke(candidate);
                        if (supportContraption != null) {
                            java.lang.reflect.Method supportGetSimplified = supportContraption.getClass().getMethod("getSimplifiedEntityColliders");
                            Object supportSimplified = supportGetSimplified.invoke(supportContraption);
                            if (supportSimplified != null) {
                                Class<?> supportListType = supportSimplified.getClass();
                                int supportSize = supportListType.getField("size").getInt(supportSimplified);
                                double[] supportCx = (double[]) supportListType.getField("centerX").get(supportSimplified);
                                double[] supportCy = (double[]) supportListType.getField("centerY").get(supportSimplified);
                                double[] supportCz = (double[]) supportListType.getField("centerZ").get(supportSimplified);
                                double[] supportEx = (double[]) supportListType.getField("extentsX").get(supportSimplified);
                                double[] supportEy = (double[]) supportListType.getField("extentsY").get(supportSimplified);
                                double[] supportEz = (double[]) supportListType.getField("extentsZ").get(supportSimplified);
                                java.lang.reflect.Method supportToLocal = candidate.getClass().getMethod("toLocalVector", Vec3.class, float.class);
                                Vec3 supportFeet = (Vec3) supportToLocal.invoke(candidate, player.position(), 0.0f);
                                final double supportEps = 1.0E-5;
                                double bestAbsGap = Double.POSITIVE_INFINITY;
                                for (int supportIndex = 0; supportIndex < supportSize; supportIndex++) {
                                    double minX = supportCx[supportIndex] - supportEx[supportIndex] - supportEps;
                                    double maxX = supportCx[supportIndex] + supportEx[supportIndex] + supportEps;
                                    double minZ = supportCz[supportIndex] - supportEz[supportIndex] - supportEps;
                                    double maxZ = supportCz[supportIndex] + supportEz[supportIndex] + supportEps;
                                    if (supportFeet.x < minX || supportFeet.x > maxX || supportFeet.z < minZ || supportFeet.z > maxZ) continue;
                                    candidateXzInside = true;
                                    double top = supportCy[supportIndex] + supportEy[supportIndex];
                                    double gap = supportFeet.y - top;
                                    double absGap = Math.abs(gap);
                                    if (absGap < bestAbsGap) {
                                        bestAbsGap = absGap;
                                        candidateVerticalGap = gap;
                                        candidateSupportCollider = supportIndex;
                                    }
                                }
                                candidateStrictSupport = candidateXzInside
                                    && Double.isFinite(candidateVerticalGap)
                                    && Math.abs(candidateVerticalGap) <= 0.05;
                            }
                        }
                    } catch (ReflectiveOperationException | RuntimeException supportException) {
                        LOGGER.info(
                            "GATE_E_CANDIDATE_NATIVE_SUPPORT player_tick={} candidate_id={} error={} read_only=true",
                            player.tickCount, candidate.getId(), supportException.getClass().getSimpleName());
                    }
                    LOGGER.info(
                        "GATE_E_CANDIDATE_NATIVE_SUPPORT player_tick={} candidate_id={} selected_by_nearest_center={} center_d2={} broadphase={} collision_eligible={} on_ground={} xz_inside={} vertical_gap={} strict_support={} collider_index={} read_only=true",
                        player.tickCount, candidate.getId(), carriageCandidates.stream().min(Comparator.comparingDouble(entity -> entity.distanceToSqr(player))).orElse(null) == candidate,
                        candidate.distanceToSqr(player), candidateBroadphase, candidate.canCollideWith(player), player.onGround(),
                        candidateXzInside, candidateVerticalGap, candidateStrictSupport, candidateSupportCollider);
                }
                candidateState.append('#').append(candidateIndex++)'''

if "GATE_E_CANDIDATE_NATIVE_SUPPORT" not in source:
    if anchor not in source:
        raise SystemExit("candidate native-support trace could not find Phase55 candidate broadphase anchor")
    source = source.replace(anchor, insert, 1)

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setVelocity(", "setNoGravity(", "setOnGround(", "keyUp.setDown(",
    "setBlock(", ".put(", ".remove(",
]:
    if forbidden in insert:
        raise SystemExit("candidate native-support trace introduced forbidden mutation: " + forbidden)

probe.write_text(source, encoding="utf-8")
print("GATE_E_CANDIDATE_NATIVE_SUPPORT_TRACE prepared=true read_only=true selector_unchanged=true")
