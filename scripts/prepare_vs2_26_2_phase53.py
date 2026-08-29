#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = client_probe.read_text(encoding="utf-8")

old_decl = '''                        StringBuilder nearby = new StringBuilder();
                        double nearestDistanceSq = Double.POSITIVE_INFINITY;
                        Object nearestKey = null;
                        for (Object key : blocks.keySet()) {'''
new_decl = '''                        StringBuilder nearby = new StringBuilder();
                        double nearestDistanceSq = Double.POSITIVE_INFINITY;
                        Object nearestKey = null;
                        int minBlockX = Integer.MAX_VALUE;
                        int minBlockY = Integer.MAX_VALUE;
                        int minBlockZ = Integer.MAX_VALUE;
                        int maxBlockX = Integer.MIN_VALUE;
                        int maxBlockY = Integer.MIN_VALUE;
                        int maxBlockZ = Integer.MIN_VALUE;
                        for (Object key : blocks.keySet()) {'''
if old_decl not in source:
    raise SystemExit("Phase 53 could not find nearest-block declaration anchor")
source = source.replace(old_decl, new_decl, 1)

old_pos = '''                            if (!(key instanceof net.minecraft.core.BlockPos pos)) continue;
                            double dx = (pos.getX() + 0.5) - localFeet.x;'''
new_pos = '''                            if (!(key instanceof net.minecraft.core.BlockPos pos)) continue;
                            minBlockX = Math.min(minBlockX, pos.getX());
                            minBlockY = Math.min(minBlockY, pos.getY());
                            minBlockZ = Math.min(minBlockZ, pos.getZ());
                            maxBlockX = Math.max(maxBlockX, pos.getX());
                            maxBlockY = Math.max(maxBlockY, pos.getY());
                            maxBlockZ = Math.max(maxBlockZ, pos.getZ());
                            double dx = (pos.getX() + 0.5) - localFeet.x;'''
if old_pos not in source:
    raise SystemExit("Phase 53 could not find block-position loop anchor")
source = source.replace(old_pos, new_pos, 1)

old_state = '''                        localSupportState = "local_feet=" + localFeet.x + "," + localFeet.y + "," + localFeet.z
                            + ";support_pos=" + supportPos.toShortString()
                            + ";support_present=" + (supportInfo != null)
                            + ";support=" + supportValue
                            + ";nearest_block=" + String.valueOf(nearestKey)
                            + ";nearest_top_distance_sq=" + nearestDistanceSq
                            + ";nearby_blocks=" + nearby
                            + ";block_count=" + blocks.size();'''
new_state = '''                        String nearestDelta = "none";
                        if (nearestKey instanceof net.minecraft.core.BlockPos nearestPos) {
                            nearestDelta = ((nearestPos.getX() + 0.5) - localFeet.x) + ","
                                + ((nearestPos.getY() + 1.0) - localFeet.y) + ","
                                + ((nearestPos.getZ() + 0.5) - localFeet.z);
                        }
                        StringBuilder frameApi = new StringBuilder();
                        for (java.lang.reflect.Method method : contraption.getClass().getMethods()) {
                            String lower = method.getName().toLowerCase(java.util.Locale.ROOT);
                            if (lower.contains("anchor") || lower.contains("origin") || lower.contains("offset")) {
                                if (frameApi.length() > 0) frameApi.append('|');
                                frameApi.append("M:").append(method.getName()).append('/').append(method.getParameterCount());
                            }
                        }
                        Class<?> frameOwner = contraption.getClass();
                        while (frameOwner != null) {
                            for (java.lang.reflect.Field candidate : frameOwner.getDeclaredFields()) {
                                String lower = candidate.getName().toLowerCase(java.util.Locale.ROOT);
                                if (lower.contains("anchor") || lower.contains("origin") || lower.contains("offset")) {
                                    if (frameApi.length() > 0) frameApi.append('|');
                                    frameApi.append("F:").append(frameOwner.getSimpleName()).append('.').append(candidate.getName());
                                }
                            }
                            frameOwner = frameOwner.getSuperclass();
                        }
                        localSupportState = "local_feet=" + localFeet.x + "," + localFeet.y + "," + localFeet.z
                            + ";support_pos=" + supportPos.toShortString()
                            + ";support_present=" + (supportInfo != null)
                            + ";support=" + supportValue
                            + ";nearest_block=" + String.valueOf(nearestKey)
                            + ";nearest_top_distance_sq=" + nearestDistanceSq
                            + ";nearest_delta=" + nearestDelta
                            + ";block_bounds=" + minBlockX + "," + minBlockY + "," + minBlockZ + "->" + maxBlockX + "," + maxBlockY + "," + maxBlockZ
                            + ";frame_api=" + frameApi
                            + ";nearby_blocks=" + nearby
                            + ";block_count=" + blocks.size();'''
if old_state not in source:
    raise SystemExit("Phase 53 could not find local support state anchor")
source = source.replace(old_state, new_state, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 53: traced contraption block-coordinate bounds, nearest local-player delta, and anchor/origin/offset API names; read-only telemetry only")
