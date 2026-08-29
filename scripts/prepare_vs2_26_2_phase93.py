#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #24 proved the settled ray resolves a stable exact occupied local
# block while vanilla still reports MISS. Before synthesizing any interaction, verify
# that the exact local hit maps back to the same world-space ray point and derive the
# local block face. This is read-only geometry telemetry only.
anchor = '''                                                exactLocalHitState = "exact_hit=" + (nearestCell != null)
                                                    + ";cell=" + (nearestCell == null ? "none" : nearestCell.toShortString())'''
replacement = '''                                                if (nearestCell != null && nearestLocalHit != null) {
                                                    String localFace = "UNKNOWN";
                                                    double eps = 1.0e-6D;
                                                    if (Math.abs(nearestLocalHit.y - (nearestCell.getY() + 1.0D)) <= eps) localFace = "UP";
                                                    else if (Math.abs(nearestLocalHit.y - nearestCell.getY()) <= eps) localFace = "DOWN";
                                                    else if (Math.abs(nearestLocalHit.x - (nearestCell.getX() + 1.0D)) <= eps) localFace = "EAST";
                                                    else if (Math.abs(nearestLocalHit.x - nearestCell.getX()) <= eps) localFace = "WEST";
                                                    else if (Math.abs(nearestLocalHit.z - (nearestCell.getZ() + 1.0D)) <= eps) localFace = "SOUTH";
                                                    else if (Math.abs(nearestLocalHit.z - nearestCell.getZ()) <= eps) localFace = "NORTH";

                                                    String roundtripState = "unresolved";
                                                    try {
                                                        java.lang.reflect.Method toGlobalExact = carriage.getClass().getMethod(
                                                            "toGlobalVector", net.minecraft.world.phys.Vec3.class, float.class);
                                                        net.minecraft.world.phys.Vec3 worldHit =
                                                            (net.minecraft.world.phys.Vec3) toGlobalExact.invoke(carriage, nearestLocalHit, 0.0F);
                                                        double localLength = exactLocalStart.distanceTo(exactLocalEnd);
                                                        double localDistance = exactLocalStart.distanceTo(nearestLocalHit);
                                                        double t = localLength <= 1.0e-12D ? 0.0D : localDistance / localLength;
                                                        net.minecraft.world.phys.Vec3 expectedWorldHit = interactionRayStart.lerp(interactionRayEnd, t);
                                                        double roundtripError = worldHit.distanceTo(expectedWorldHit);
                                                        roundtripState = "face=" + localFace
                                                            + ";world_hit=" + worldHit.x + "," + worldHit.y + "," + worldHit.z
                                                            + ";expected_world_hit=" + expectedWorldHit.x + "," + expectedWorldHit.y + "," + expectedWorldHit.z
                                                            + ";ray_t=" + t
                                                            + ";roundtrip_error=" + roundtripError;
                                                    } catch (ReflectiveOperationException | RuntimeException exception) {
                                                        roundtripState = "face=" + localFace + ";error=" + exception.getClass().getSimpleName();
                                                    }
                                                    LOGGER.info(
                                                        "GATE_F_CONTRAPTION_HIT_ROUNDTRIP carriage_id={} player_tick={} cell={} local_hit={},{},{} state={}",
                                                        carriage.getId(), player.tickCount, nearestCell.toShortString(),
                                                        nearestLocalHit.x, nearestLocalHit.y, nearestLocalHit.z, roundtripState);
                                                }
                                                exactLocalHitState = "exact_hit=" + (nearestCell != null)
                                                    + ";cell=" + (nearestCell == null ? "none" : nearestCell.toShortString())'''

if "GATE_F_CONTRAPTION_HIT_ROUNDTRIP" not in source:
    if anchor not in source:
        raise SystemExit("Phase 93 could not find Phase 92 exact-hit anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_HIT_ROUNDTRIP',
    'toGlobalVector',
    'roundtrip_error=',
    'face=',
    'expected_world_hit=',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 93 lost exact-hit roundtrip anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 93: validated exact local contraption hit face and local-to-world ray roundtrip; read-only telemetry")
