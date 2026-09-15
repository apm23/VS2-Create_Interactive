#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinExternalReferenceOwnerCreateCarry.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

# Runtime proof 35008163064 showed the exact same carriage-frame horizontal delta is applied twice:
# first by VS2 EntityDragger for the active external reference owner, then by Create's second
# surfaceCollision setPos after getContactPointMotion. Create must remain collision-authoritative, so
# preserve its first collision-response setPos and every other collision/damage/grounding path. Only
# skip the second contact-carry setPos for the LocalPlayer when the currently processed carriage is
# exactly the same Entity id as VS2's active external reference owner.
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
 * second Entity.setPos is the horizontal contact-point carry translation. When VS2 already owns body
 * reference continuity for this exact Create carriage, that second translation would apply the same
 * carriage frame step a second time, so it is skipped only for that exact LocalPlayer+owner pair.
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
        boolean exactExternalOwner = dragging.isEntityBeingDraggedByExternalReference()
            && ownerEntityId != null
            && ownerEntityId.intValue() == carriageEntity.getId();
        if (!exactExternalOwner) {
            entity.setPos(x, y, z);
            return;
        }

        VS2_REFERENCE_OWNER_AUTHORITY.info(
            "REFERENCE_OWNER_V2_CREATE_CONTACT_CARRY_SUPPRESSED player_tick={} carriage_id={} owner_id={} " +
                "requested_delta={},{},{} collision_response_preserved=true exact_external_owner=true",
            player.tickCount,
            carriageEntity.getId(),
            ownerEntityId,
            x - entity.getX(),
            y - entity.getY(),
            z - entity.getZ()
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
    "ownerEntityId.intValue() == carriageEntity.getId()",
    "REFERENCE_OWNER_V2_CREATE_CONTACT_CARRY_SUPPRESSED",
    "collision_response_preserved=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("reference-owner v2 authority fix lost anchors: " + ", ".join(missing))

# The arbitration must not become a new motion/collision implementation. The only setPos calls in
# this mixin are pass-through invocations preserving Create behavior when the exact owner gate is false.
for forbidden in [
    "setDeltaMovement(", ".move(", "teleport", "getContactPointMotion(", "setOnGround(",
    "gravity", "floorY", "wall", "camera", "velocity", "reanchorEntityWithExternalFrame",
]:
    if forbidden in source:
        raise SystemExit("reference-owner v2 authority fix introduced forbidden workaround token: " + forbidden)

print("REFERENCE_OWNER_V2_AUTHORITY_FIX exact_owner_only=true create_collision_response_preserved=true")
print("REFERENCE_OWNER_V2_AUTHORITY_FIX second_contact_carry_writer_suppressed=true synthetic_motion=false collision_takeover=false")
