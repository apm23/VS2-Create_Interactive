#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
dragger_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
dragger = dragger_file.read_text(encoding="utf-8")

# Read-only root-boundary proof. The native isDraggable/vs$shouldDrag gate was proven open in
# run 35045444238. Trace the already-existing external-owner calculated step and VS2 body writer
# without changing ownership, movement, collision, gravity, yaw, camera, or writer semantics.
setpos_before = dragger.count("entity.setPos(")
bbox_before = dragger.count("entity.boundingBox =")

calc_anchor = '''                    if (currentWorld != null) {
                        dragTheEntity = true
                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())
                        // v1 deliberately leaves look/yaw untouched. A later core-slice step will route
'''
calc_trace = '''                    if (currentWorld != null) {
                        dragTheEntity = true
                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())
                        if (entity is LocalPlayer) {
                            val traceMovement = addedMovement ?: Vector3d(Double.NaN, Double.NaN, Double.NaN)
                            println("REFERENCE_OWNER_V2_DRAG_APPLY_CALC player_tick=${entity.tickCount}" +
                                " pre_tick=$preTick owner_id=$externalReferenceOwnerEntityId" +
                                " movement_x=${traceMovement.x()} movement_y=${traceMovement.y()} movement_z=${traceMovement.z()}" +
                                " ref_x=${entityReferencePos.x()} ref_y=${entityReferencePos.y()} ref_z=${entityReferencePos.z()}" +
                                " current_x=${currentWorld.x()} current_y=${currentWorld.y()} current_z=${currentWorld.z()}" +
                                " on_ground=${entity.onGround()} read_only=true")
                        }
                        // v1 deliberately leaves look/yaw untouched. A later core-slice step will route
'''
if dragger.count(calc_anchor) != 1:
    raise SystemExit(f"expected exactly one external-owner calc anchor, found {dragger.count(calc_anchor)}")
dragger = dragger.replace(calc_anchor, calc_trace, 1)

guard_anchor = '''            if (dragTheEntity && addedMovement != null && addedMovement.isFinite && addedYRot.isFinite()) {
'''
guard_trace = '''            if (entity is LocalPlayer && entityDraggingInformation.isEntityBeingDraggedByExternalReference()) {
                val traceMovement = addedMovement ?: Vector3d(Double.NaN, Double.NaN, Double.NaN)
                println("REFERENCE_OWNER_V2_DRAG_APPLY_PRE player_tick=${entity.tickCount}" +
                    " pre_tick=$preTick drag=$dragTheEntity movement_nonnull=${addedMovement != null}" +
                    " movement_x=${traceMovement.x()} movement_y=${traceMovement.y()} movement_z=${traceMovement.z()}" +
                    " pos_x=${entity.x} pos_y=${entity.y} pos_z=${entity.z}" +
                    " on_ground=${entity.onGround()} read_only=true")
            }
            if (dragTheEntity && addedMovement != null && addedMovement.isFinite && addedYRot.isFinite()) {
'''
if dragger.count(guard_anchor) != 1:
    raise SystemExit(f"expected exactly one VS2 body apply guard, found {dragger.count(guard_anchor)}")
dragger = dragger.replace(guard_anchor, guard_trace, 1)

setpos_anchor = '''                entity.setPos(
                    entity.x + addedMovement.x(),
                    entity.y + addedMovement.y(),
                    entity.z + addedMovement.z()
                )
'''
setpos_trace = '''                entity.setPos(
                    entity.x + addedMovement.x(),
                    entity.y + addedMovement.y(),
                    entity.z + addedMovement.z()
                )
                if (entity is LocalPlayer && entityDraggingInformation.isEntityBeingDraggedByExternalReference()) {
                    println("REFERENCE_OWNER_V2_DRAG_APPLY_POST player_tick=${entity.tickCount}" +
                        " pre_tick=$preTick movement_x=${addedMovement.x()} movement_y=${addedMovement.y()} movement_z=${addedMovement.z()}" +
                        " pos_x=${entity.x} pos_y=${entity.y} pos_z=${entity.z}" +
                        " on_ground=${entity.onGround()} read_only=true")
                }
'''
if dragger.count(setpos_anchor) != 1:
    raise SystemExit(f"expected exactly one VS2 setPos writer anchor, found {dragger.count(setpos_anchor)}")
dragger = dragger.replace(setpos_anchor, setpos_trace, 1)

if dragger.count("entity.setPos(") != setpos_before:
    raise SystemExit("read-only trace changed setPos writer count")
if dragger.count("entity.boundingBox =") != bbox_before:
    raise SystemExit("read-only trace changed boundingBox writer count")

for token in [
    "REFERENCE_OWNER_V2_DRAG_APPLY_CALC",
    "REFERENCE_OWNER_V2_DRAG_APPLY_PRE",
    "REFERENCE_OWNER_V2_DRAG_APPLY_POST",
]:
    if token not in dragger:
        raise SystemExit("drag-apply trace lost required token: " + token)

dragger_file.write_text(dragger, encoding="utf-8")
print("REFERENCE_OWNER_V2_DRAG_APPLY_TRACE read_only=true gameplay_mutation=false")
