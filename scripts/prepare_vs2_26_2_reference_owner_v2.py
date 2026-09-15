#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
state_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDraggingInformation.kt"
dragger_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
resolver_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/ExternalReferenceFrameResolver.kt"
lerper_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityLerper.kt"
local_packet_file = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/feature/entity_movement_packets/MixinLocalPlayer.java"
network_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/networking/VSGamePackets.kt"
reference_packet_file = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/networking/PacketPlayerReferenceMotion.kt"
render_file = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/renderer/MixinGameRenderer.java"
probe_file = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collider_file = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"

state = state_file.read_text(encoding="utf-8")
dragger = dragger_file.read_text(encoding="utf-8")
resolver = resolver_file.read_text(encoding="utf-8")
lerper = lerper_file.read_text(encoding="utf-8")
local_packet = local_packet_file.read_text(encoding="utf-8")
network = network_file.read_text(encoding="utf-8")
render = render_file.read_text(encoding="utf-8")
probe = probe_file.read_text(encoding="utf-8")
collider = collider_file.read_text(encoding="utf-8")

# V2 hypothesis: the already-proven Create carriage Entity id is promoted from passive resolver input
# to a single VS2-owned reference-owner lifecycle spanning acquisition, body carry, client->server
# relative position/yaw, server world resolution, and standing-player render interpolation. Create keeps
# all collision/gameplay geometry. No fake ShipId, proxy ship, synthetic velocity, gravity, clamp, or
# camera counter-rotation is introduced.

# -----------------------------------------------------------------------------
# 1) Persistent external-owner lifetime/state.
# -----------------------------------------------------------------------------
old_external_state = '''    var externalReferenceOwnerEntityId: Int? = null
        set(value) {
            field = value
            if (value != null) {
                // External ownership and native VS2-ship ownership are mutually exclusive.
                lastShipStoodOn = null
                addedMovementLastTick = Vector3d()
                addedYawRotLastTick = 0.0
            }
        }

    fun isEntityBeingDraggedByExternalReference(): Boolean {
        return externalReferenceOwnerEntityId != null && !mountedToEntity
    }

    fun isEntityBeingDraggedByReferenceOwner(): Boolean {
        return isEntityBeingDraggedByAShip() || isEntityBeingDraggedByExternalReference()
    }
'''
new_external_state = '''    var externalReferenceOwnerEntityId: Int? = null
        set(value) {
            field = value
            if (value != null) {
                // External ownership and native VS2-ship ownership are mutually exclusive.
                lastShipStoodOn = null
                addedMovementLastTick = Vector3d()
                addedYawRotLastTick = 0.0
            }
        }
    var ticksSinceExternalReferenceOwner: Int = 0
    var serverRelativeExternalPosition: Vector3dc? = null
    var serverRelativeExternalYaw: Double? = null
    var serverResolvedExternalYaw: Double? = null

    fun refreshExternalReferenceOwner(ownerEntityId: Int) {
        if (externalReferenceOwnerEntityId != ownerEntityId) {
            externalReferenceOwnerEntityId = ownerEntityId
        }
        ticksSinceExternalReferenceOwner = 0
    }

    fun clearExternalReferenceOwner() {
        externalReferenceOwnerEntityId = null
        ticksSinceExternalReferenceOwner = 0
        serverRelativeExternalPosition = null
        serverRelativeExternalYaw = null
        serverResolvedExternalYaw = null
        addedMovementLastTick = Vector3d()
        addedYawRotLastTick = 0.0
    }

    fun isEntityBeingDraggedByExternalReference(): Boolean {
        return externalReferenceOwnerEntityId != null &&
            ticksSinceExternalReferenceOwner < TICKS_TO_DRAG_ENTITIES && !mountedToEntity
    }

    fun isEntityBeingDraggedByReferenceOwner(): Boolean {
        return isEntityBeingDraggedByAShip() || isEntityBeingDraggedByExternalReference()
    }
'''
if "ticksSinceExternalReferenceOwner" not in state:
    if state.count(old_external_state) != 1:
        raise SystemExit("reference-owner v2 lost v1 external-owner state anchor")
    state = state.replace(old_external_state, new_external_state, 1)
state_file.write_text(state, encoding="utf-8")

# -----------------------------------------------------------------------------
# 2) Bilateral current-frame + yaw transforms. These are pure transform helpers.
# -----------------------------------------------------------------------------
resolver_anchor = '''    @JvmStatic
    fun currentLocalToWorld(level: Level, ownerEntityId: Int, localPosition: Vector3dc): Vector3d? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        return invokeTransform(owner, "toGlobalVector", localPosition, 1.0f, false)
    }

    private fun invokeTransform('''
resolver_extension = '''    @JvmStatic
    fun currentLocalToWorld(level: Level, ownerEntityId: Int, localPosition: Vector3dc): Vector3d? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        return invokeTransform(owner, "toGlobalVector", localPosition, 1.0f, false)
    }

    @JvmStatic
    fun currentWorldToLocal(level: Level, ownerEntityId: Int, worldPosition: Vector3dc): Vector3d? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        return invokeTransform(owner, "toLocalVector", worldPosition, 1.0f, false)
    }

    @JvmStatic
    fun currentWorldYawToLocal(level: Level, ownerEntityId: Int, worldYawDegrees: Double): Double? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        val origin = Vector3d(owner.x, owner.y, owner.z)
        val yaw = Math.toRadians(worldYawDegrees)
        val look = Vector3d(origin.x() + Math.sin(yaw), origin.y(), origin.z() + Math.cos(yaw))
        val localOrigin = invokeTransform(owner, "toLocalVector", origin, 1.0f, false) ?: return null
        val localLook = invokeTransform(owner, "toLocalVector", look, 1.0f, false) ?: return null
        val direction = localLook.sub(localOrigin, Vector3d())
        if (!direction.x().isFinite() || !direction.z().isFinite() || direction.x() * direction.x() + direction.z() * direction.z() <= 1.0E-16) return null
        return Math.atan2(direction.x(), direction.z())
    }

    @JvmStatic
    fun currentLocalYawToWorld(level: Level, ownerEntityId: Int, localYawRadians: Double): Double? {
        val owner = resolveOwner(level, ownerEntityId) ?: return null
        val localOrigin = Vector3d()
        val localLook = Vector3d(Math.sin(localYawRadians), 0.0, Math.cos(localYawRadians))
        val worldOrigin = invokeTransform(owner, "toGlobalVector", localOrigin, 1.0f, false) ?: return null
        val worldLook = invokeTransform(owner, "toGlobalVector", localLook, 1.0f, false) ?: return null
        val direction = worldLook.sub(worldOrigin, Vector3d())
        if (!direction.x().isFinite() || !direction.z().isFinite() || direction.x() * direction.x() + direction.z() * direction.z() <= 1.0E-16) return null
        var yaw = Math.toDegrees(Math.atan2(direction.x(), direction.z()))
        while (yaw <= -180.0) yaw += 360.0
        while (yaw > 180.0) yaw -= 360.0
        return yaw
    }

    private fun invokeTransform('''
if "fun currentWorldToLocal" not in resolver:
    if resolver.count(resolver_anchor) != 1:
        raise SystemExit("reference-owner v2 lost resolver extension anchor")
    resolver = resolver.replace(resolver_anchor, resolver_extension, 1)
resolver_file.write_text(resolver, encoding="utf-8")

# -----------------------------------------------------------------------------
# 3) Lifetime: grounded contact refreshes ownership; airborne keeps the same owner for the native
#    bounded drag window. Grounded loss releases quickly instead of dragging a player across shore.
# -----------------------------------------------------------------------------
drag_info_anchor = '''            val entityDraggingInformation = (entity as? IEntityDraggingInformationProvider)?.draggingInformation ?: continue
'''
drag_lifetime = drag_info_anchor + '''
            if (!preTick && entityDraggingInformation.externalReferenceOwnerEntityId != null) {
                entityDraggingInformation.ticksSinceExternalReferenceOwner += 1
                val ownerId = entityDraggingInformation.externalReferenceOwnerEntityId
                val ownerStillResolvable = ownerId != null && ExternalReferenceFrameResolver.resolveOwner(entity.level(), ownerId) != null
                val groundedContactExpired = entity.onGround() && entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
                val ownerExpired = entityDraggingInformation.ticksSinceExternalReferenceOwner >= EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES
                if (!ownerStillResolvable || groundedContactExpired || ownerExpired) {
                    entityDraggingInformation.clearExternalReferenceOwner()
                }
            }
'''
if "groundedContactExpired" not in dragger:
    if dragger.count(drag_info_anchor) != 1:
        raise SystemExit("reference-owner v2 lost EntityDragger lifecycle anchor")
    dragger = dragger.replace(drag_info_anchor, drag_lifetime, 1)
dragger_file.write_text(dragger, encoding="utf-8")

# Acquire/refresh from the already-selected exact Create carriage only while grounded physical support
# and recent native Create contact agree. Insert immediately before the historical Phase83 bridge gate,
# then remove that bridge so acquisition tick cannot stack old reanchor authority with the new owner.
if "REFERENCE_OWNER_V2_ACQUIRE" not in probe:
    phase83_marker = probe.find('"GATE_E_PHASE83_CONTACT_REFRESH')
    if phase83_marker < 0:
        raise SystemExit("reference-owner v2 could not locate historical Phase83 marker")
    gate_start = probe.rfind('            if (Boolean.getBoolean("vs2.createCarryCompat")', 0, phase83_marker)
    if gate_start < 0:
        raise SystemExit("reference-owner v2 could not locate historical Phase83 gate")
    acquisition = '''            if (phase83ExactBaselineCarriage
                && phase81PhysicalSupport
                && player.onGround()
                && phase83RecentNativeApplication) {
                org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider referenceProvider =
                    (org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider) (Object) player;
                referenceProvider.getDraggingInformation().refreshExternalReferenceOwner(carriage.getId());
                LOGGER.info("REFERENCE_OWNER_V2_ACQUIRE player_tick={} carriage_id={} physical_support=true recent_native_contact=true owner_key=entity_id",
                    player.tickCount, carriage.getId());
            }

'''
    probe = probe[:gate_start] + acquisition + probe[gate_start:]
    phase83_marker = probe.find('"GATE_E_PHASE83_CONTACT_REFRESH', gate_start + len(acquisition))
    gate_start = probe.rfind('            if (Boolean.getBoolean("vs2.createCarryCompat")', 0, phase83_marker)
    replay_start = probe.find('            if (false && carryBaselineCaptured', phase83_marker)
    if gate_start < 0 or replay_start < 0:
        raise SystemExit("reference-owner v2 could not bound historical Phase83 bridge")
    probe = probe[:gate_start] + '''            // REFERENCE_OWNER_V2: historical Phase83 lease/reanchor authority removed.
            // Native Create contact acquires the generalized owner above; VS2 EntityDragger owns continuity.

''' + probe[replay_start:]
probe_file.write_text(probe, encoding="utf-8")

# Remove Phase205's old pre-collision reanchor injection and duplicate-contact-motion redirect entirely.
# Once V2 is composed, Create executes its native collision path and VS2 owns only reference continuity.
pre205 = collider.find('    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)\n    private static void vs2$preCollisionExternalFrame')
if pre205 >= 0:
    first_redirect = collider.find('    @Redirect(method = "collideEntities", at = @At(value = "INVOKE", target = "Lcom/zurrtum/create/content/contraptions/AbstractContraptionEntity;getContactPointMotion', pre205)
    next_redirect = collider.find('    @Redirect(', first_redirect + 1) if first_redirect >= 0 else -1
    if first_redirect < 0 or next_redirect < 0:
        raise SystemExit("reference-owner v2 could not bound Phase205 legacy methods")
    collider = collider[:pre205] + '''    // REFERENCE_OWNER_V2: legacy Phase205 external reanchor and contact-motion suppression removed.

''' + collider[next_redirect:]
collider_file.write_text(collider, encoding="utf-8")

# -----------------------------------------------------------------------------
# 4) Transform-only yaw facade shared by LocalPlayer packet + server resolution.
# -----------------------------------------------------------------------------
if "fun yawToExternalReference" not in lerper:
    import_anchor = "import net.minecraft.world.entity.decoration.ArmorStand\n"
    if "import net.minecraft.world.level.Level\n" not in lerper:
        if lerper.count(import_anchor) != 1:
            raise SystemExit("reference-owner v2 lost EntityLerper import anchor")
        lerper = lerper.replace(import_anchor, import_anchor + "import net.minecraft.world.level.Level\n", 1)
    yaw_anchor = '''    /**
     * Converts yaw to worldspace.
'''
    yaw_helpers = '''    fun yawToExternalReference(level: Level, ownerEntityId: Int, yaw: Double): Double? {
        return ExternalReferenceFrameResolver.currentWorldYawToLocal(level, ownerEntityId, yaw)
    }

    fun yawFromExternalReference(level: Level, ownerEntityId: Int, yaw: Double): Double? {
        return ExternalReferenceFrameResolver.currentLocalYawToWorld(level, ownerEntityId, yaw)
    }

'''
    if lerper.count(yaw_anchor) != 1:
        raise SystemExit("reference-owner v2 lost EntityLerper yaw anchor")
    lerper = lerper.replace(yaw_anchor, yaw_helpers + yaw_anchor, 1)
lerper_file.write_text(lerper, encoding="utf-8")

# -----------------------------------------------------------------------------
# 5) Dedicated external-reference motion packet; never overload ShipId/PacketPlayerShipMotion.
# -----------------------------------------------------------------------------
reference_packet_file.write_text('''package org.valkyrienskies.mod.common.networking

import org.valkyrienskies.core.impl.networking.simple.SimplePacket

/** Relative LocalPlayer motion in a non-Ship VS2 reference owner such as a Create carriage. */
data class PacketPlayerReferenceMotion(
    val ownerEntityId: Int,
    val x: Double,
    val y: Double,
    val z: Double,
    val yRot: Double
) : SimplePacket
''', encoding="utf-8")

# LocalPlayer: one reference-owner gate. External owner sends the dedicated packet using the same
# resolver/yaw facade; native ShipId branch remains unchanged for real VS2 ships.
if "PacketPlayerReferenceMotion" not in local_packet:
    import_anchor = "import org.valkyrienskies.mod.common.networking.PacketPlayerShipMotion;\n"
    if local_packet.count(import_anchor) != 1:
        raise SystemExit("reference-owner v2 lost LocalPlayer packet import anchor")
    local_packet = local_packet.replace(
        import_anchor,
        import_anchor + "import org.valkyrienskies.mod.common.networking.PacketPlayerReferenceMotion;\n" +
        "import org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver;\n",
        1,
    )

    ship_gate = '''        if (getDraggingInformation().isEntityBeingDraggedByAShip()) {
            if (getDraggingInformation().getLastShipStoodOn() != null) {'''
    reference_gate = '''        if (getDraggingInformation().isEntityBeingDraggedByReferenceOwner()) {
            if (getDraggingInformation().isEntityBeingDraggedByExternalReference()) {
                Integer ownerEntityId = getDraggingInformation().getExternalReferenceOwnerEntityId();
                if (ownerEntityId != null) {
                    Vector3dc relativePosition = ExternalReferenceFrameResolver.currentWorldToLocal(
                        level(), ownerEntityId, VectorConversionsMCKt.toJOML(getPosition(1f)));
                    Double relativeYaw = EntityLerper.INSTANCE.yawToExternalReference(
                        level(), ownerEntityId, getViewYRot(1f));
                    if (relativePosition != null && relativeYaw != null) {
                        PacketPlayerReferenceMotion packet = new PacketPlayerReferenceMotion(
                            ownerEntityId, relativePosition.x(), relativePosition.y(), relativePosition.z(), relativeYaw);
                        ValkyrienSkiesMod.getVsCore().getSimplePacketNetworking().sendToServer(packet);
                    }
                }
            } else if (getDraggingInformation().getLastShipStoodOn() != null) {'''
    if local_packet.count(ship_gate) != 1:
        raise SystemExit("reference-owner v2 lost LocalPlayer ship gate")
    local_packet = local_packet.replace(ship_gate, reference_gate, 1)
    local_packet = local_packet.replace(
        'final boolean draggedAndGrounded = getDraggingInformation().isEntityBeingDraggedByAShip()',
        'final boolean draggedAndGrounded = getDraggingInformation().isEntityBeingDraggedByReferenceOwner()',
        1,
    )
local_packet_file.write_text(local_packet, encoding="utf-8")

# Server: resolve the SAME external owner Entity id back to current world position/yaw. The native
# queued-position handshake is reused; no velocity/gravity/collision mutation is introduced here.
if "PacketPlayerReferenceMotion::class.register()" not in network:
    register_anchor = "        PacketPlayerShipMotion::class.register()\n"
    if network.count(register_anchor) != 1:
        raise SystemExit("reference-owner v2 lost packet registration anchor")
    network = network.replace(register_anchor, register_anchor + "        PacketPlayerReferenceMotion::class.register()\n", 1)

if "PacketPlayerReferenceMotion::class.registerServerHandler" not in network:
    handler_anchor = "        PacketPlayerShipMotion::class.registerServerHandler { motion, iPlayer ->\n"
    handler = '''        PacketPlayerReferenceMotion::class.registerServerHandler { motion, iPlayer ->
            val player = (iPlayer as MinecraftPlayer).player as ServerPlayer?
                ?: return@registerServerHandler
            val dragInfo = (player as? IEntityDraggingInformationProvider)?.draggingInformation
                ?: return@registerServerHandler
            if (ExternalReferenceFrameResolver.resolveOwner(player.level(), motion.ownerEntityId) == null) {
                if (dragInfo.externalReferenceOwnerEntityId == motion.ownerEntityId) {
                    dragInfo.clearExternalReferenceOwner()
                }
                return@registerServerHandler
            }
            dragInfo.refreshExternalReferenceOwner(motion.ownerEntityId)
            dragInfo.serverRelativeExternalPosition = Vector3d(motion.x, motion.y, motion.z)
            dragInfo.serverRelativeExternalYaw = motion.yRot
            val posUpdate = ExternalReferenceFrameResolver.currentLocalToWorld(
                player.level(), motion.ownerEntityId, Vector3d(motion.x, motion.y, motion.z)
            )?.toMinecraft() ?: return@registerServerHandler
            if ((player as PlayerDuck).vs_handledMovePacket()) {
                player.setPos(posUpdate.x, posUpdate.y, posUpdate.z)
                player.vs_setHandledMovePacket(false)
            } else {
                player.vs_setQueuedPositionUpdate(posUpdate)
            }
            dragInfo.serverResolvedExternalYaw = EntityLerper.yawFromExternalReference(
                player.level(), motion.ownerEntityId, motion.yRot
            )
        }

'''
    if network.count(handler_anchor) != 1:
        raise SystemExit("reference-owner v2 lost server ship-handler anchor")
    network = network.replace(handler_anchor, handler + handler_anchor, 1)
    import_anchor = "import org.valkyrienskies.mod.common.util.EntityLerper\n"
    if "import org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver\n" not in network:
        if network.count(import_anchor) != 1:
            raise SystemExit("reference-owner v2 lost VSGamePackets util import anchor")
        network = network.replace(import_anchor, import_anchor + "import org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver\n", 1)
network_file.write_text(network, encoding="utf-8")

# -----------------------------------------------------------------------------
# 6) Standing-player render interpolation uses the same external owner previous->current transform.
#    This touches entity interpolation only; the mounted-camera code is not entered or modified.
# -----------------------------------------------------------------------------
if "externalReferenceOwnerPresent" not in render:
    ship_only_gate = '''            vs$ranDragInterpolation = shipWorld.getLoadedShips().size() > 0;
            if (!vs$ranDragInterpolation) {
                return;
            }
'''
    generalized_gate = '''            vs$ranDragInterpolation = shipWorld.getLoadedShips().size() > 0;
            boolean externalReferenceOwnerPresent = false;
            if (!vs$ranDragInterpolation) {
                for (final Entity candidate : clientWorld.entitiesForRendering()) {
                    if (candidate instanceof IEntityDraggingInformationProvider referenceProvider
                        && referenceProvider.getDraggingInformation().isEntityBeingDraggedByExternalReference()) {
                        externalReferenceOwnerPresent = true;
                        break;
                    }
                }
                vs$ranDragInterpolation = externalReferenceOwnerPresent;
            }
            if (!vs$ranDragInterpolation) {
                return;
            }
'''
    if render.count(ship_only_gate) != 1:
        raise SystemExit("reference-owner v2 lost render early-gate anchor")
    render = render.replace(ship_only_gate, generalized_gate, 1)

    apply_anchor = '''                // Apply entityShouldBeHere, if its present
'''
    external_render = '''                if (entityShouldBeHere == null && entityDraggingInformation.isEntityBeingDraggedByExternalReference()) {
                    final Integer externalOwnerId = entityDraggingInformation.getExternalReferenceOwnerEntityId();
                    if (externalOwnerId != null) {
                        entityDraggingInformation.setCachedLastPosition(new Vector3d(entity.xo, entity.yo, entity.zo));
                        entityDraggingInformation.setRestoreCachedLastPosition(true);
                        final Vector3dc entityAddedVelocity = entityDraggingInformation.getAddedMovementLastTick();
                        final double entityMovementX = entity.getX() - entityAddedVelocity.x() - entity.xo;
                        final double entityMovementY = entity.getY() - entityAddedVelocity.y() - entity.yo;
                        final double entityMovementZ = entity.getZ() - entityAddedVelocity.z() - entity.zo;
                        final Vector3dc entityShouldBeHerePreTransform = new Vector3d(
                            entity.xo + entityMovementX * partialTick,
                            entity.yo + entityMovementY * partialTick,
                            entity.zo + entityMovementZ * partialTick
                        );
                        final Vector3d previousLocal = org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver.previousWorldToLocal(
                            clientWorld, externalOwnerId, entityShouldBeHerePreTransform);
                        if (previousLocal != null) {
                            entityShouldBeHere = org.valkyrienskies.mod.common.util.ExternalReferenceFrameResolver.currentLocalToWorld(
                                clientWorld, externalOwnerId, previousLocal);
                        }
                    }
                }

'''
    if render.count(apply_anchor) != 1:
        raise SystemExit("reference-owner v2 lost standing render apply anchor")
    render = render.replace(apply_anchor, external_render + apply_anchor, 1)
render_file.write_text(render, encoding="utf-8")

# -----------------------------------------------------------------------------
# Structural self-audit.
# -----------------------------------------------------------------------------
required = {
    "state_lifetime": "ticksSinceExternalReferenceOwner" in state and "refreshExternalReferenceOwner" in state,
    "resolver_current_frame": "currentWorldToLocal" in resolver and "currentLocalToWorld" in resolver,
    "resolver_yaw": "currentWorldYawToLocal" in resolver and "currentLocalYawToWorld" in resolver,
    "acquisition_selected_create_owner": "REFERENCE_OWNER_V2_ACQUIRE" in probe and "refreshExternalReferenceOwner(carriage.getId())" in probe,
    "phase83_reanchor_removed": "GATE_E_PHASE83_CONTACT_REFRESH" not in probe,
    "phase205_reanchor_removed": "GATE_E_PHASE205_PRE_COLLISION_REANCHOR" not in collider,
    "phase205_duplicate_suppression_removed": "GATE_E_PHASE205_DUPLICATE_CONTACT_CARRY_SUPPRESSED" not in collider,
    "dedicated_packet": reference_packet_file.exists() and "ownerEntityId: Int" in reference_packet_file.read_text(encoding="utf-8"),
    "local_packet_external_owner": "PacketPlayerReferenceMotion" in local_packet and "currentWorldToLocal" in local_packet and "yawToExternalReference" in local_packet,
    "server_same_owner_resolve": "PacketPlayerReferenceMotion::class.registerServerHandler" in network and "currentLocalToWorld" in network and "yawFromExternalReference" in network,
    "standing_render_same_owner": "isEntityBeingDraggedByExternalReference()" in render and "previousWorldToLocal" in render and "currentLocalToWorld" in render,
}
for key, value in required.items():
    print(f"REFERENCE_OWNER_V2 {key}={str(value).lower()}")
missing = [k for k, v in required.items() if not v]
if missing:
    raise SystemExit("reference-owner v2 structural proof failed: " + ",".join(missing))

# New resolver/acquisition/render code may transform positions/yaw, but it must not add gameplay
# velocity, gravity, floor/wall clamps, fake ShipId, or camera forcing. Server queued-position handling
# deliberately reuses the native PacketPlayerShipMotion handshake and is audited separately.
for name, text in {
    "resolver": resolver,
    "acquisition": probe[probe.find("REFERENCE_OWNER_V2_ACQUIRE") - 600:probe.find("REFERENCE_OWNER_V2_ACQUIRE") + 600],
    "render_external": render[render.find("entityShouldBeHere == null && entityDraggingInformation.isEntityBeingDraggedByExternalReference"):
                              render.find("// Apply entityShouldBeHere", render.find("entityShouldBeHere == null && entityDraggingInformation.isEntityBeingDraggedByExternalReference"))],
}.items():
    for forbidden in ["setDeltaMovement(", "getContactPointMotion(", "setNoGravity(", "setOnGround(", "floorY", "wallClamp", "camera.set", "setupWithShipMounted"]:
        if forbidden in text:
            raise SystemExit(f"reference-owner v2 {name} introduced forbidden gameplay/camera token: {forbidden}")

if "PacketPlayerReferenceMotion(val shipID" in reference_packet_file.read_text(encoding="utf-8"):
    raise SystemExit("reference-owner v2 must not encode external owner as ShipId")

print("REFERENCE_OWNER_V2 conclusion=single_external_owner_core_slice_composed runtime_candidate_requires_compile_and_proof=true")
