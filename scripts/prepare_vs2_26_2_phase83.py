#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
entity_dragger = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/util/EntityDragger.kt"
source = client_probe.read_text(encoding="utf-8")
dragger_source = entity_dragger.read_text(encoding="utf-8")

# Real moving-train smoke proves the old contact-refresh experiment is the wrong boundary:
# after valid native Create carry/walk/reverse/strafe, Create can temporarily stop producing a
# surfaceCollision while the authoritative carriage frame keeps moving. The LocalPlayer then stays
# in world space and its carriage-local position walks away by multiple blocks.
#
# Route that reference-frame gap through VS2's existing EntityDragger mechanism. Create remains
# authoritative for previous/current carriage transforms; VS2 owns applying the reference-space
# re-anchor. No synthetic velocity, gravity, collision response, train state, or world state is added.
dragger_anchor = "object EntityDragger {\n"
dragger_helper = r'''object EntityDragger {
    /**
     * Re-anchor an entity through an authoritative external moving reference frame.
     *
     * targetForPreviousPosition is where the entity's previous world position maps under the
     * external frame's current transform. This is the same previous-to-current reference-space
     * operation used by native VS2 ship dragging; callers supply transforms, not velocity.
     */
    @JvmStatic
    fun reanchorEntityWithExternalFrame(entity: Entity, targetForPreviousPosition: Vec3) {
        val addedMovement = targetForPreviousPosition.subtract(entity.xo, entity.yo, entity.zo)
        if (!addedMovement.x.isFinite() || !addedMovement.y.isFinite() || !addedMovement.z.isFinite()) {
            return
        }
        if (addedMovement.lengthSqr() <= 1.0E-16) {
            return
        }

        // Keep application semantics identical to EntityDragger's native ship carry.
        val newBB = entity.boundingBox.move(addedMovement)
        entity.boundingBox = newBB
        entity.setPos(
            entity.x + addedMovement.x,
            entity.y + addedMovement.y,
            entity.z + addedMovement.z
        )
        (entity as? IEntityDraggingInformationProvider)?.draggingInformation?.addedMovementLastTick =
            Vector3d(addedMovement.x, addedMovement.y, addedMovement.z)
    }

'''
if "reanchorEntityWithExternalFrame" not in dragger_source:
    if dragger_source.count(dragger_anchor) != 1:
        raise SystemExit("Phase 85 could not find unique EntityDragger object anchor")
    dragger_source = dragger_source.replace(dragger_anchor, dragger_helper, 1)

condition_anchor = '''            if (carryBaselineCaptured
                && phase81PhysicalSupport
                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            String phase83NativeApplicationTickValue = System.getProperty(
                "vs2.phase170NativeContactApplicationTick." + carriage.getId());
            int phase83NativeApplicationAge = Integer.MAX_VALUE;
            if (phase83NativeApplicationTickValue != null) {
                try {
                    phase83NativeApplicationAge = player.tickCount - Integer.parseInt(phase83NativeApplicationTickValue);
                } catch (NumberFormatException ignored) {
                    phase83NativeApplicationAge = Integer.MAX_VALUE;
                }
            }
            boolean phase83RecentNativeApplication = phase83NativeApplicationAge >= 0
                && phase83NativeApplicationAge <= 1;
            boolean phase83AirborneNativeLease = !player.onGround()
                && phase83NativeApplicationAge >= 0
                && phase83NativeApplicationAge <= 20;
            boolean phase83NativeFrameEligible = phase81PhysicalSupport || phase83RecentNativeApplication || phase83AirborneNativeLease;
            boolean phase83ExternalFrameLease = phase83NativeApplicationAge >= 1
                && phase83NativeApplicationAge <= 20
                && (phase81PhysicalSupport || phase83AirborneNativeLease || phase83NativeApplicationAge <= 2);
            if (Boolean.getBoolean("vs2.createCarryCompat")
                && carryBaselineCaptured
                && phase83NativeFrameEligible
                && phase83ExternalFrameLease
                && collisionEligible
                && broadphaseOverlap) {
                try {
                    java.lang.reflect.Method phase83ToPreviousLocal = carriage.getClass().getMethod(
                        "toLocalVector", Vec3.class, float.class, boolean.class);
                    java.lang.reflect.Method phase83ToCurrentWorld = carriage.getClass().getMethod(
                        "toGlobalVector", Vec3.class, float.class, boolean.class);
                    Vec3 phase83PreviousReference = new Vec3(player.xo, player.yo, player.zo);
                    Vec3 phase83PreviousLocal = (Vec3) phase83ToPreviousLocal.invoke(
                        carriage, phase83PreviousReference, 0.0f, true);
                    Vec3 phase83CurrentTarget = (Vec3) phase83ToCurrentWorld.invoke(
                        carriage, phase83PreviousLocal, 1.0f, true);
                    org.valkyrienskies.mod.common.util.EntityDragger.reanchorEntityWithExternalFrame(
                        player, phase83CurrentTarget);
                    LOGGER.info(
                        "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} airborne={} vertical_gap={} on_ground={} native_application_age={} airborne_native_lease={} native_frame_eligible=true external_reference_frame=true create_authoritative_transform=true vs2_entity_dragger=true",
                        carriage.getId(), player.tickCount, phase81PhysicalSupport, !player.onGround(), phase81VerticalGap, player.onGround(),
                        phase83NativeApplicationAge, phase83AirborneNativeLease);
                } catch (ReflectiveOperationException | RuntimeException exception) {
                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());
                }
            }

            if (carryBaselineCaptured
                && phase81PhysicalSupport
                && carryReplayPlayerTick != player.tickCount'''
if "phase83NativeApplicationAge" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 85 could not find Phase 81 replay guard")
    source = source.replace(condition_anchor, condition_replacement, 1)
else:
    old_start = source.find('            String phase83NativeApplicationTickValue = System.getProperty(')
    old_tail = source.find(condition_anchor, old_start)
    if old_start < 0 or old_tail < 0:
        raise SystemExit("Phase 85 could not locate existing Phase83 block for reference-frame rewrite")
    source = source[:old_start] + condition_replacement + source[old_tail + len(condition_anchor):]

# Preserve the historical replay markers/body because later cumulative transforms still use them
# as stable anchors, but keep the old synthetic replay branch unreachable.
active_replay_guard = '''            if (carryBaselineCaptured
                && phase81PhysicalSupport
                && carryReplayPlayerTick != player.tickCount'''
disabled_replay_guard = '''            if (false && carryBaselineCaptured
                && phase81PhysicalSupport
                && carryReplayPlayerTick != player.tickCount'''
if disabled_replay_guard not in source:
    if active_replay_guard not in source:
        raise SystemExit("Phase 85 could not find legacy LocalPlayer carry replay guard")
    source = source.replace(active_replay_guard, disabled_replay_guard, 1)

source = source.replace(
    '"GATE_E_PHASE81_CARRY_REPLAY carriage_id={} requested={},{},{} allowed={},{},{} before={},{},{} after={},{},{}"',
    '"GATE_E_PHASE85_CARRY_REPLAY carriage_id={} requested={},{},{} allowed={},{},{} before={},{},{} after={},{},{}"',
    1,
)
source = source.replace(
    '"GATE_E_PHASE81_CARRY_REPLAY_ERROR type={}"',
    '"GATE_E_PHASE85_CARRY_REPLAY_ERROR type={}"',
    1,
)

required = [
    "phase83NativeApplicationTickValue",
    "phase83NativeApplicationAge",
    "phase83RecentNativeApplication",
    "phase83AirborneNativeLease",
    "phase83NativeFrameEligible",
    "phase83ExternalFrameLease",
    "phase81PhysicalSupport || phase83RecentNativeApplication || phase83AirborneNativeLease",
    "vs2.phase170NativeContactApplicationTick.",
    "phase83NativeApplicationAge <= 20",
    'Boolean.getBoolean("vs2.createCarryCompat")',
    '"toLocalVector", Vec3.class, float.class, boolean.class',
    '"toGlobalVector", Vec3.class, float.class, boolean.class',
    "phase83PreviousReference",
    "phase83PreviousLocal",
    "phase83CurrentTarget",
    "EntityDragger.reanchorEntityWithExternalFrame",
    "external_reference_frame=true",
    "create_authoritative_transform=true",
    "vs2_entity_dragger=true",
    "collisionEligible",
    "broadphaseOverlap",
    "GATE_E_PHASE83_CONTACT_REFRESH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 85 lost external-reference carry anchors: " + ", ".join(missing))

dragger_required = [
    "reanchorEntityWithExternalFrame",
    "targetForPreviousPosition.subtract(entity.xo, entity.yo, entity.zo)",
    "entity.boundingBox.move(addedMovement)",
    "entity.setPos(",
    "addedMovementLastTick",
]
dragger_missing = [token for token in dragger_required if token not in dragger_source]
if dragger_missing:
    raise SystemExit("Phase 85 lost VS2 EntityDragger reuse anchors: " + ", ".join(dragger_missing))

if disabled_replay_guard not in source:
    raise SystemExit("Phase 85 legacy LocalPlayer carry replay must remain disabled")

# The adapter may select/translate frames, but it must not synthesize gameplay velocity,
# gravity, collision responses, world state, or directly reposition the LocalPlayer.
inserted = condition_replacement
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "getContactPointMotion(", "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 85 adapter introduced forbidden gameplay/physics mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
entity_dragger.write_text(dragger_source, encoding="utf-8")
print("Phase 85: routes Create surface-contact gaps through VS2 EntityDragger's previous/current reference-frame reanchor; Create transform remains authoritative and no synthetic velocity is added")

# Phase 86 separates verified compatibility movement from archived-save fixture normalization.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase86.py")), run_name="__main__")
