#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream"
CREATE = ROOT / "create-source"

create_collider = CREATE / "src/main/java/com/zurrtum/create/content/contraptions/ContraptionCollider.java"
compat_collider = UPSTREAM / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"
render_path = UPSTREAM / "common/src/main/java/org/valkyrienskies/mod/mixin/client/renderer/MixinGameRenderer.java"
v2_generator = ROOT / "scripts/prepare_vs2_26_2_reference_owner_v2.py"

for path in (create_collider, compat_collider, render_path, v2_generator):
    if not path.exists():
        raise SystemExit(f"SOURCE_MAP missing required source: {path}")

create = create_collider.read_text(encoding="utf-8")
compat = compat_collider.read_text(encoding="utf-8")
render = render_path.read_text(encoding="utf-8")
generator = v2_generator.read_text(encoding="utf-8")

# Create's authoritative wall/ceiling response chain. This is a source map only: it proves
# where horizontal/vertical OBB results are consumed, not that a particular runtime contact
# produced the right result.
create_required = {
    "current_collision_local_transform": "getWorldToLocalTranslation(entity, anchorVec, rotationMatrix, yawOffset)" in create,
    "obb_solver": "ContinuousOBBCollider.collideMany" in create,
    "collision_normal": "collisionResult.normal" in create,
    "collision_response": "collisionResult.collisionResponse" in create,
    "surface_response": "collisionResult.surfaceCollision" in create,
    "temporal_response": "collisionResult.temporalResponse" in create,
    "hard_collision_gate": "boolean hardCollision = !totalResponse.equals(Vec3.ZERO)" in create,
    "wall_x_clip": "entityMotion = entityMotion.multiply(0, 1, 1)" in create,
    "ceiling_floor_y_clip": "entityMotion = entityMotion.multiply(1, 0, 1).add(0, contraptionMotion.y, 0)" in create,
    "wall_z_clip": "entityMotion = entityMotion.multiply(1, 1, 0)" in create,
    "response_move": "Vec3 allowedMovement = collide(totalResponse, entity)" in create,
    "response_setpos": "entityPosition.x + allowedMovement.x" in create and "entityPosition.y + allowedMovement.y" in create,
    "surface_contact_motion": "contactPointMotion = contraptionEntity.getContactPointMotion(entityPosition)" in create,
}
missing_create = [k for k, ok in create_required.items() if not ok]
if missing_create:
    raise SystemExit("SOURCE_MAP lost Create wall/ceiling response anchors: " + ",".join(missing_create))

# Current V2 must leave Create collision authority intact. The historical pre-OBB external
# reanchor/contact-motion suppression methods are removed when V2 is composed.
legacy_methods_present = (
    "private static void vs2$preCollisionExternalFrame" in compat
    or "private static Vec3 vs2$avoidDuplicateExternalFrameCarry" in compat
)
if legacy_methods_present:
    raise SystemExit("SOURCE_MAP current V2 unexpectedly retained legacy Phase205 collision authority")
if "legacy Phase205 external reanchor and contact-motion suppression removed" not in compat:
    raise SystemExit("SOURCE_MAP missing V2 legacy-collision-removal marker")

# External-owner render interpolation is wired, but the V2 generator explicitly avoids mounted
# camera ownership/counter-rotation. This does not prove camera runtime correctness; it localizes
# the next read-only measurement to player-vs-camera positional frame during turns.
render_required = {
    "external_owner_render_gate": "externalReferenceOwnerPresent" in render,
    "external_owner_render_state": "isEntityBeingDraggedByExternalReference" in render,
    "render_uses_drag_step": "getAddedMovementLastTick" in render,
    "render_interpolated_position": "entityShouldBeHerePreTransform" in render,
}
missing_render = [k for k, ok in render_required.items() if not ok]
if missing_render:
    raise SystemExit("SOURCE_MAP lost external-owner render anchors: " + ",".join(missing_render))

if "mounted-camera code is not entered or modified" not in generator:
    raise SystemExit("SOURCE_MAP generator no longer documents mounted-camera exclusion")

owner_tokens = (
    "getExternalReferenceOwnerEntityId",
    "isEntityBeingDraggedByExternalReference",
    "ExternalReferenceFrameResolver",
)
camera_candidates = []
camera_owner_files = []
for source_root in (UPSTREAM / "common/src", UPSTREAM / "fabric/src"):
    for path in source_root.rglob("*"):
        if not path.is_file() or path.suffix not in {".java", ".kt"}:
            continue
        rel = path.relative_to(UPSTREAM).as_posix()
        if "camera" not in rel.lower():
            continue
        camera_candidates.append(rel)
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(token in text for token in owner_tokens):
            camera_owner_files.append(rel)

classification = "CREATE_WALL_CEILING_RESPONSE_WRITERS_PRESENT_CAMERA_POSITIONAL_OWNER_UNWIRED"
print(
    "M1_WALL_CEILING_CAMERA_SOURCE_MAP "
    f"classification={classification} "
    "create_current_world_to_local=true obb_solver=true "
    "horizontal_wall_axis_response=true vertical_y_response=true "
    "create_response_setpos_writer=true surface_contact_motion_writer=true "
    "legacy_precollision_external_reanchor_removed=true create_collision_authority_preserved=true "
    "external_owner_render_interpolation=true "
    f"camera_candidates={len(camera_candidates)} camera_owner_files={len(camera_owner_files)} "
    "mounted_camera_untouched=true "
    "wall_ceiling_runtime_contact_still_unproven=true turn_camera_runtime_still_unproven=true "
    "read_only=true gameplay_unchanged=true final_ready=false"
)
if camera_owner_files:
    print("M1_CAMERA_OWNER_FILES " + " ".join(camera_owner_files))
else:
    print("M1_CAMERA_OWNER_FILES none")
