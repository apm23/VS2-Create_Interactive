#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = probe.read_text(encoding="utf-8")

# Current-production candidate-support run 35086290531 reached a valid native jump but
# its workflow terminated before the jump-active 40-tick owner lifetime and same-owner
# grounded-native refresh seam could be observed. Publish only the existing generalized
# owner state plus player coordinates in that owner's Create local frame. Read-only only:
# no owner refresh/clear, player/train motion, collision, input, timing, or world mutation.
anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
telemetry = '''            if (productionSmokeFixture && player.tickCount >= 35 && player.tickCount <= 100) {\n                try {\n                    org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider postArcProvider =\n                        (org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider) (Object) player;\n                    org.valkyrienskies.mod.common.util.EntityDraggingInformation postArcInfo =\n                        postArcProvider.getDraggingInformation();\n                    Integer postArcOwnerId = postArcInfo.getExternalReferenceOwnerEntityId();\n                    int postArcAge = postArcInfo.getTicksSinceExternalReferenceOwner();\n                    boolean postArcJumpActive = postArcInfo.getExternalReferenceOwnerJumpActive();\n                    int postArcLimit = postArcJumpActive\n                        ? 40 : org.valkyrienskies.mod.common.util.EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES;\n                    boolean postArcAgeWithinLifetime = postArcOwnerId != null && postArcAge < postArcLimit;\n                    net.minecraft.world.entity.Entity postArcOwnerEntity = postArcOwnerId == null\n                        ? null : client.level.getEntity(postArcOwnerId);\n                    String postArcOwnerLocal = "unresolved";\n                    if (postArcOwnerEntity != null) {\n                        try {\n                            java.lang.reflect.Method postArcToLocal = postArcOwnerEntity.getClass().getMethod(\n                                "toLocalVector", net.minecraft.world.phys.Vec3.class, float.class);\n                            net.minecraft.world.phys.Vec3 postArcLocal = (net.minecraft.world.phys.Vec3) postArcToLocal.invoke(\n                                postArcOwnerEntity, player.position(), 0.0f);\n                            postArcOwnerLocal = postArcLocal.x + "," + postArcLocal.y + "," + postArcLocal.z;\n                        } catch (ReflectiveOperationException | RuntimeException postArcLocalException) {\n                            postArcOwnerLocal = "error=" + postArcLocalException.getClass().getSimpleName();\n                        }\n                    }\n                    LOGGER.info(\n                        "REFERENCE_OWNER_V2_POST_ARC_STATE player_tick={} owner_id={} owner_age={} jump_active={} lifetime_limit={} age_within_lifetime={} on_ground={} delta_y={} owner_entity_present={} owner_local={} read_only=true",\n                        player.tickCount, postArcOwnerId == null ? -1 : postArcOwnerId, postArcAge,\n                        postArcJumpActive, postArcLimit, postArcAgeWithinLifetime, player.onGround(),\n                        player.getDeltaMovement().y, postArcOwnerEntity != null, postArcOwnerLocal);\n                } catch (RuntimeException postArcException) {\n                    LOGGER.info(\n                        "REFERENCE_OWNER_V2_POST_ARC_STATE player_tick={} error={} read_only=true",\n                        player.tickCount, postArcException.getClass().getSimpleName());\n                }\n            }\n\n''' + anchor

if "REFERENCE_OWNER_V2_POST_ARC_STATE" not in source:
    if anchor not in source:
        raise SystemExit("post-arc owner trace could not find Gate E client-state anchor")
    source = source.replace(anchor, telemetry, 1)

required = [
    "REFERENCE_OWNER_V2_POST_ARC_STATE",
    "getExternalReferenceOwnerEntityId()",
    "getTicksSinceExternalReferenceOwner()",
    "getExternalReferenceOwnerJumpActive()",
    "TICKS_TO_DRAG_ENTITIES",
    "toLocalVector",
    "age_within_lifetime={}",
    "owner_local={}",
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("post-arc owner trace lost telemetry anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "refreshExternalReferenceOwner(", "clearExternalReferenceOwner(",
    "setVelocity(", "setNoGravity(", "setOnGround(", "keyUp.setDown(",
    "setBlock(", ".put(", ".remove(",
]:
    if forbidden in telemetry:
        raise SystemExit("post-arc owner trace introduced forbidden mutation: " + forbidden)

probe.write_text(source, encoding="utf-8")
print("REFERENCE_OWNER_V2_POST_ARC_TRACE prepared=true read_only=true owner_state_only=true")
