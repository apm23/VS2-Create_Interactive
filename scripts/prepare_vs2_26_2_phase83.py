#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 111 proves Phase 84 keeps Create's collidingEntities lease alive even when
# LocalPlayer.onGround transiently drops false, but Create 6.0.9 still never emits
# horizontal carry from ContraptionColliderClient and the player subsequently falls
# away from the verified simplified carriage surface. The remaining compatibility
# seam is therefore the missing application of Create's already-computed contact
# motion, not lease lifetime.
#
# Phase 85 keeps the Phase 84 lease refresh and re-enables the already-proven
# Phase 81 replay, which uses carriage.getContactPointMotion() and Create's own
# ContraptionCollider.collide() result. It remains restricted to a simplified
# collider directly under the player's feet, collisionEligible+broadphaseOverlap,
# one application per player tick, and horizontal components only. No custom
# physics vector, teleport target, train controls, schedule, or VS2 physics changes.
condition_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method registerCollidingMethod = null;\n                    Class<?> registerOwner = carriage.getClass();\n                    while (registerOwner != null && registerCollidingMethod == null) {\n                        try {\n                            registerCollidingMethod = registerOwner.getDeclaredMethod("registerColliding", Entity.class);\n                        } catch (NoSuchMethodException ignored) {\n                            registerOwner = registerOwner.getSuperclass();\n                        }\n                    }\n                    if (registerCollidingMethod != null) {\n                        registerCollidingMethod.setAccessible(true);\n                        registerCollidingMethod.invoke(carriage, player);\n                        LOGGER.info(\n                            "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} vertical_gap={} on_ground={} phase84_on_ground_independent=true",\n                            carriage.getId(), player.tickCount, phase81PhysicalSupport, phase81VerticalGap, player.onGround());\n                    } else {\n                        LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_MISSING carriage_id={}", carriage.getId());\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "GATE_E_PHASE83_CONTACT_REFRESH" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 85 could not find Phase 81 replay guard")
    source = source.replace(condition_anchor, condition_replacement, 1)

# Phase 83/84 deliberately disabled the validated Create-filtered replay while
# testing native carry in isolation. Run 111 falsified that hypothesis, so restore
# only this narrow guarded path and give it a distinct functional marker.
source = source.replace(
    '''            if (false && carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount''',
    '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount''',
    1,
)
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

client_probe.write_text(source, encoding="utf-8")
print("Phase 85: restored Create-computed, Create-collision-filtered horizontal carry only under strict physical support; compatibility candidate")
