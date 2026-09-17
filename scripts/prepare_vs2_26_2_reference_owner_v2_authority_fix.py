#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinExternalReferenceOwnerCreateCarry.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

# Runtime proof 35008163064 showed duplicate exact-owner carry. Authority-gate run 35011902625 then
# proved a second, material sibling carriage writer on the same active external-owner tick: owner 5's
# contact carry was suppressed, carriage 7 still applied +7.11959 through the same ordinal-1 setPos,
# and VS2 EntityDragger then applied owner 5's +4.38299 reference-frame step. Create remains collision-
# authoritative: its first collision-response setPos and all OBB/grounding/damage paths remain untouched.
# Once a valid VS2 external reference owner is active, only the second contact-point carry translation
# is suppressed for LocalPlayer regardless of which carriage callback produced it. The active owner id
# remains the explicit authority key; this is not a global Create collision or movement suppression.
#
# Current-production post-arc run 35089177675 adds a narrower lifecycle fact. A valid owner7 native jump
# remained authoritative through the real descent, but the landing itself was expressed by Create's
# exact-owner contact-carry callback plus applied grounding while Phase170 emitted no native-application
# marker. The old jump-owner fallback therefore never refreshed and the 40-tick safety cap cleared a
# visibly settled owner at tick84. Reuse this already-authoritative exact-owner Create callback as the
# landing/settled refresh signal. While jump-active it is admitted only after the ordinary 25-tick cap,
# preserving rejection of early false grounded/side contacts at ticks49 and55-64. After landing resets
# the jump latch, continued exact-owner grounded contact may refresh the same existing owner. This never
# acquires a new owner and never changes Create collision response, motion, gravity, transforms, or camera.
#
# Ceiling correlation run 35179359526 then proved the integration-side collision-frame defect directly.
# At native jump tick39 VS2 had already applied the exact-owner carriage frame to LocalPlayer position,
# while Create's client collider still formed relative OBB motion as entityMotion - contraptionMotion.
# The same tick had an exact Create-contracted ceiling overlap (-0.095100039 block) but no Y response;
# broadphase/narrowphase instead reported a tiny temporal X contact. Once VS2 owns the exact carriage
# frame, contraption translation is already represented by the player's transformed position and must
# not be subtracted a second time from the LocalPlayer collision query. Keep Create's full geometry,
# SAT/OBB, grounding and response writers authoritative; remove only that duplicate frame-motion term
# for the exact active external owner. Sibling carriages and all non-LocalPlayer entities remain native.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider;

/**
 * Thin authority arbitration for the V2 non-Ship reference owner.
 *
 * Create still executes its complete collision geometry / OBB / grounding / damage path. When VS2
 * owns the exact carriage reference frame, Create's collision query consumes LocalPlayer's intrinsic
 * motion directly instead of subtracting the carriage translation a second time. The first Entity.setPos
 * in collideEntities remains Create's collision-response writer. The second Entity.setPos is contact-
 * point carry translation and is suppressed while VS2 owns reference continuity. Sibling carriages and
 * all non-LocalPlayer entities retain native Create motion/collision semantics. The same exact-owner
 * callback can refresh an already-existing grounded owner; it never acquires one.
 */
@Mixin(targets = "com.zurrtum.create.client.content.contraptions.ContraptionColliderClient", remap = false)
public abstract class MixinExternalReferenceOwnerCreateCarry {
    private static final Logger VS2_REFERENCE_OWNER_AUTHORITY =
        LogManager.getLogger("VS2-ReferenceOwner-Authority");

    @Redirect(
        method = "collideEntities",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/world/phys/Vec3;subtract(Lnet/minecraft/world/phys/Vec3;)Lnet/minecraft/world/phys/Vec3;",
            ordinal = 1
        ),
        remap = false,
        require = 1
    )
    private static Vec3 vs2$externalReferenceOwnerCollisionMotion(
        Vec3 entityMotion,
        Vec3 contraptionMotion,
        @Coerce Object carriage
    ) {
        LocalPlayer player = Minecraft.getInstance().player;
        if (player == null
            || entityMotion != player.getDeltaMovement()
            || !(player instanceof IEntityDraggingInformationProvider provider)
            || !(carriage instanceof Entity carriageEntity)) {
            return entityMotion.subtract(contraptionMotion);
        }

        var dragging = provider.getDraggingInformation();
        Integer ownerEntityId = dragging.getExternalReferenceOwnerEntityId();
        boolean activeExactExternalOwner = dragging.isEntityBeingDraggedByExternalReference()
            && ownerEntityId != null
            && ownerEntityId.intValue() == carriageEntity.getId();
        if (!activeExactExternalOwner) {
            return entityMotion.subtract(contraptionMotion);
        }

        VS2_REFERENCE_OWNER_AUTHORITY.info(
            "REFERENCE_OWNER_V2_COLLISION_MOTION_FRAME player_tick={} carriage_id={} owner_id={} " +
                "entity_motion={} contraption_motion={} create_relative_motion={} " +
                "external_frame_already_owned=true create_geometry_authoritative=true duplicate_frame_motion_removed=true",
            player.tickCount,
            carriageEntity.getId(),
            ownerEntityId,
            entityMotion,
            contraptionMotion,
            entityMotion
        );
        return entityMotion;
    }

    @Redirect(
        method = "collideEntities",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/world/entity/Entity;setPos(DDD)V",
            ordinal = 1
        ),
        remap = false,
        require = 1
    )
    private static void vs2$singleReferenceOwnerCarryWriter(
        Entity entity,
        double x,
        double y,
        double z,
        @Coerce Object carriage
    ) {
        if (!(entity instanceof LocalPlayer player)
            || !(player instanceof IEntityDraggingInformationProvider provider)
            || !(carriage instanceof Entity carriageEntity)) {
            entity.setPos(x, y, z);
            return;
        }

        var dragging = provider.getDraggingInformation();
        Integer ownerEntityId = dragging.getExternalReferenceOwnerEntityId();
        boolean activeExternalOwner = dragging.isEntityBeingDraggedByExternalReference()
            && ownerEntityId != null;
        if (!activeExternalOwner) {
            entity.setPos(x, y, z);
            return;
        }

        boolean exactExternalOwner = ownerEntityId.intValue() == carriageEntity.getId();
        boolean groundedExactOwnerContact = exactExternalOwner && player.onGround();
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

        VS2_REFERENCE_OWNER_AUTHORITY.info(
            "REFERENCE_OWNER_V2_CREATE_CONTACT_CARRY_SUPPRESSED player_tick={} carriage_id={} owner_id={} " +
                "requested_delta={},{},{} collision_response_preserved=true active_external_owner=true exact_external_owner={}",
            player.tickCount,
            carriageEntity.getId(),
            ownerEntityId,
            x - entity.getX(),
            y - entity.getY(),
            z - entity.getZ(),
            exactExternalOwner
        );
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
entry = "MixinExternalReferenceOwnerCreateCarry"
if entry not in client:
    client.append(entry)
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

source = java.read_text(encoding="utf-8")
required = [
    'target = "Lnet/minecraft/world/phys/Vec3;subtract(Lnet/minecraft/world/phys/Vec3;)Lnet/minecraft/world/phys/Vec3;"',
    "entityMotion != player.getDeltaMovement()",
    "activeExactExternalOwner",
    "REFERENCE_OWNER_V2_COLLISION_MOTION_FRAME",
    "duplicate_frame_motion_removed=true",
    "create_geometry_authoritative=true",
    "return entityMotion;",
    'target = "Lnet/minecraft/world/entity/Entity;setPos(DDD)V"',
    "ordinal = 1",
    "isEntityBeingDraggedByExternalReference()",
    "getExternalReferenceOwnerEntityId()",
    "activeExternalOwner",
    "ownerEntityId.intValue() == carriageEntity.getId()",
    "groundedExactOwnerContact",
    "getExternalReferenceOwnerJumpActive()",
    "getTicksSinceExternalReferenceOwner()",
    "EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES",
    "refreshExternalReferenceOwner(carriageEntity.getId())",
    "REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH",
    "source=create_contact_carry",
    "REFERENCE_OWNER_V2_CREATE_CONTACT_CARRY_SUPPRESSED",
    "active_external_owner=true",
    "collision_response_preserved=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("reference-owner v2 authority fix lost anchors: " + ", ".join(missing))

# The arbitration must not become a new movement/collision implementation. It only removes duplicate
# carriage-frame velocity from the exact-owner OBB query and preserves native Create pass-through for
# every other case. The only setPos calls are pass-through invocations when no VS2 owner is active.
for forbidden in [
    "setDeltaMovement(", ".move(", "teleport", "getContactPointMotion(", "setOnGround(",
    "gravity", "floorY", "wall", "camera", "reanchorEntityWithExternalFrame",
]:
    if forbidden in source:
        raise SystemExit("reference-owner v2 authority fix introduced forbidden workaround token: " + forbidden)

print("REFERENCE_OWNER_V2_AUTHORITY_FIX active_owner_scoped=true create_collision_response_preserved=true")
print("REFERENCE_OWNER_V2_AUTHORITY_FIX exact_owner_collision_motion_frame=true duplicate_contraption_motion_removed=true create_geometry_authoritative=true")
print("REFERENCE_OWNER_V2_AUTHORITY_FIX exact_and_sibling_contact_carry_suppressed=true synthetic_motion=false collision_takeover=false")
print("REFERENCE_OWNER_V2_AUTHORITY_FIX exact_owner_grounded_refresh=true jump_refresh_after_ordinary_cap_only=true")
