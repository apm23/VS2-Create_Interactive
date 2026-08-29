#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = client_probe.read_text(encoding="utf-8")

old_decl = '''                String localFeetState = "unresolved";
                try {'''
new_decl = '''                String localFeetState = "unresolved";
                String colliderLocalFeetState = "unresolved";
                double colliderNearestTopDistanceSq = Double.POSITIVE_INFINITY;
                Vec3 colliderLocalFeet = null;
                try {'''
if old_decl not in source:
    raise SystemExit("Phase 56 could not find candidate local-feet declaration anchor")
source = source.replace(old_decl, new_decl, 1)

old_local = '''                    Vec3 candidateLocalFeet = (Vec3) toLocalCandidate.invoke(candidate, player.position(), 0.0f);
                    localFeetState = candidateLocalFeet.x + "," + candidateLocalFeet.y + "," + candidateLocalFeet.z;
                    java.lang.reflect.Method getContraptionCandidate = candidate.getClass().getMethod("getContraption");'''
new_local = '''                    Vec3 candidateLocalFeet = (Vec3) toLocalCandidate.invoke(candidate, player.position(), 0.0f);
                    localFeetState = candidateLocalFeet.x + "," + candidateLocalFeet.y + "," + candidateLocalFeet.z;

                    // Reproduce the coordinate transform used by Create's own ContraptionCollider.
                    // This is intentionally reflective/read-only so Create remains an optional runtime dependency.
                    Class<?> colliderClass = Class.forName("com.zurrtum.create.content.contraptions.ContraptionCollider");
                    java.lang.reflect.Method worldToLocalMethod = null;
                    for (java.lang.reflect.Method method : colliderClass.getMethods()) {
                        if (!method.getName().equals("worldToLocalPos") || method.getParameterCount() != 2) continue;
                        Class<?>[] parameterTypes = method.getParameterTypes();
                        if (parameterTypes[0] == Vec3.class && parameterTypes[1].isAssignableFrom(candidate.getClass())) {
                            worldToLocalMethod = method;
                            break;
                        }
                    }
                    if (worldToLocalMethod != null) {
                        colliderLocalFeet = (Vec3) worldToLocalMethod.invoke(null, player.position(), candidate);
                        colliderLocalFeetState = colliderLocalFeet.x + "," + colliderLocalFeet.y + "," + colliderLocalFeet.z;
                    } else {
                        colliderLocalFeetState = "method_missing";
                    }

                    java.lang.reflect.Method getContraptionCandidate = candidate.getClass().getMethod("getContraption");'''
if old_local not in source:
    raise SystemExit("Phase 56 could not find candidate toLocalVector anchor")
source = source.replace(old_local, new_local, 1)

old_distance = '''                                double candidateDistanceSq = cdx * cdx + cdy * cdy + cdz * cdz;
                                if (candidateDistanceSq < nearestTopDistanceSq) nearestTopDistanceSq = candidateDistanceSq;'''
new_distance = '''                                double candidateDistanceSq = cdx * cdx + cdy * cdy + cdz * cdz;
                                if (candidateDistanceSq < nearestTopDistanceSq) nearestTopDistanceSq = candidateDistanceSq;
                                if (colliderLocalFeet != null) {
                                    double colliderDx = (candidatePos.getX() + 0.5) - colliderLocalFeet.x;
                                    double colliderDy = (candidatePos.getY() + 1.0) - colliderLocalFeet.y;
                                    double colliderDz = (candidatePos.getZ() + 0.5) - colliderLocalFeet.z;
                                    double colliderDistanceSq = colliderDx * colliderDx + colliderDy * colliderDy + colliderDz * colliderDz;
                                    if (colliderDistanceSq < colliderNearestTopDistanceSq) {
                                        colliderNearestTopDistanceSq = colliderDistanceSq;
                                    }
                                }'''
if old_distance not in source:
    raise SystemExit("Phase 56 could not find candidate distance anchor")
source = source.replace(old_distance, new_distance, 1)

old_log = '''                    .append(";broadphase=").append(candidateBroadphase)
                    .append(";local_feet=").append(localFeetState)
                    .append(";nearest_top_d2=").append(nearestTopDistanceSq)
                    .append(";blocks=").append(blockCount);'''
new_log = '''                    .append(";broadphase=").append(candidateBroadphase)
                    .append(";local_feet=").append(localFeetState)
                    .append(";nearest_top_d2=").append(nearestTopDistanceSq)
                    .append(";collider_local_feet=").append(colliderLocalFeetState)
                    .append(";collider_nearest_top_d2=").append(colliderNearestTopDistanceSq)
                    .append(";blocks=").append(blockCount);'''
if old_log not in source:
    raise SystemExit("Phase 56 could not find candidate log anchor")
source = source.replace(old_log, new_log, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 56: compared toLocalVector with Create ContraptionCollider.worldToLocalPos for every carriage candidate; read-only telemetry only")
