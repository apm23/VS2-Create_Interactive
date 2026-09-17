#!/usr/bin/env python3
from pathlib import Path

# TARGETED_PROOF_TRIGGER: timeout-recovery rerun of exact-owner collision-motion candidate; observation unchanged.
# This trace remains observational; production composition supplies the candidate root correction.
ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
obb = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContinuousOBBColliderTrace.java"
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
    old_args = '''                player.getX(), player.getY(), player.getZ(),
                playerBox.minX'''
    new_args = '''                player.tickCount,
                player.getX(), player.getY(), player.getZ(),
                playerBox.minX'''
    if old_args not in s:
        raise SystemExit("ceiling trace could not find GateE state arguments")
    s = s.replace(old_args, new_args, 1)
probe.write_text(s, encoding="utf-8")

# Read-only inventory of EXISTING simplified-collider vertical clearances. This
# does not move the player, change fixture selection, modify geometry, alter
# input timing, or affect collision. The previous exact tick-20 sample could
# occur before a ready player/carriage observation, so sample the first ready
# observation in this client process instead.
s = probe.read_text(encoding="utf-8")
marker = "GATE_E_CEILING_GEOMETRY_INVENTORY"
if marker not in s:
    anchor = '''                        double verticalGap = highestTopUnderFeet == -Double.MAX_VALUE ? Double.NaN : localFeetForCollider.y - highestTopUnderFeet;
                        double ceilingHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + player.getBbHeight());
                        simplifiedColliderState = "type=" + collisionListClass.getName()'''
    replacement = '''                        double verticalGap = highestTopUnderFeet == -Double.MAX_VALUE ? Double.NaN : localFeetForCollider.y - highestTopUnderFeet;
                        double ceilingHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + player.getBbHeight());
                        if (!Boolean.getBoolean("vs2.ceilingInventoryLogged")) {
                            System.setProperty("vs2.ceilingInventoryLogged", "true");
                            double bestClearance = Double.POSITIVE_INFINITY;
                            double bestHeadroom = Double.POSITIVE_INFINITY;
                            int bestFloorIndex = -1;
                            int bestCeilingIndex = -1;
                            double bestOverlapCenterX = Double.NaN;
                            double bestOverlapCenterZ = Double.NaN;
                            double bestOverlapSpanX = Double.NaN;
                            double bestOverlapSpanZ = Double.NaN;
                            double requiredSpanX = (playerBox.maxX - playerBox.minX) + 0.05;
                            double requiredSpanZ = (playerBox.maxZ - playerBox.minZ) + 0.05;
                            for (int floorIndex = 0; floorIndex < size; floorIndex++) {
                                double floorMinX = centerX[floorIndex] - extentsX[floorIndex];
                                double floorMaxX = centerX[floorIndex] + extentsX[floorIndex];
                                double floorTop = centerY[floorIndex] + extentsY[floorIndex];
                                double floorMinZ = centerZ[floorIndex] - extentsZ[floorIndex];
                                double floorMaxZ = centerZ[floorIndex] + extentsZ[floorIndex];
                                for (int ceilingIndex = 0; ceilingIndex < size; ceilingIndex++) {
                                    if (ceilingIndex == floorIndex) continue;
                                    double ceilingBottom = centerY[ceilingIndex] - extentsY[ceilingIndex];
                                    double clearance = ceilingBottom - floorTop;
                                    if (clearance < player.getBbHeight() + 0.05 || clearance >= bestClearance) continue;
                                    double ceilingMinX = centerX[ceilingIndex] - extentsX[ceilingIndex];
                                    double ceilingMaxX = centerX[ceilingIndex] + extentsX[ceilingIndex];
                                    double ceilingMinZ = centerZ[ceilingIndex] - extentsZ[ceilingIndex];
                                    double ceilingMaxZ = centerZ[ceilingIndex] + extentsZ[ceilingIndex];
                                    double overlapMinX = Math.max(floorMinX, ceilingMinX);
                                    double overlapMaxX = Math.min(floorMaxX, ceilingMaxX);
                                    double overlapMinZ = Math.max(floorMinZ, ceilingMinZ);
                                    double overlapMaxZ = Math.min(floorMaxZ, ceilingMaxZ);
                                    double overlapSpanX = overlapMaxX - overlapMinX;
                                    double overlapSpanZ = overlapMaxZ - overlapMinZ;
                                    if (overlapSpanX < requiredSpanX || overlapSpanZ < requiredSpanZ) continue;
                                    bestClearance = clearance;
                                    bestHeadroom = clearance - player.getBbHeight();
                                    bestFloorIndex = floorIndex;
                                    bestCeilingIndex = ceilingIndex;
                                    bestOverlapCenterX = (overlapMinX + overlapMaxX) * 0.5;
                                    bestOverlapCenterZ = (overlapMinZ + overlapMaxZ) * 0.5;
                                    bestOverlapSpanX = overlapSpanX;
                                    bestOverlapSpanZ = overlapSpanZ;
                                }
                            }
                            LOGGER.info(
                                "GATE_E_CEILING_GEOMETRY_INVENTORY player_tick={} size={} player_height={} floor_index={} ceiling_index={} clearance={} headroom={} overlap_center={},{} overlap_span={},{} read_only=true geometry_mutated=false player_mutated=false input_mutated=false",
                                player.tickCount, size, player.getBbHeight(), bestFloorIndex, bestCeilingIndex,
                                bestClearance, bestHeadroom, bestOverlapCenterX, bestOverlapCenterZ, bestOverlapSpanX, bestOverlapSpanZ);
                        }
                        simplifiedColliderState = "type=" + collisionListClass.getName()'''
    if anchor not in s:
        raise SystemExit("ceiling trace could not find Phase66 simplified-collider summary anchor")
    s = s.replace(anchor, replacement, 1)
probe.write_text(s, encoding="utf-8")

# Identify the exact simplified-collider ceiling candidate used by the same
# CollisionList that Create passes into ContinuousOBBCollider. Also report the
# gap after Create's client-player 2/16-block height contraction. This is
# observational only and resolves whether a full-height overlap is still a real
# overlap for Create's actual client collision OBB.
s = probe.read_text(encoding="utf-8")
if "lowest_bottom_over_head_index=" not in s:
    old = '''                        double lowestBottomOverHead = Double.MAX_VALUE;
                        for (int i = 0; i < size; i++) {'''
    new = '''                        double lowestBottomOverHead = Double.MAX_VALUE;
                        int lowestBottomOverHeadIndex = -1;
                        for (int i = 0; i < size; i++) {'''
    if old not in s:
        raise SystemExit("ceiling trace could not find lowest overhead declaration")
    s = s.replace(old, new, 1)

    old = '''                                if (minY >= playerHeadY - 0.25 && minY < lowestBottomOverHead) lowestBottomOverHead = minY;'''
    new = '''                                if (minY >= playerHeadY - 0.25 && minY < lowestBottomOverHead) {
                                    lowestBottomOverHead = minY;
                                    lowestBottomOverHeadIndex = i;
                                }'''
    if old not in s:
        raise SystemExit("ceiling trace could not find lowest overhead update")
    s = s.replace(old, new, 1)

    old = '''                        double ceilingHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + player.getBbHeight());
                        if (!Boolean.getBoolean("vs2.ceilingInventoryLogged")) {'''
    new = '''                        double ceilingHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + player.getBbHeight());
                        double createClientCollisionHeight = playerBox.getYsize() > 1.0 ? playerBox.getYsize() - (2.0 / 16.0) : playerBox.getYsize();
                        double createClientCollisionHeadGap = lowestBottomOverHead == Double.MAX_VALUE ? Double.NaN : lowestBottomOverHead - (localFeetForCollider.y + createClientCollisionHeight);
                        String ceilingCandidate = "none";
                        if (lowestBottomOverHeadIndex >= 0) {
                            int ci = lowestBottomOverHeadIndex;
                            ceilingCandidate = "i=" + ci
                                + ",center=" + centerX[ci] + "," + centerY[ci] + "," + centerZ[ci]
                                + ",extents=" + extentsX[ci] + "," + extentsY[ci] + "," + extentsZ[ci]
                                + ",bottom=" + (centerY[ci] - extentsY[ci]);
                        }
                        if (!Boolean.getBoolean("vs2.ceilingInventoryLogged")) {'''
    if old not in s:
        raise SystemExit("ceiling trace could not find ceiling gap anchor")
    s = s.replace(old, new, 1)

    old = '''                            + ";lowest_bottom_over_head=" + lowestBottomOverHead
                            + ";ceiling_head_gap=" + ceilingHeadGap;'''
    new = '''                            + ";lowest_bottom_over_head=" + lowestBottomOverHead
                            + ";lowest_bottom_over_head_index=" + lowestBottomOverHeadIndex
                            + ";ceiling_candidate=" + ceilingCandidate
                            + ";create_client_collision_height=" + createClientCollisionHeight
                            + ";create_client_collision_head_gap=" + createClientCollisionHeadGap
                            + ";ceiling_head_gap=" + ceilingHeadGap;'''
    if old not in s:
        raise SystemExit("ceiling trace could not find simplified collider output tail")
    s = s.replace(old, new, 1)
probe.write_text(s, encoding="utf-8")

# The production OBB telemetry window currently stops at call 128. On the
# naturally successful jump that window ended at player tick 69, while the
# existing ceiling overlap occurred at ticks 73-74. Extend observation only;
# collideMany return values and all collision/gameplay state remain untouched.
s = obb.read_text(encoding="utf-8")
if "if (index > 256) return;" not in s:
    old = "        if (index > 128) return;"
    new = "        if (index > 256) return;"
    if old not in s:
        raise SystemExit("ceiling trace could not find OBB telemetry cap")
    s = s.replace(old, new, 1)
obb.write_text(s, encoding="utf-8")

s = collide.read_text(encoding="utf-8")
ready = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}"'
if ready not in s:
    old = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",
            index,'
    new = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",
            index, entity.tickCount,'
    if old not in s:
        raise SystemExit("ceiling trace could not find nonzero LocalPlayer collide marker")
    s = s.replace(old, new, 1)
collide.write_text(s, encoding="utf-8")

s = setpos.read_text(encoding="utf-8")
ready = '"GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}"'
if ready not in s:
    old = '"GATE_E_LOCALPLAYER_SET_POS index={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",
            index,'
    new = '"GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",
            index, self.tickCount,'
    if old not in s:
        raise SystemExit("ceiling trace could not find LocalPlayer setPos marker")
    s = s.replace(old, new, 1)
setpos.write_text(s, encoding="utf-8")

for text, required in [
    (probe.read_text(encoding="utf-8"), "GATE_E_CLIENT_STATE player_tick={}"),
    (probe.read_text(encoding="utf-8"), "GATE_E_CEILING_GEOMETRY_INVENTORY"),
    (probe.read_text(encoding="utf-8"), "lowest_bottom_over_head_index="),
    (probe.read_text(encoding="utf-8"), "create_client_collision_head_gap="),
    (obb.read_text(encoding="utf-8"), "if (index > 256) return;"),
    (collide.read_text(encoding="utf-8"), "GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={}"),
    (setpos.read_text(encoding="utf-8"), "GATE_E_LOCALPLAYER_SET_POS index={} player_tick={}"),
]:
    if required not in text:
        raise SystemExit("ceiling trace verification failed: " + required)

print("M1_CEILING_CONTACT_CORRELATION_TRACE prepared=true read_only=true idempotent_tick_anchors=true geometry_inventory=true exact_ceiling_candidate=true create_client_contracted_gap=true first_ready_inventory=true obb_window=256 local_frame=create_worldToLocalPos gameplay_mutated=false collision_mutated=false input_mutated=false camera_mutated=false")