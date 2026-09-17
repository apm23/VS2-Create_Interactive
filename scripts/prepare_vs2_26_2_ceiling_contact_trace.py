#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collide = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderTrace.java"
setpos = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerSetPosTrace.java"

# Ceiling proof correlation only. Add player tick to already-existing read-only
# local-frame/collide/setPos telemetry. Later composition phases may already have
# added the same tick field, so each anchor is deliberately idempotent.
# No movement, collision, input, world, train, camera, ownership, or physics
# value is changed.
s = probe.read_text(encoding="utf-8")
ready = '"GATE_E_CLIENT_STATE player_tick={} player_pos={},{},{} player_box='
if ready not in s:
    old = '"GATE_E_CLIENT_STATE player_pos={},{},{} player_box='
    new = ready
    if old not in s:
        raise SystemExit("ceiling trace could not find GateE state format")
    s = s.replace(old, new, 1)
    old_args = '''                player.getX(), player.getY(), player.getZ(),\n                playerBox.minX'''
    new_args = '''                player.tickCount,\n                player.getX(), player.getY(), player.getZ(),\n                playerBox.minX'''
    if old_args not in s:
        raise SystemExit("ceiling trace could not find GateE state arguments")
    s = s.replace(old_args, new_args, 1)
probe.write_text(s, encoding="utf-8")

# Read-only inventory of EXISTING simplified-collider vertical clearances. This
# does not move the player, change fixture selection, modify geometry, alter
# input timing, or affect collision. It samples once and reports the tightest
# X/Z-overlapping floor/ceiling pair that can still fit the current player.
s = probe.read_text(encoding="utf-8")
marker = "GATE_E_CEILING_GEOMETRY_INVENTORY"
if marker not in s:
    anchor = '''                        double verticalGap = highestTopUnderFeet == -Double.MAX_VALUE ? Double.NaN : localFeetForCollider.y - highestTopUnderFeet;\n                        double ceilingHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + player.getBbHeight());\n                        simplifiedColliderState = "type=" + collisionListClass.getName()'''
    replacement = '''                        double verticalGap = highestTopUnderFeet == -Double.MAX_VALUE ? Double.NaN : localFeetForCollider.y - highestTopUnderFeet;\n                        double ceilingHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + player.getBbHeight());\n                        if (player.tickCount == 20) {\n                            double bestClearance = Double.POSITIVE_INFINITY;\n                            double bestHeadroom = Double.POSITIVE_INFINITY;\n                            int bestFloorIndex = -1;\n                            int bestCeilingIndex = -1;\n                            double bestOverlapCenterX = Double.NaN;\n                            double bestOverlapCenterZ = Double.NaN;\n                            double bestOverlapSpanX = Double.NaN;\n                            double bestOverlapSpanZ = Double.NaN;\n                            double requiredSpanX = (playerBox.maxX - playerBox.minX) + 0.05;\n                            double requiredSpanZ = (playerBox.maxZ - playerBox.minZ) + 0.05;\n                            for (int floorIndex = 0; floorIndex < size; floorIndex++) {\n                                double floorMinX = centerX[floorIndex] - extentsX[floorIndex];\n                                double floorMaxX = centerX[floorIndex] + extentsX[floorIndex];\n                                double floorTop = centerY[floorIndex] + extentsY[floorIndex];\n                                double floorMinZ = centerZ[floorIndex] - extentsZ[floorIndex];\n                                double floorMaxZ = centerZ[floorIndex] + extentsZ[floorIndex];\n                                for (int ceilingIndex = 0; ceilingIndex < size; ceilingIndex++) {\n                                    if (ceilingIndex == floorIndex) continue;\n                                    double ceilingBottom = centerY[ceilingIndex] - extentsY[ceilingIndex];\n                                    double clearance = ceilingBottom - floorTop;\n                                    if (clearance < player.getBbHeight() + 0.05 || clearance >= bestClearance) continue;\n                                    double ceilingMinX = centerX[ceilingIndex] - extentsX[ceilingIndex];\n                                    double ceilingMaxX = centerX[ceilingIndex] + extentsX[ceilingIndex];\n                                    double ceilingMinZ = centerZ[ceilingIndex] - extentsZ[ceilingIndex];\n                                    double ceilingMaxZ = centerZ[ceilingIndex] + extentsZ[ceilingIndex];\n                                    double overlapMinX = Math.max(floorMinX, ceilingMinX);\n                                    double overlapMaxX = Math.min(floorMaxX, ceilingMaxX);\n                                    double overlapMinZ = Math.max(floorMinZ, ceilingMinZ);\n                                    double overlapMaxZ = Math.min(floorMaxZ, ceilingMaxZ);\n                                    double overlapSpanX = overlapMaxX - overlapMinX;\n                                    double overlapSpanZ = overlapMaxZ - overlapMinZ;\n                                    if (overlapSpanX < requiredSpanX || overlapSpanZ < requiredSpanZ) continue;\n                                    bestClearance = clearance;\n                                    bestHeadroom = clearance - player.getBbHeight();\n                                    bestFloorIndex = floorIndex;\n                                    bestCeilingIndex = ceilingIndex;\n                                    bestOverlapCenterX = (overlapMinX + overlapMaxX) * 0.5;\n                                    bestOverlapCenterZ = (overlapMinZ + overlapMaxZ) * 0.5;\n                                    bestOverlapSpanX = overlapSpanX;\n                                    bestOverlapSpanZ = overlapSpanZ;\n                                }\n                            }\n                            LOGGER.info(\n                                "GATE_E_CEILING_GEOMETRY_INVENTORY player_tick={} size={} player_height={} floor_index={} ceiling_index={} clearance={} headroom={} overlap_center={},{} overlap_span={},{} read_only=true geometry_mutated=false player_mutated=false input_mutated=false",\n                                player.tickCount, size, player.getBbHeight(), bestFloorIndex, bestCeilingIndex,\n                                bestClearance, bestHeadroom, bestOverlapCenterX, bestOverlapCenterZ, bestOverlapSpanX, bestOverlapSpanZ);\n                        }\n                        simplifiedColliderState = "type=" + collisionListClass.getName()'''
    if anchor not in s:
        raise SystemExit("ceiling trace could not find Phase66 simplified-collider summary anchor")
    s = s.replace(anchor, replacement, 1)
probe.write_text(s, encoding="utf-8")

s = collide.read_text(encoding="utf-8")
ready = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}"'
if ready not in s:
    old = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",\n            index,'
    new = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",\n            index, entity.tickCount,'
    if old not in s:
        raise SystemExit("ceiling trace could not find nonzero LocalPlayer collide marker")
    s = s.replace(old, new, 1)
collide.write_text(s, encoding="utf-8")

s = setpos.read_text(encoding="utf-8")
ready = '"GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}"'
if ready not in s:
    old = '"GATE_E_LOCALPLAYER_SET_POS index={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",\n            index,'
    new = '"GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",\n            index, self.tickCount,'
    if old not in s:
        raise SystemExit("ceiling trace could not find LocalPlayer setPos marker")
    s = s.replace(old, new, 1)
setpos.write_text(s, encoding="utf-8")

for text, required in [
    (probe.read_text(encoding="utf-8"), "GATE_E_CLIENT_STATE player_tick={}"),
    (probe.read_text(encoding="utf-8"), "GATE_E_CEILING_GEOMETRY_INVENTORY"),
    (collide.read_text(encoding="utf-8"), "GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={}"),
    (setpos.read_text(encoding="utf-8"), "GATE_E_LOCALPLAYER_SET_POS index={} player_tick={}"),
]:
    if required not in text:
        raise SystemExit("ceiling trace verification failed: " + required)

print("M1_CEILING_CONTACT_CORRELATION_TRACE prepared=true read_only=true idempotent_tick_anchors=true geometry_inventory=true local_frame=create_worldToLocalPos gameplay_mutated=false collision_mutated=false input_mutated=false camera_mutated=false")
