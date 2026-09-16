#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "upstream"
dragger = root / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
authority = root / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinExternalReferenceOwnerCreateCarry.java"

text = dragger.read_text(encoding="utf-8")
old = '''                val nativeUpwardMotion = entity.deltaMovement.y > 1.0E-5
                val groundedContactExpired = entity.onGround() && !nativeUpwardMotion && entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
                val ownerExpired = entityDraggingInformation.ticksSinceExternalReferenceOwner >= EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES
                if (!ownerStillResolvable || groundedContactExpired || ownerExpired) {
                    entityDraggingInformation.clearExternalReferenceOwner()
                }
'''
new = '''                val nativeUpwardMotion = entity.deltaMovement.y > 1.0E-5
                val groundedContactExpired = entity.onGround() && !nativeUpwardMotion && entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
                val ownerExpired = entityDraggingInformation.ticksSinceExternalReferenceOwner >= EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES
                val lifecycleWillClear = !ownerStillResolvable || groundedContactExpired || ownerExpired
                println("REFERENCE_OWNER_V2_LIFECYCLE_TRACE entity_tick=${entity.tickCount} owner_id=$ownerId age=${entityDraggingInformation.ticksSinceExternalReferenceOwner} on_ground=${entity.onGround()} delta_y=${entity.deltaMovement.y} upward=$nativeUpwardMotion owner_resolvable=$ownerStillResolvable grounded_expired=$groundedContactExpired owner_expired=$ownerExpired will_clear=$lifecycleWillClear read_only=true")
                if (lifecycleWillClear) {
                    entityDraggingInformation.clearExternalReferenceOwner()
                }
'''
if text.count(old) != 1:
    raise SystemExit(f"lifecycle trace expected one exact lifetime block, found {text.count(old)}")
text = text.replace(old, new, 1)
dragger.write_text(text, encoding="utf-8")

j = authority.read_text(encoding="utf-8")
oldj = '''        boolean activeExternalOwner = dragging.isEntityBeingDraggedByExternalReference()
            && ownerEntityId != null;
        if (!activeExternalOwner) {
            entity.setPos(x, y, z);
            return;
        }
'''
newj = '''        boolean activeExternalOwner = dragging.isEntityBeingDraggedByExternalReference()
            && ownerEntityId != null;
        VS2_REFERENCE_OWNER_AUTHORITY.info(
            "REFERENCE_OWNER_V2_AUTHORITY_STATE player_tick={} carriage_id={} owner_id={} owner_age={} active_external_owner={} requested_delta={},{},{} read_only=true",
            player.tickCount,
            carriageEntity.getId(),
            ownerEntityId,
            dragging.getTicksSinceExternalReferenceOwner(),
            activeExternalOwner,
            x - entity.getX(),
            y - entity.getY(),
            z - entity.getZ()
        );
        if (!activeExternalOwner) {
            entity.setPos(x, y, z);
            return;
        }
'''
if j.count(oldj) != 1:
    raise SystemExit(f"authority trace expected one active-owner gate, found {j.count(oldj)}")
j = j.replace(oldj, newj, 1)
authority.write_text(j, encoding="utf-8")

for token in ["REFERENCE_OWNER_V2_LIFECYCLE_TRACE", "lifecycleWillClear", "REFERENCE_OWNER_V2_AUTHORITY_STATE", "owner_age={}"]:
    if token not in (text + j):
        raise SystemExit("trace token missing: " + token)
for forbidden in ["setDeltaMovement(", ".move(", "teleport(", "setOnGround(", "setNoGravity("]:
    if forbidden in new:
        raise SystemExit("lifecycle trace introduced movement mutation: " + forbidden)
print("REFERENCE_OWNER_V2_LIFECYCLE_AUTHORITY_TRACE read_only=true gameplay_mutation=false")
