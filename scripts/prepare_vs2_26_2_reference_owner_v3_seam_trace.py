#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
dragger_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
resolver_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/ExternalReferenceFrameResolver.kt"

dragger = dragger_file.read_text(encoding="utf-8")
resolver = resolver_file.read_text(encoding="utf-8")

before = {
    "dragger_setPos": dragger.count("setPos("),
    "dragger_setDeltaMovement": dragger.count("setDeltaMovement("),
    "dragger_move": dragger.count(".move("),
    "dragger_teleport": dragger.count("teleport"),
    "resolver_setPos": resolver.count("setPos("),
    "resolver_setDeltaMovement": resolver.count("setDeltaMovement("),
    "resolver_move": resolver.count(".move("),
    "resolver_teleport": resolver.count("teleport"),
}

helper_anchor = '''    private fun invokeTransform(
'''
helper = '''    /** Read-only mirror of Create ContraptionCollider.worldToLocalPos for seam diagnosis only. */
    @JvmStatic
    fun currentCreateCollisionWorldToLocal(
        level: Level,
        ownerEntityId: Int,
        worldPosition: Vector3dc
    ): Vector3d? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        return try {
            val getContraption = owner.javaClass.getMethod("getContraption")
            if (getContraption.invoke(owner) == null) return null
            val abstractContraptionType = getContraption.declaringClass
            val colliderClass = Class.forName(abstractContraptionType.packageName + ".ContraptionCollider")
            val worldToLocal = colliderClass.getMethod(
                "worldToLocalPos", Vec3::class.java, abstractContraptionType
            )
            val result = worldToLocal.invoke(
                null,
                Vec3(worldPosition.x(), worldPosition.y(), worldPosition.z()),
                owner
            ) as? Vec3 ?: return null
            if (!result.x.isFinite() || !result.y.isFinite() || !result.z.isFinite()) return null
            Vector3d(result.x, result.y, result.z)
        } catch (_: ReflectiveOperationException) {
            null
        } catch (_: RuntimeException) {
            null
        }
    }

'''
if "fun currentCreateCollisionWorldToLocal" in resolver:
    raise SystemExit("V3 seam trace helper unexpectedly already present")
if resolver.count(helper_anchor) != 1:
    raise SystemExit(f"V3 seam trace expected one resolver helper anchor, found {resolver.count(helper_anchor)}")
resolver = resolver.replace(helper_anchor, helper + helper_anchor, 1)

trace_anchor = '''                        addedYRot = poseYawDelta
                        if (java.lang.Boolean.getBoolean("vs2.referenceOwnerV3Trace")) {
'''
trace_insert = '''                        addedYRot = poseYawDelta
                        if (java.lang.Boolean.getBoolean("vs2.referenceOwnerV3SeamTrace")) {
                            val createLocalInput = ExternalReferenceFrameResolver.currentCreateCollisionWorldToLocal(
                                entity.level(), externalReferenceOwnerEntityId, entityReferencePos
                            )
                            val createLocalTarget = ExternalReferenceFrameResolver.currentCreateCollisionWorldToLocal(
                                entity.level(), externalReferenceOwnerEntityId, currentWorld
                            )
                            val targetYawRadians = Math.toRadians(currentWorldYaw)
                            val targetLookWorld = Vector3d(
                                currentWorld.x() + Math.sin(targetYawRadians),
                                currentWorld.y(),
                                currentWorld.z() + Math.cos(targetYawRadians)
                            )
                            val createLocalTargetLook = ExternalReferenceFrameResolver.currentCreateCollisionWorldToLocal(
                                entity.level(), externalReferenceOwnerEntityId, targetLookWorld
                            )
                            var createTargetLocalYaw = Double.NaN
                            if (createLocalTarget != null && createLocalTargetLook != null) {
                                val dx = createLocalTargetLook.x() - createLocalTarget.x()
                                val dz = createLocalTargetLook.z() - createLocalTarget.z()
                                if (dx * dx + dz * dz > 1.0E-16) {
                                    createTargetLocalYaw = Math.atan2(dx, dz)
                                }
                            }
                            println(
                                "REFERENCE_OWNER_V3_SEAM_NATIVE player_tick=${entity.tickCount}" +
                                    " owner_id=$externalReferenceOwnerEntityId" +
                                    " world_x=${entityReferencePos.x()} world_y=${entityReferencePos.y()} world_z=${entityReferencePos.z()}" +
                                    " resolver_local_x=${localPosition?.x() ?: Double.NaN} resolver_local_y=${localPosition?.y() ?: Double.NaN} resolver_local_z=${localPosition?.z() ?: Double.NaN}" +
                                    " target_x=${currentWorld.x()} target_y=${currentWorld.y()} target_z=${currentWorld.z()}" +
                                    " added_x=${addedMovement.x()} added_y=${addedMovement.y()} added_z=${addedMovement.z()}" +
                                    " input_yaw=${entity.yRot.toDouble()} resolver_local_yaw=$previousLocalYaw" +
                                    " target_yaw=$currentWorldYaw added_yaw=$addedYRot" +
                                    " create_input_local_x=${createLocalInput?.x() ?: Double.NaN} create_input_local_y=${createLocalInput?.y() ?: Double.NaN} create_input_local_z=${createLocalInput?.z() ?: Double.NaN}" +
                                    " create_target_local_x=${createLocalTarget?.x() ?: Double.NaN} create_target_local_y=${createLocalTarget?.y() ?: Double.NaN} create_target_local_z=${createLocalTarget?.z() ?: Double.NaN}" +
                                    " create_target_local_yaw=$createTargetLocalYaw" +
                                    " gameplay_mutated=false writer=native_entity_dragger"
                            )
                        }
                        if (java.lang.Boolean.getBoolean("vs2.referenceOwnerV3Trace")) {
'''
if dragger.count(trace_anchor) != 1:
    raise SystemExit(f"V3 seam trace expected one native pose trace anchor, found {dragger.count(trace_anchor)}")
dragger = dragger.replace(trace_anchor, trace_insert, 1)

after = {
    "dragger_setPos": dragger.count("setPos("),
    "dragger_setDeltaMovement": dragger.count("setDeltaMovement("),
    "dragger_move": dragger.count(".move("),
    "dragger_teleport": dragger.count("teleport"),
    "resolver_setPos": resolver.count("setPos("),
    "resolver_setDeltaMovement": resolver.count("setDeltaMovement("),
    "resolver_move": resolver.count(".move("),
    "resolver_teleport": resolver.count("teleport"),
}
if before != after:
    raise SystemExit(f"V3 seam trace changed movement writer inventory: before={before} after={after}")

added_slice = helper + trace_insert
for forbidden in [
    "setPos(", "setDeltaMovement(", ".move(", "teleport", "setNoGravity(", "setOnGround(",
    "getContactPointMotion(", "camera.", "floorY", "wallClamp", "push(",
]:
    if forbidden in added_slice:
        raise SystemExit("V3 seam trace introduced forbidden gameplay token: " + forbidden)

for required in [
    "currentCreateCollisionWorldToLocal",
    "REFERENCE_OWNER_V3_SEAM_NATIVE",
    "create_target_local_yaw",
    "gameplay_mutated=false",
]:
    if required not in (resolver + dragger):
        raise SystemExit("V3 seam trace lost required read-only anchor: " + required)

resolver_file.write_text(resolver, encoding="utf-8")
dragger_file.write_text(dragger, encoding="utf-8")

print("REFERENCE_OWNER_V3_SEAM_TRACE read_only=true gameplay_mutated=false")
print("REFERENCE_OWNER_V3_SEAM_TRACE compares=resolver_previous_local_to_create_current_target_local native_added_delta=true yaw_local_frame=true")
