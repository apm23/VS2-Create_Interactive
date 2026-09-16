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
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
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
 * Create still executes its complete collision geometry / OBB / grounding / damage path. The first
 * Entity.setPos in collideEntities is Create's collision-response writer and remains untouched. The
 * second Entity.setPos is contact-point carry translation. While VS2 has an active external reference
 * owner for LocalPlayer, VS2 owns reference continuity, so no Create carriage may also apply that
 * second carry writer. Calls are classified against the explicit active owner id for proof/logging.
 * The same exact-owner callback can refresh an already-existing grounded owner; it never acquires one.
 */
@Mixin(targets = "com.zurrtum.create.client.content.contraptions.ContraptionColliderClient", remap = false)
public abstract class MixinExternalReferenceOwnerCreateCarry {
    private static final Logger VS2_REFERENCE_OWNER_AUTHORITY =
        LogManager.getLogger("VS2-ReferenceOwner-Authority");

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

# The arbitration must not become a new motion/collision implementation. The only setPos calls in
# this mixin are pass-through invocations preserving Create behavior when no VS2 external owner exists.
for forbidden in [
    "setDeltaMovement(", ".move(", "teleport", "getContactPointMotion(", "setOnGround(",
    "gravity", "floorY", "wall", "camera", "velocity", "reanchorEntityWithExternalFrame",
]:
    if forbidden in source:
        raise SystemExit("reference-owner v2 authority fix introduced forbidden workaround token: " + forbidden)

print("REFERENCE_OWNER_V2_AUTHORITY_FIX active_owner_scoped=true create_collision_response_preserved=true")
print("REFERENCE_OWNER_V2_AUTHORITY_FIX exact_and_sibling_contact_carry_suppressed=true synthetic_motion=false collision_takeover=false")
print("REFERENCE_OWNER_V2_AUTHORITY_FIX exact_owner_grounded_refresh=true jump_refresh_after_ordinary_cap_only=true")
