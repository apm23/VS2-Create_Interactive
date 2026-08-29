#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase 55 declares blockCount before localFeetState; Phase 56 then inserts the
# collider fields immediately before the try. Anchor only on the stable Phase 56
# tail so this remains compatible with the chained generated source.
old_decl = '''                Vec3 colliderLocalFeet = null;
                try {'''
new_decl = '''                Vec3 colliderLocalFeet = null;
                net.minecraft.core.BlockPos nearestLocalTopBlock = null;
                String nearestWorldTopState = "unresolved";
                double nearestWorldTopDistanceSq = Double.POSITIVE_INFINITY;
                try {'''
if old_decl not in source:
    raise SystemExit("Phase 59 could not find Gate E Phase 56 collider declaration anchor")
source = source.replace(old_decl, new_decl, 1)

old_distance = '''                                double candidateDistanceSq = cdx * cdx + cdy * cdy + cdz * cdz;
                                if (candidateDistanceSq < nearestTopDistanceSq) nearestTopDistanceSq = candidateDistanceSq;
                                if (colliderLocalFeet != null) {'''
new_distance = '''                                double candidateDistanceSq = cdx * cdx + cdy * cdy + cdz * cdz;
                                if (candidateDistanceSq < nearestTopDistanceSq) {
                                    nearestTopDistanceSq = candidateDistanceSq;
                                    nearestLocalTopBlock = candidatePos;
                                }
                                if (colliderLocalFeet != null) {'''
if old_distance not in source:
    raise SystemExit("Phase 59 could not find Gate E nearest local block anchor")
source = source.replace(old_distance, new_distance, 1)

old_after_try = '''                } catch (ReflectiveOperationException | RuntimeException exception) {
                    localFeetState = "error=" + exception.getClass().getSimpleName();
                }
                boolean candidateBroadphase = candidate.getBoundingBox().inflate(2.0)'''
new_after_try = '''                    if (nearestLocalTopBlock != null) {
                        Vec3 localTopCenter = new Vec3(
                            nearestLocalTopBlock.getX() + 0.5,
                            nearestLocalTopBlock.getY() + 1.0,
                            nearestLocalTopBlock.getZ() + 0.5);
                        java.lang.reflect.Method toGlobal = null;
                        for (java.lang.reflect.Method method : candidate.getClass().getMethods()) {
                            if (!method.getName().equals("toGlobalVector") || method.getParameterCount() != 2) continue;
                            Class<?>[] p = method.getParameterTypes();
                            if (p[0] == Vec3.class && (p[1] == float.class || p[1] == Float.TYPE)) {
                                toGlobal = method;
                                break;
                            }
                        }
                        if (toGlobal != null) {
                            Vec3 worldTop = (Vec3) toGlobal.invoke(candidate, localTopCenter, 0.0f);
                            double wdx = worldTop.x - player.getX();
                            double wdy = worldTop.y - player.getY();
                            double wdz = worldTop.z - player.getZ();
                            nearestWorldTopDistanceSq = wdx * wdx + wdy * wdy + wdz * wdz;
                            nearestWorldTopState = nearestLocalTopBlock.toShortString()
                                + "->" + worldTop.x + "," + worldTop.y + "," + worldTop.z
                                + ";delta=" + wdx + "," + wdy + "," + wdz;
                        } else {
                            nearestWorldTopState = "toGlobalVector_missing local=" + nearestLocalTopBlock.toShortString();
                        }
                    }
                } catch (ReflectiveOperationException | RuntimeException exception) {
                    localFeetState = "error=" + exception.getClass().getSimpleName();
                    nearestWorldTopState = "error=" + exception.getClass().getSimpleName();
                }
                boolean candidateBroadphase = candidate.getBoundingBox().inflate(2.0)'''
if old_after_try not in source:
    raise SystemExit("Phase 59 could not find Gate E candidate try/catch anchor")
source = source.replace(old_after_try, new_after_try, 1)

old_log = '''                    .append(";collider_local_feet=").append(colliderLocalFeetState)
                    .append(";collider_nearest_top_d2=").append(colliderNearestTopDistanceSq)
                    .append(";blocks=").append(blockCount);'''
new_log = '''                    .append(";collider_local_feet=").append(colliderLocalFeetState)
                    .append(";collider_nearest_top_d2=").append(colliderNearestTopDistanceSq)
                    .append(";nearest_world_top=").append(nearestWorldTopState)
                    .append(";nearest_world_top_d2=").append(nearestWorldTopDistanceSq)
                    .append(";blocks=").append(blockCount);'''
if old_log not in source:
    raise SystemExit("Phase 59 could not find Gate E candidate log anchor")
source = source.replace(old_log, new_log, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 59: mapped each nearest local Create block top back to world space to prove whether the saved smoke player is physically on carriage geometry; read-only telemetry only")
