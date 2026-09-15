#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
mixin_file = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/MixinMinecraft.java"

source = mixin_file.read_text(encoding="utf-8")

# Runtime 35001990251 proved that a generalized Create owner needs the VS2 EntityDragger lifecycle
# even when the native VS2 ship world is empty. Runtime collision-order proof 35025200849 then proved
# that applying that external-owner drag from MixinMinecraft.postTick() is too late: Create's complete
# collision pass runs first on every observed same-owner tick, and the VS2 reference-frame body step
# follows afterward. Apply ONLY the LocalPlayer external-owner body step immediately after ClientLevel
# entity ticking, before Create's Minecraft TAIL/ContraptionHandlerClient collision pass. Keep native
# VS2 ship dragging in its original postTick location; if a native ship coexists while LocalPlayer has
# an external owner, exclude only that already-applied LocalPlayer from the native postTick sweep.
# No fake/proxy ship, synthetic motion, collision takeover, camera forcing, or teleport is introduced.
import_anchor = "import org.valkyrienskies.mod.common.util.EntityDragger;\n"
provider_import = "import org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider;\n"
if provider_import not in source:
    if source.count(import_anchor) != 1:
        raise SystemExit("reference-owner v2 schedule fix lost MixinMinecraft import anchor")
    source = source.replace(import_anchor, import_anchor + provider_import, 1)

native_gate = '''            // The drag sweep visits every rendered entity; skip it when there are no ships.
            if (shipObjectWorld.getAllShips().size() > 0) {
                EntityDragger.INSTANCE.dragEntitiesWithShips(level.entitiesForRendering(), false);
            }
'''
post_tick_gate = '''            // Native VS2 Ship dragging stays at the native postTick boundary. The generalized
            // Create LocalPlayer owner is applied earlier, before Create collision, so do not apply
            // that LocalPlayer a second time here if native Ships also exist in the level.
            final LocalPlayer referencePlayer = Minecraft.getInstance().player;
            final boolean hasExternalReferenceOwner =
                referencePlayer instanceof IEntityDraggingInformationProvider referenceProvider
                    && referenceProvider.getDraggingInformation().isEntityBeingDraggedByExternalReference();
            if (shipObjectWorld.getAllShips().size() > 0) {
                if (hasExternalReferenceOwner && referencePlayer != null) {
                    final java.util.List<net.minecraft.world.entity.Entity> nativeDragTargets =
                        new java.util.ArrayList<>();
                    for (final net.minecraft.world.entity.Entity renderedEntity : level.entitiesForRendering()) {
                        if (renderedEntity != referencePlayer) {
                            nativeDragTargets.add(renderedEntity);
                        }
                    }
                    EntityDragger.INSTANCE.dragEntitiesWithShips(nativeDragTargets, false);
                } else {
                    EntityDragger.INSTANCE.dragEntitiesWithShips(level.entitiesForRendering(), false);
                }
            }
'''

if "nativeDragTargets" not in source:
    if source.count(native_gate) != 1:
        raise SystemExit("reference-owner v2 schedule fix expected one native ship drag-sweep gate")
    source = source.replace(native_gate, post_tick_gate, 1)

run_tick_anchor = '''    @Inject(
        method = "runTick",
        at = @At(value = "TAIL")
    )
'''
external_pre_collision = '''    @Inject(
        method = "tick",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/client/multiplayer/ClientLevel;tick(Ljava/util/function/BooleanSupplier;)V",
            shift = At.Shift.AFTER
        )
    )
    private void vs2$applyExternalReferenceOwnerBeforeCreateCollision(final CallbackInfo ci) {
        if (pause || shipObjectWorld == null || level == null || getConnection() == null) {
            return;
        }
        final LocalPlayer referencePlayer = Minecraft.getInstance().player;
        if (referencePlayer instanceof IEntityDraggingInformationProvider referenceProvider
            && referenceProvider.getDraggingInformation().isEntityBeingDraggedByExternalReference()) {
            EntityDragger.INSTANCE.dragEntitiesWithShips(
                java.util.Collections.singletonList(referencePlayer),
                false
            );
        }
    }

'''
if "vs2$applyExternalReferenceOwnerBeforeCreateCollision" not in source:
    if source.count(run_tick_anchor) != 1:
        raise SystemExit("reference-owner v2 schedule fix lost runTick injection anchor")
    source = source.replace(run_tick_anchor, external_pre_collision + run_tick_anchor, 1)

# Scheduling only: no new movement/collision/velocity/gravity/camera algorithm is permitted here.
for forbidden in [
    "setPos(", "setDeltaMovement(", "teleportTo(", "setNoGravity(", "setOnGround(",
    "getContactPointMotion(", "reanchorEntityWithExternalFrame(",
]:
    if forbidden in post_tick_gate + external_pre_collision:
        raise SystemExit("reference-owner v2 schedule fix introduced forbidden movement authority: " + forbidden)

required = [
    "vs2$applyExternalReferenceOwnerBeforeCreateCollision",
    "Lnet/minecraft/client/multiplayer/ClientLevel;tick(Ljava/util/function/BooleanSupplier;)V",
    "shift = At.Shift.AFTER",
    "java.util.Collections.singletonList(referencePlayer)",
    "isEntityBeingDraggedByExternalReference()",
    "shipObjectWorld.getAllShips().size() > 0",
    "nativeDragTargets",
    "renderedEntity != referencePlayer",
]
for token in required:
    if token not in source:
        raise SystemExit("reference-owner v2 schedule fix lost required scheduler token: " + token)

if "shipObjectWorld.getAllShips().size() > 0 || hasExternalReferenceOwner" in source:
    raise SystemExit("reference-owner v2 schedule fix retained late external-owner postTick scheduling")

mixin_file.write_text(source, encoding="utf-8")
print("REFERENCE_OWNER_V2_SCHEDULE_FIX native_ship_posttick_preserved=true external_owner_pre_create_collision=true")
print("REFERENCE_OWNER_V2_SCHEDULE_FIX localplayer_double_apply=false fake_vs2_ship=false movement_authority_added=false collision_mutation=false camera_mutation=false")
