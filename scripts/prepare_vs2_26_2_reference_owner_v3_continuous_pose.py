#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
state_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDraggingInformation.kt"
dragger_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
resolver_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/ExternalReferenceFrameResolver.kt"
authority_file = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinExternalReferenceOwnerCreateCarry.java"
probe_file = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

state = state_file.read_text(encoding="utf-8")
dragger = dragger_file.read_text(encoding="utf-8")
resolver = resolver_file.read_text(encoding="utf-8")
authority = authority_file.read_text(encoding="utf-8")
probe = probe_file.read_text(encoding="utf-8")

before_writer_counts = {
    "setPos": dragger.count("entity.setPos("),
    "setDeltaMovement": dragger.count("setDeltaMovement("),
    "teleport": dragger.count("teleport"),
}

# V3 root hypothesis:
# - External carriage ownership is a frame membership state, not a countdown lease.
# - Once acquired from Create's proven physical/native contact, ownership survives arbitrary airborne time.
# - Release is only owner disappearance or settled grounded loss; there is no jump flag or 25/40-tick cap.
# - The external EntityDragger branch applies one atomic previous-owner -> current-owner POSE transform:
#   position and yaw are derived from the same owner lifecycle. Create remains the collision authority.
# - No second movement writer, velocity synthesis, gravity, clamp, camera forcing or fake Ship is added.

old_state_field = "    var externalReferenceOwnerJumpActive: Boolean = false\n"
if state.count(old_state_field) != 1:
    raise SystemExit(f"V3 expected one jump-active field, found {state.count(old_state_field)}")
state = state.replace(old_state_field, "", 1)

old_drag_gate = '''    fun externalReferenceOwnerLifetimeLimit(): Int {
        return if (externalReferenceOwnerJumpActive) 40 else TICKS_TO_DRAG_ENTITIES
    }

    fun isEntityBeingDraggedByExternalReference(): Boolean {
        return externalReferenceOwnerEntityId != null &&
            ticksSinceExternalReferenceOwner < externalReferenceOwnerLifetimeLimit() && !mountedToEntity
    }
'''
new_drag_gate = '''    fun isEntityBeingDraggedByExternalReference(): Boolean {
        return externalReferenceOwnerEntityId != null && !mountedToEntity
    }
'''
if state.count(old_drag_gate) != 1:
    raise SystemExit(f"V3 expected one TTL drag gate, found {state.count(old_drag_gate)}")
state = state.replace(old_drag_gate, new_drag_gate, 1)

reset_line = "        externalReferenceOwnerJumpActive = false\n"
if state.count(reset_line) < 2:
    raise SystemExit(f"V3 expected jump-active resets in refresh+clear, found {state.count(reset_line)}")
state = state.replace(reset_line, "")

# Remove the jump latch / cap from the lifecycle. Age remains diagnostics plus a short contact-loss
# debounce only; it is never an absolute ownership lifetime. Vanilla onGround is known to stay true
# during this fixture's real upward jump arc, so a release is "settled grounded loss" only when
# vertical motion has also stopped. This keeps the same owner through actual airborne motion without
# introducing a jump flag/window, synthetic velocity, or another movement writer.
old_motion_latch = '''                val nativeUpwardMotion = entity.deltaMovement.y > 1.0E-5
                if (nativeUpwardMotion) {
                    entityDraggingInformation.externalReferenceOwnerJumpActive = true
                }
                val groundedContactExpired = entity.onGround() &&
                    !entityDraggingInformation.externalReferenceOwnerJumpActive &&
                    entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
                val ownerExpired = entityDraggingInformation.ticksSinceExternalReferenceOwner >= entityDraggingInformation.externalReferenceOwnerLifetimeLimit()
                if (!ownerStillResolvable || groundedContactExpired || ownerExpired) {
                    entityDraggingInformation.clearExternalReferenceOwner()
                }
'''
new_motion_latch = '''                val hasVerticalMotion = kotlin.math.abs(entity.deltaMovement.y) > 1.0E-5
                val settledGroundedContactLost =
                    entity.onGround() && !hasVerticalMotion &&
                    entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
                if (!ownerStillResolvable || settledGroundedContactLost) {
                    entityDraggingInformation.clearExternalReferenceOwner()
                }
'''
if dragger.count(old_motion_latch) != 1:
    raise SystemExit(f"V3 expected one TTL/jump lifecycle block, found {dragger.count(old_motion_latch)}")
dragger = dragger.replace(old_motion_latch, new_motion_latch, 1)

# Previous-frame yaw -> owner-local. Translation cancels by transforming two points with the exact same
# previous Create transform, matching the positional previousWorldToLocal/currentLocalToWorld pair.
yaw_anchor = '''    @JvmStatic
    fun currentWorldYawToLocal(level: Level, ownerEntityId: Int, worldYawDegrees: Double): Double? {
'''
previous_yaw = '''    @JvmStatic
    fun previousWorldYawToLocal(level: Level, ownerEntityId: Int, worldYawDegrees: Double): Double? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        val origin = Vector3d(owner.xo, owner.yo, owner.zo)
        val yaw = Math.toRadians(worldYawDegrees)
        val look = Vector3d(origin.x() + Math.sin(yaw), origin.y(), origin.z() + Math.cos(yaw))
        val localOrigin = invokeTransform(owner, "toLocalVector", origin, 0.0f, true) ?: return null
        val localLook = invokeTransform(owner, "toLocalVector", look, 0.0f, true) ?: return null
        val direction = localLook.sub(localOrigin, Vector3d())
        if (!direction.x().isFinite() || !direction.z().isFinite() ||
            direction.x() * direction.x() + direction.z() * direction.z() <= 1.0E-16) return null
        return Math.atan2(direction.x(), direction.z())
    }

'''
if "fun previousWorldYawToLocal" in resolver:
    raise SystemExit("V3 previous yaw helper unexpectedly already exists")
if resolver.count(yaw_anchor) != 1:
    raise SystemExit(f"V3 expected one current yaw helper anchor, found {resolver.count(yaw_anchor)}")
resolver = resolver.replace(yaw_anchor, previous_yaw + yaw_anchor, 1)

old_external_pose = '''                    if (currentWorld != null) {
                        dragTheEntity = true
                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())
                        // v1 deliberately leaves look/yaw untouched. A later core-slice step will route
                        // standing-player render/yaw through this same owner; no camera compensation here.
                        addedYRot = 0.0
                    } else {
                        entityDraggingInformation.externalReferenceOwnerEntityId = null
                    }
'''
new_external_pose = '''                    val previousLocalYaw = ExternalReferenceFrameResolver.previousWorldYawToLocal(
                        entity.level(), externalReferenceOwnerEntityId, entity.yRot.toDouble()
                    )
                    val currentWorldYaw = previousLocalYaw?.let {
                        ExternalReferenceFrameResolver.currentLocalYawToWorld(
                            entity.level(), externalReferenceOwnerEntityId, it
                        )
                    }
                    if (currentWorld != null && currentWorldYaw != null) {
                        dragTheEntity = true
                        addedMovement = currentWorld.sub(entityReferencePos, Vector3d())
                        var poseYawDelta = currentWorldYaw - entity.yRot.toDouble()
                        while (poseYawDelta <= -180.0) poseYawDelta += 360.0
                        while (poseYawDelta > 180.0) poseYawDelta -= 360.0
                        addedYRot = poseYawDelta
                        if (java.lang.Boolean.getBoolean("vs2.referenceOwnerV3Trace")) {
                            println(
                                "REFERENCE_OWNER_V3_CONTINUOUS_POSE player_tick=${entity.tickCount}" +
                                    " owner_id=$externalReferenceOwnerEntityId" +
                                    " owner_age=${entityDraggingInformation.ticksSinceExternalReferenceOwner}" +
                                    " on_ground=${entity.onGround()}" +
                                    " yaw_delta=$addedYRot" +
                                    " previous_local_yaw=$previousLocalYaw" +
                                    " current_world_yaw=$currentWorldYaw" +
                                    " writer=native_entity_dragger"
                            )
                        }
                    } else {
                        entityDraggingInformation.clearExternalReferenceOwner()
                    }
'''
if dragger.count(old_external_pose) != 1:
    raise SystemExit(f"V3 expected one external pose branch, found {dragger.count(old_external_pose)}")
dragger = dragger.replace(old_external_pose, new_external_pose, 1)

# Remove the second V2 jump/TTL refresh path in GateEClientProbe. It is neither acquisition nor collision;
# under V3 it would be duplicate lease authority. Strict physical-support acquisition remains untouched.
probe_marker = 'REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH'
marker_index = probe.find(probe_marker)
if marker_index < 0:
    raise SystemExit("V3 expected V2 native grounded refresh marker in probe")
probe_if = probe.rfind('            if (phase83ExactBaselineCarriage', 0, marker_index)
if probe_if < 0:
    raise SystemExit("V3 could not locate V2 probe refresh block start")

def java_block_end(source: str, statement_start: int) -> int:
    open_brace = source.find('{', statement_start)
    if open_brace < 0:
        raise SystemExit("V3 probe refresh block has no opening brace")
    depth = 0
    state_name = "normal"
    i = open_brace
    while i < len(source):
        c = source[i]
        n = source[i + 1] if i + 1 < len(source) else ""
        if state_name == "normal":
            if c == '"':
                state_name = "string"
            elif c == "'":
                state_name = "char"
            elif c == '/' and n == '/':
                state_name = "line_comment"; i += 1
            elif c == '/' and n == '*':
                state_name = "block_comment"; i += 1
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i + 1
        elif state_name == "string":
            if c == '\\':
                i += 1
            elif c == '"':
                state_name = "normal"
        elif state_name == "char":
            if c == '\\':
                i += 1
            elif c == "'":
                state_name = "normal"
        elif state_name == "line_comment":
            if c == '\n':
                state_name = "normal"
        elif state_name == "block_comment":
            if c == '*' and n == '/':
                state_name = "normal"; i += 1
        i += 1
    raise SystemExit("V3 probe refresh block has no matching close")

probe_end = java_block_end(probe, probe_if)
if not (probe_if < marker_index < probe_end):
    raise SystemExit("V3 probe marker escaped selected refresh block")
probe = probe[:probe_if] + '''            // REFERENCE_OWNER_V3: no jump/TTL refresh lease.
            // Strict support/contact acquisition above owns entry; continuous VS2 frame state owns retention.

''' + probe[probe_end:]

# Exact-owner Create contact remains collision-authoritative, but it is no longer a jump/TTL lease refresh.
old_authority_refresh = '''        boolean groundedExactOwnerContact = exactExternalOwner && player.onGround();
        boolean jumpLandingAfterOrdinaryCap = groundedExactOwnerContact
            && dragging.getExternalReferenceOwnerJumpActive()
            && dragging.getTicksSinceExternalReferenceOwner()
                >= org.valkyrienskies.mod.common.util.EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES;
        boolean settledSameOwnerContact = groundedExactOwnerContact
            && !dragging.getExternalReferenceOwnerJumpActive();
        if (jumpLandingAfterOrdinaryCap || settledSameOwnerContact) {
            int ageBeforeRefresh = dragging.getTicksSinceExternalReferenceOwner();
            dragging.refreshExternalReferenceOwner(carriageEntity.getId());
            VS2_REFERENCE_OWNER_AUTHORITY.info(
                "REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH player_tick={} carriage_id={} " +
                    "jump_landing_after_ordinary_cap={} settled_same_owner_contact={} " +
                    "physical_support=unknown recent_native_contact=unknown owner_key=entity_id " +
                    "source=create_contact_carry age_before_refresh={}",
                player.tickCount,
                carriageEntity.getId(),
                jumpLandingAfterOrdinaryCap,
                settledSameOwnerContact,
                ageBeforeRefresh
            );
        }
'''
new_authority_refresh = '''        boolean groundedExactOwnerContact = exactExternalOwner && player.onGround();
        if (groundedExactOwnerContact) {
            int ageBeforeRefresh = dragging.getTicksSinceExternalReferenceOwner();
            dragging.refreshExternalReferenceOwner(carriageEntity.getId());
            VS2_REFERENCE_OWNER_AUTHORITY.info(
                "REFERENCE_OWNER_V3_GROUNDED_OWNER_CONFIRMED player_tick={} carriage_id={} " +
                    "continuous_owner=true source=create_contact_carry age_before_refresh={}",
                player.tickCount,
                carriageEntity.getId(),
                ageBeforeRefresh
            );
        }
'''
if authority.count(old_authority_refresh) != 1:
    raise SystemExit(f"V3 expected one jump/TTL authority refresh block, found {authority.count(old_authority_refresh)}")
authority = authority.replace(old_authority_refresh, new_authority_refresh, 1)

combined = state + dragger + authority + probe
for forbidden_old in [
    "externalReferenceOwnerLifetimeLimit",
    "externalReferenceOwnerJumpActive",
    "getExternalReferenceOwnerJumpActive",
    "jumpLandingAfterOrdinaryCap",
    "jump_landing_after_ordinary_cap",
]:
    if forbidden_old in combined:
        raise SystemExit("V3 retained old lease/jump workaround: " + forbidden_old)

for required in [
    "fun isEntityBeingDraggedByExternalReference(): Boolean",
    "externalReferenceOwnerEntityId != null && !mountedToEntity",
    "fun previousWorldYawToLocal",
    "currentLocalYawToWorld",
    "REFERENCE_OWNER_V3_CONTINUOUS_POSE",
    "REFERENCE_OWNER_V3_GROUNDED_OWNER_CONFIRMED",
]:
    if required not in (state + dragger + resolver + authority + probe):
        raise SystemExit("V3 lost required continuous-pose anchor: " + required)

after_writer_counts = {
    "setPos": dragger.count("entity.setPos("),
    "setDeltaMovement": dragger.count("setDeltaMovement("),
    "teleport": dragger.count("teleport"),
}
if before_writer_counts != after_writer_counts:
    raise SystemExit(
        f"V3 changed EntityDragger movement-writer inventory: before={before_writer_counts} after={after_writer_counts}"
    )

new_slice = previous_yaw + new_external_pose + new_motion_latch + new_authority_refresh
for forbidden in [
    "setPos(", "setDeltaMovement(", ".move(", "teleport", "setNoGravity(", "setOnGround(",
    "getContactPointMotion(", "camera.", "floorY", "wallClamp", "push(",
]:
    if forbidden in new_slice:
        raise SystemExit("V3 root slice introduced forbidden authority token: " + forbidden)

state_file.write_text(state, encoding="utf-8")
dragger_file.write_text(dragger, encoding="utf-8")
resolver_file.write_text(resolver, encoding="utf-8")
authority_file.write_text(authority, encoding="utf-8")
probe_file.write_text(probe, encoding="utf-8")

print("REFERENCE_OWNER_V3 continuous_owner=true fixed_ttl=false jump_lease=false")
print("REFERENCE_OWNER_V3 atomic_previous_to_current_pose=true position=true yaw=true")
print("REFERENCE_OWNER_V3 create_collision_geometry_authoritative=true added_body_writer=false synthetic_velocity=false camera_forcing=false")
