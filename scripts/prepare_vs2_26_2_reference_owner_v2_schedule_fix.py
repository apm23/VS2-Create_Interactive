#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
mixin_file = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/MixinMinecraft.java"

source = mixin_file.read_text(encoding="utf-8")

# Runtime 35001990251 proved that the generalized Create owner is acquired while the V2
# EntityDragger body branch is never entered. The pinned VS2 client caller explains why:
# its postTick drag sweep is skipped whenever the native VS2 ship world contains zero ships.
# A Create carriage is deliberately NOT a VS2 Ship, so the generalized owner needs to be
# allowed to schedule the existing VS2 drag sweep without creating a proxy/fake ship.
import_anchor = "import org.valkyrienskies.mod.common.util.EntityDragger;\n"
provider_import = "import org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider;\n"
if provider_import not in source:
    if source.count(import_anchor) != 1:
        raise SystemExit("reference-owner v2 schedule fix lost MixinMinecraft import anchor")
    source = source.replace(import_anchor, import_anchor + provider_import, 1)

old_gate = '''            // The drag sweep visits every rendered entity; skip it when there are no ships.
            if (shipObjectWorld.getAllShips().size() > 0) {
                EntityDragger.INSTANCE.dragEntitiesWithShips(level.entitiesForRendering(), false);
            }
'''
new_gate = '''            // Native VS2 ships and the generalized non-Ship reference owner share the same VS2 body
            // drag lifecycle. A Create carriage must not be registered as a fake VS2 Ship merely to pass
            // this scheduler gate, so keep the native condition and additionally schedule the sweep while
            // the LocalPlayer has a live external reference owner.
            final LocalPlayer referencePlayer = Minecraft.getInstance().player;
            final boolean hasExternalReferenceOwner =
                referencePlayer instanceof IEntityDraggingInformationProvider referenceProvider
                    && referenceProvider.getDraggingInformation().isEntityBeingDraggedByExternalReference();
            if (shipObjectWorld.getAllShips().size() > 0 || hasExternalReferenceOwner) {
                EntityDragger.INSTANCE.dragEntitiesWithShips(level.entitiesForRendering(), false);
            }
'''

if "hasExternalReferenceOwner" not in source:
    if source.count(old_gate) != 1:
        raise SystemExit("reference-owner v2 schedule fix expected one native ship-only drag-sweep gate")
    source = source.replace(old_gate, new_gate, 1)

# This hypothesis changes scheduling only. It must not introduce body/world movement, collision,
# velocity, gravity, camera, or teleport authority of its own.
for forbidden in [
    "setPos(", "setDeltaMovement(", "teleportTo(", "setNoGravity(", "setOnGround(",
    "getContactPointMotion(", "reanchorEntityWithExternalFrame(",
]:
    if forbidden in new_gate:
        raise SystemExit("reference-owner v2 schedule fix introduced forbidden movement authority: " + forbidden)

required = [
    "hasExternalReferenceOwner",
    "isEntityBeingDraggedByExternalReference()",
    "shipObjectWorld.getAllShips().size() > 0 || hasExternalReferenceOwner",
    "EntityDragger.INSTANCE.dragEntitiesWithShips(level.entitiesForRendering(), false)",
]
for token in required:
    if token not in source:
        raise SystemExit("reference-owner v2 schedule fix lost required scheduler token: " + token)

mixin_file.write_text(source, encoding="utf-8")
print("REFERENCE_OWNER_V2_SCHEDULE_FIX native_ship_gate_preserved=true external_owner_schedules_drag_sweep=true")
print("REFERENCE_OWNER_V2_SCHEDULE_FIX fake_vs2_ship=false movement_authority_added=false collision_mutation=false camera_mutation=false")
