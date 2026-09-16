#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
dragger_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
dragger = dragger_file.read_text(encoding="utf-8")

# Read-only root-boundary proof. Runtime 35044312977 proved that the LocalPlayer still has an active
# external owner and the scheduler calls EntityDragger at the jump tick, while the authoritative
# resolver expects a material owner-frame step and EntityDragger applies zero displacement. This trace
# distinguishes rejection by VS2's native isDraggable/vs$shouldDrag gate from a later external-owner
# resolver/application failure. It must not change the return value or any movement/collision state.
old_gate = '''    @JvmStatic
    fun isDraggable(entity: Entity): Boolean {
        return !VSEntityManager.isShipyardEntity(entity) && entity is IEntityDraggingInformationProvider && (entity as IEntityDraggingInformationProvider).`vs$shouldDrag`()
    }
'''
new_gate = '''    @JvmStatic
    fun isDraggable(entity: Entity): Boolean {
        val shipyard = VSEntityManager.isShipyardEntity(entity)
        val provider = entity as? IEntityDraggingInformationProvider
        val shouldDrag = provider?.`vs$shouldDrag`() == true
        val result = !shipyard && provider != null && shouldDrag
        if (entity is LocalPlayer && provider?.draggingInformation?.isEntityBeingDraggedByExternalReference() == true) {
            println("REFERENCE_OWNER_V2_DRAG_GATE player_tick=${entity.tickCount} external_active=true" +
                " shipyard=$shipyard provider=${provider != null} should_drag=$shouldDrag result=$result" +
                " vehicle=${entity.vehicle != null} on_ground=${entity.onGround()} read_only=true")
        }
        return result
    }
'''
if dragger.count(old_gate) != 1:
    raise SystemExit(f"expected exactly one EntityDragger isDraggable gate, found {dragger.count(old_gate)}")
dragger = dragger.replace(old_gate, new_gate, 1)

resolver_anchor = '''                    val currentWorld = localPosition?.let {
                        ExternalReferenceFrameResolver.currentLocalToWorld(
                            entity.level(), externalReferenceOwnerEntityId, it
                        )
                    }
                    if (currentWorld != null) {
                        dragTheEntity = true
                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())
'''
resolver_trace = '''                    val currentWorld = localPosition?.let {
                        ExternalReferenceFrameResolver.currentLocalToWorld(
                            entity.level(), externalReferenceOwnerEntityId, it
                        )
                    }
                    if (entity is LocalPlayer) {
                        println("REFERENCE_OWNER_V2_DRAG_EXTERNAL_BRANCH player_tick=${entity.tickCount}" +
                            " owner_id=$externalReferenceOwnerEntityId local_nonnull=${localPosition != null}" +
                            " world_nonnull=${currentWorld != null} read_only=true")
                    }
                    if (currentWorld != null) {
                        dragTheEntity = true
                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())
'''
if dragger.count(resolver_anchor) != 1:
    raise SystemExit(f"expected exactly one external-owner resolver branch, found {dragger.count(resolver_anchor)}")
dragger = dragger.replace(resolver_anchor, resolver_trace, 1)

apply_anchor = '''            if (dragTheEntity) {
'''
apply_trace = '''            if (entity is LocalPlayer && entityDraggingInformation.isEntityBeingDraggedByExternalReference()) {
                println("REFERENCE_OWNER_V2_DRAG_APPLY_GATE player_tick=${entity.tickCount}" +
                    " drag_the_entity=$dragTheEntity movement_nonnull=${addedMovement != null}" +
                    " movement=${addedMovement ?: Vector3d()} pre_tick=$preTick read_only=true")
            }
            if (dragTheEntity) {
'''
if dragger.count(apply_anchor) != 1:
    raise SystemExit(f"expected exactly one EntityDragger application gate, found {dragger.count(apply_anchor)}")
dragger = dragger.replace(apply_anchor, apply_trace, 1)

for forbidden in [
    "setPos(", "setDeltaMovement(", "teleportTo(", "setNoGravity(", "setOnGround(",
    "getContactPointMotion(", "reanchorEntityWithExternalFrame(",
]:
    if forbidden in new_gate + resolver_trace + apply_trace:
        raise SystemExit("drag-gate trace introduced forbidden mutation token: " + forbidden)

for token in [
    "REFERENCE_OWNER_V2_DRAG_GATE",
    "REFERENCE_OWNER_V2_DRAG_EXTERNAL_BRANCH",
    "REFERENCE_OWNER_V2_DRAG_APPLY_GATE",
    "return result",
]:
    if token not in dragger:
        raise SystemExit("drag-gate trace lost required token: " + token)

dragger_file.write_text(dragger, encoding="utf-8")
print("REFERENCE_OWNER_V2_DRAG_GATE_TRACE read_only=true gameplay_mutation=false")
