#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
state_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDraggingInformation.kt"
dragger_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
resolver_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/ExternalReferenceFrameResolver.kt"
probe_file = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collider_file = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"

state = state_file.read_text(encoding="utf-8")
dragger = dragger_file.read_text(encoding="utf-8")
probe = probe_file.read_text(encoding="utf-8") if probe_file.exists() else ""
collider = collider_file.read_text(encoding="utf-8") if collider_file.exists() else ""

# Hypothesis v1: VS2 owns a generalized reference-owner state/resolver keyed by the already-networked
# Create carriage Entity id. The resolver consumes Create's authoritative previous/current transforms,
# but it owns no geometry, velocity, gravity, collision response, camera forcing, or fake VS2 ship.
resolver = r'''package org.valkyrienskies.mod.common.util

import net.minecraft.world.entity.Entity
import net.minecraft.world.level.Level
import net.minecraft.world.phys.Vec3
import org.joml.Vector3d
import org.joml.Vector3dc

/**
 * VS2-owned resolver for a non-ship moving reference owner.
 *
 * The owner key is an existing networked vanilla Entity id. For Create carriage owners, VS2 asks the
 * authoritative carriage entity to map previous-world -> local and local -> current-world. This is a
 * transform seam only: it does not register geometry, synthesize velocity/gravity, or reposition an entity.
 */
object ExternalReferenceFrameResolver {
    private const val CREATE_CONTRAPTION_PREFIX = "com.zurrtum.create.content.contraptions."
    private const val CREATE_TRAIN_PREFIX = "com.zurrtum.create.content.trains."

    @JvmStatic
    fun resolveOwner(level: Level, ownerEntityId: Int): Entity? {
        val owner = level.getEntity(ownerEntityId) ?: return null
        val className = owner.javaClass.name
        if (!className.startsWith(CREATE_CONTRAPTION_PREFIX) && !className.startsWith(CREATE_TRAIN_PREFIX)) {
            return null
        }
        return try {
            owner.javaClass.getMethod("toLocalVector", Vec3::class.java, Float::class.javaPrimitiveType, Boolean::class.javaPrimitiveType)
            owner.javaClass.getMethod("toGlobalVector", Vec3::class.java, Float::class.javaPrimitiveType, Boolean::class.javaPrimitiveType)
            owner
        } catch (_: ReflectiveOperationException) {
            null
        }
    }

    @JvmStatic
    fun previousWorldToLocal(level: Level, ownerEntityId: Int, worldPosition: Vector3dc): Vector3d? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        return invokeTransform(owner, "toLocalVector", worldPosition, 0.0f, true)
    }

    @JvmStatic
    fun currentLocalToWorld(level: Level, ownerEntityId: Int, localPosition: Vector3dc): Vector3d? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        return invokeTransform(owner, "toGlobalVector", localPosition, 1.0f, false)
    }

    private fun invokeTransform(
        owner: Entity,
        methodName: String,
        position: Vector3dc,
        partialTicks: Float,
        previousAnchor: Boolean
    ): Vector3d? {
        return try {
            val method = owner.javaClass.getMethod(
                methodName,
                Vec3::class.java,
                Float::class.javaPrimitiveType,
                Boolean::class.javaPrimitiveType
            )
            val result = method.invoke(
                owner,
                Vec3(position.x(), position.y(), position.z()),
                partialTicks,
                previousAnchor
            ) as? Vec3 ?: return null
            if (!result.x.isFinite() || !result.y.isFinite() || !result.z.isFinite()) return null
            Vector3d(result.x, result.y, result.z)
        } catch (_: ReflectiveOperationException) {
            null
        } catch (_: RuntimeException) {
            null
        }
    }
}
'''
resolver_file.write_text(resolver, encoding="utf-8")

# Separate generalized owner state. Never overload lastShipStoodOn with a fake/proxy ShipId.
state_anchor = '''    var lastShipStoodOnServerWriteOnly : ShipId? = null\n'''
state_insert = state_anchor + '''\n    // Generalized non-ship reference owner. The id is an existing synchronized world Entity id;\n    // it never represents or registers a VS2 Ship. Ownership persists until acquisition/release code\n    // explicitly changes it or the resolver can no longer resolve that entity.\n    var externalReferenceOwnerEntityId: Int? = null\n        set(value) {\n            field = value\n            if (value != null) {\n                // External ownership and native VS2-ship ownership are mutually exclusive.\n                lastShipStoodOn = null\n                addedMovementLastTick = Vector3d()\n                addedYawRotLastTick = 0.0\n            }\n        }\n\n    fun isEntityBeingDraggedByExternalReference(): Boolean {\n        return externalReferenceOwnerEntityId != null && !mountedToEntity\n    }\n\n    fun isEntityBeingDraggedByReferenceOwner(): Boolean {\n        return isEntityBeingDraggedByAShip() || isEntityBeingDraggedByExternalReference()\n    }\n'''
if "externalReferenceOwnerEntityId" not in state:
    if state.count(state_anchor) != 1:
        raise SystemExit("reference-owner v1 expected one dragging-state ShipId boundary")
    state = state.replace(state_anchor, state_insert, 1)
state_file.write_text(state, encoding="utf-8")

# Feed the generalized owner into VS2's existing native drag lifecycle. We only compute addedMovement;
# the existing VS2 application path below remains the sole body-position writer. No external reanchor call.
ship_owner_anchor = '''            val shipDraggingEntity = entityDraggingInformation.lastShipStoodOn\n\n\n            // Only drag entities that aren't mounted to vehicles\n            if (shipDraggingEntity != null && entity.vehicle == null && isDraggable(entity)) {'''
external_branch = '''            val shipDraggingEntity = entityDraggingInformation.lastShipStoodOn\n            val externalReferenceOwnerEntityId = entityDraggingInformation.externalReferenceOwnerEntityId\n\n            // A Create carriage can be a VS2 reference owner without becoming a VS2 Ship. The owner\n            // supplies only authoritative previous/current frame transforms; VS2 still owns this lifecycle.\n            if (externalReferenceOwnerEntityId != null && entity.vehicle == null && isDraggable(entity)) {\n                if (entityDraggingInformation.isEntityBeingDraggedByExternalReference()) {\n                    val entityReferencePos: Vector3dc = if (preTick) {\n                        Vector3d(entity.x, entity.y, entity.z)\n                    } else {\n                        Vector3d(entity.xo, entity.yo, entity.zo)\n                    }\n                    val localPosition = ExternalReferenceFrameResolver.previousWorldToLocal(\n                        entity.level(), externalReferenceOwnerEntityId, entityReferencePos\n                    )\n                    val currentWorld = localPosition?.let {\n                        ExternalReferenceFrameResolver.currentLocalToWorld(\n                            entity.level(), externalReferenceOwnerEntityId, it\n                        )\n                    }\n                    if (currentWorld != null) {\n                        dragTheEntity = true\n                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())\n                        // v1 deliberately leaves look/yaw untouched. A later core-slice step will route\n                        // standing-player render/yaw through this same owner; no camera compensation here.\n                        addedYRot = 0.0\n                    } else {\n                        entityDraggingInformation.externalReferenceOwnerEntityId = null\n                    }\n                }\n            } else if (shipDraggingEntity != null && entity.vehicle == null && isDraggable(entity)) {'''
if "val externalReferenceOwnerEntityId = entityDraggingInformation.externalReferenceOwnerEntityId" not in dragger:
    if dragger.count(ship_owner_anchor) != 1:
        raise SystemExit("reference-owner v1 expected one native EntityDragger owner branch")
    dragger = dragger.replace(ship_owner_anchor, external_branch, 1)

# The historical helper must never compete with the generalized owner. The existing helper remains only
# for old paths while no external owner is active; this v1 does not acquire an owner yet.
helper_anchor = '''    fun reanchorEntityWithExternalFrame(entity: Entity, targetForPreviousPosition: Vec3) {\n        val addedMovement = targetForPreviousPosition.subtract(entity.xo, entity.yo, entity.zo)'''
helper_replacement = '''    fun reanchorEntityWithExternalFrame(entity: Entity, targetForPreviousPosition: Vec3) {\n        val externalOwnerActive = (entity as? IEntityDraggingInformationProvider)\n            ?.draggingInformation?.isEntityBeingDraggedByExternalReference() == true\n        if (externalOwnerActive) return\n        val addedMovement = targetForPreviousPosition.subtract(entity.xo, entity.yo, entity.zo)'''
if helper_anchor in dragger:
    dragger = dragger.replace(helper_anchor, helper_replacement, 1)
elif "externalOwnerActive" not in dragger and "reanchorEntityWithExternalFrame" in dragger:
    raise SystemExit("reference-owner v1 could not guard historical external reanchor helper")

dragger_file.write_text(dragger, encoding="utf-8")

# Mutual exclusion with Phase83: when generalized owner becomes active in a later acquisition step,
# the old bounded lease/reanchor bridge must not execute in parallel.
phase83_gate = '''            if (Boolean.getBoolean("vs2.createCarryCompat")\n                && phase83ExactBaselineCarriage'''
phase83_guarded = '''            if (Boolean.getBoolean("vs2.createCarryCompat")\n                && !((org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider) player)\n                    .getDraggingInformation().isEntityBeingDraggedByExternalReference()\n                && phase83ExactBaselineCarriage'''
if probe:
    if phase83_gate in probe:
        probe = probe.replace(phase83_gate, phase83_guarded, 1)
    elif "isEntityBeingDraggedByExternalReference()" not in probe and "GATE_E_PHASE83_CONTACT_REFRESH" in probe:
        raise SystemExit("reference-owner v1 could not guard Phase83 lease/reanchor path")
    probe_file.write_text(probe, encoding="utf-8")

# Mutual exclusion with Phase205 must happen before its marker is written, otherwise the old redirect
# would suppress Create's native contact motion even though no old reanchor was applied.
phase205_player = '''        net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;\n        if (player == null || !player.onGround() || !(carriage instanceof Entity carriageEntity)) return;'''
phase205_guarded = '''        net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;\n        if (player instanceof org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider referenceProvider\n                && referenceProvider.getDraggingInformation().isEntityBeingDraggedByExternalReference()) return;\n        if (player == null || !player.onGround() || !(carriage instanceof Entity carriageEntity)) return;'''
if collider:
    if phase205_player in collider:
        collider = collider.replace(phase205_player, phase205_guarded, 1)
    elif "isEntityBeingDraggedByExternalReference()" not in collider and "GATE_E_PHASE205_PRE_COLLISION_REANCHOR" in collider:
        raise SystemExit("reference-owner v1 could not guard Phase205 pre-collision reanchor path")
    collider_file.write_text(collider, encoding="utf-8")

# Structural proof: the new abstraction is transform-only and cannot itself chase the player.
for token in ["setPos(", "setDeltaMovement(", ".push(", "getContactPointMotion(", "gravity", "camera", "teleport"]:
    if token in resolver:
        raise SystemExit("reference-owner v1 resolver introduced forbidden mutation token: " + token)

required_state = [
    "externalReferenceOwnerEntityId",
    "isEntityBeingDraggedByExternalReference",
    "isEntityBeingDraggedByReferenceOwner",
]
required_dragger = [
    "ExternalReferenceFrameResolver.previousWorldToLocal",
    "ExternalReferenceFrameResolver.currentLocalToWorld",
    "currentWorld.sub(entityReferencePos, Vector3d())",
    "dragTheEntity = true",
    "addedYRot = 0.0",
]
for token in required_state:
    if token not in state:
        raise SystemExit("reference-owner v1 lost state anchor: " + token)
for token in required_dragger:
    if token not in dragger:
        raise SystemExit("reference-owner v1 lost EntityDragger anchor: " + token)
if "reanchorEntityWithExternalFrame(\n                        entity" in external_branch:
    raise SystemExit("reference-owner v1 must not invoke historical external reanchor")

print("REFERENCE_OWNER_V1 generalized_state=true bilateral_entity_id_resolver=true native_drag_lifecycle=true")
print("REFERENCE_OWNER_V1 fake_vs2_ship=false geometry_authority=create velocity_synthesis=false camera_compensation=false")
print("REFERENCE_OWNER_V1 acquisition_enabled=false old_reanchor_mutually_excluded_when_external_owner_active=true")
