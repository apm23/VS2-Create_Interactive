#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #26 proved exact local hit -> world point roundtrips with zero error
# and a stable local face while vanilla picking still reports MISS. Before constructing
# any synthetic BlockHitResult, validate how that local face normal transforms into
# world-space. This is read-only geometry telemetry; no hitResult assignment or use.
anchor = '''                                                        roundtripState = "face=" + localFace
                                                            + ";world_hit=" + worldHit.x + "," + worldHit.y + "," + worldHit.z
                                                            + ";expected_world_hit=" + expectedWorldHit.x + "," + expectedWorldHit.y + "," + expectedWorldHit.z
                                                            + ";ray_t=" + t
                                                            + ";roundtrip_error=" + roundtripError;'''
replacement = '''                                                        net.minecraft.world.phys.Vec3 localNormal = switch (localFace) {
                                                            case "UP" -> new net.minecraft.world.phys.Vec3(0.0D, 1.0D, 0.0D);
                                                            case "DOWN" -> new net.minecraft.world.phys.Vec3(0.0D, -1.0D, 0.0D);
                                                            case "EAST" -> new net.minecraft.world.phys.Vec3(1.0D, 0.0D, 0.0D);
                                                            case "WEST" -> new net.minecraft.world.phys.Vec3(-1.0D, 0.0D, 0.0D);
                                                            case "SOUTH" -> new net.minecraft.world.phys.Vec3(0.0D, 0.0D, 1.0D);
                                                            case "NORTH" -> new net.minecraft.world.phys.Vec3(0.0D, 0.0D, -1.0D);
                                                            default -> net.minecraft.world.phys.Vec3.ZERO;
                                                        };
                                                        net.minecraft.world.phys.Vec3 worldNormalPoint =
                                                            (net.minecraft.world.phys.Vec3) toGlobalExact.invoke(
                                                                carriage, nearestLocalHit.add(localNormal), 0.0F);
                                                        net.minecraft.world.phys.Vec3 worldNormal = worldNormalPoint.subtract(worldHit);
                                                        if (worldNormal.lengthSqr() > 1.0e-12D) worldNormal = worldNormal.normalize();
                                                        double ax = Math.abs(worldNormal.x);
                                                        double ay = Math.abs(worldNormal.y);
                                                        double az = Math.abs(worldNormal.z);
                                                        String worldFace;
                                                        if (ay >= ax && ay >= az) worldFace = worldNormal.y >= 0.0D ? "UP" : "DOWN";
                                                        else if (ax >= az) worldFace = worldNormal.x >= 0.0D ? "EAST" : "WEST";
                                                        else worldFace = worldNormal.z >= 0.0D ? "SOUTH" : "NORTH";
                                                        roundtripState = "face=" + localFace
                                                            + ";world_face=" + worldFace
                                                            + ";world_normal=" + worldNormal.x + "," + worldNormal.y + "," + worldNormal.z
                                                            + ";world_hit=" + worldHit.x + "," + worldHit.y + "," + worldHit.z
                                                            + ";expected_world_hit=" + expectedWorldHit.x + "," + expectedWorldHit.y + "," + expectedWorldHit.z
                                                            + ";ray_t=" + t
                                                            + ";roundtrip_error=" + roundtripError;'''

if "world_face=" not in source:
    if anchor not in source:
        raise SystemExit("Phase 94 could not find Phase 93 roundtrip-state anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'world_face=',
    'world_normal=',
    'nearestLocalHit.add(localNormal)',
    'toGlobalExact.invoke',
    'GATE_F_CONTRAPTION_HIT_ROUNDTRIP',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 94 lost transformed-face anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 94: transformed exact contraption local hit face into world-space normal/face; read-only telemetry")

# Run construct-only validation last. Phase 95 creates a BlockHitResult object and checks
# its stored fields but never assigns it to Minecraft or dispatches an interaction.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase95.py")), run_name="__main__")
