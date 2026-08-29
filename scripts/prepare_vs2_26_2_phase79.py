#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 98 proved Create's LocalPlayer colliding lease ages 0 -> 1 -> 2 -> 3 and
# expires while the player remains onGround and ~1e-4 above the real simplified
# collider. Phase 77 also proved getContactPointMotion becomes non-zero once the
# carriage moves. Before changing production collision semantics, replay Create's
# own horizontal carry operation only inside the already-normalized Gate E smoke
# fixture, only for the exact carriage that established genuine surface contact.
# This is a harness-only functional hypothesis check, not a general physics patch.
field_anchor = '''    private static double carryCarriageZ;\n'''
field_insert = '''    private static double carryCarriageZ;\n    private static int carryCarriageEntityId = Integer.MIN_VALUE;\n    private static int carryReplayPlayerTick = Integer.MIN_VALUE;\n'''
if "carryCarriageEntityId" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 79 could not find carry field anchor")
    source = source.replace(field_anchor, field_insert, 1)

capture_anchor = '''                carryCarriageZ = carriage.getZ();\n                LOGGER.info('''
capture_insert = '''                carryCarriageZ = carriage.getZ();\n                carryCarriageEntityId = carriage.getId();\n                LOGGER.info('''
if "carryCarriageEntityId = carriage.getId();" not in source:
    if capture_anchor not in source:
        raise SystemExit("Phase 79 could not find carry baseline capture anchor")
    source = source.replace(capture_anchor, capture_insert, 1)

telemetry_anchor = '''            if (!carryBaselineCaptured && createRegisteredContact && player.onGround()) {'''
replay = '''            if (carryBaselineCaptured\n                && carryCarriageEntityId == carriage.getId()\n                && carryReplayPlayerTick != player.tickCount\n                && player.onGround()\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method contactPointMotionMethod = null;\n                    Class<?> contactOwner = carriage.getClass();\n                    while (contactOwner != null && contactPointMotionMethod == null) {\n                        try {\n                            contactPointMotionMethod = contactOwner.getDeclaredMethod("getContactPointMotion", Vec3.class);\n                        } catch (NoSuchMethodException ignored) {\n                            contactOwner = contactOwner.getSuperclass();\n                        }\n                    }\n                    if (contactPointMotionMethod != null) {\n                        contactPointMotionMethod.setAccessible(true);\n                        Object rawMotion = contactPointMotionMethod.invoke(carriage, player.position());\n                        if (rawMotion instanceof Vec3 contactMotion\n                            && (contactMotion.x * contactMotion.x + contactMotion.z * contactMotion.z) > 1.0E-10) {\n                            Class<?> colliderClass = Class.forName("com.zurrtum.create.content.contraptions.ContraptionCollider");\n                            java.lang.reflect.Method collideMethod = colliderClass.getDeclaredMethod("collide", Vec3.class, Entity.class);\n                            collideMethod.setAccessible(true);\n                            Object rawAllowed = collideMethod.invoke(null, contactMotion, player);\n                            if (rawAllowed instanceof Vec3 allowedMovement) {\n                                double beforeX = player.getX();\n                                double beforeY = player.getY();\n                                double beforeZ = player.getZ();\n                                player.setPos(\n                                    beforeX + allowedMovement.x,\n                                    beforeY,\n                                    beforeZ + allowedMovement.z\n                                );\n                                carryReplayPlayerTick = player.tickCount;\n                                LOGGER.info(\n                                    "GATE_E_PHASE79_CARRY_REPLAY carriage_id={} requested={},{},{} allowed={},{},{} before={},{},{} after={},{},{}",\n                                    carriage.getId(),\n                                    contactMotion.x, contactMotion.y, contactMotion.z,\n                                    allowedMovement.x, allowedMovement.y, allowedMovement.z,\n                                    beforeX, beforeY, beforeZ,\n                                    player.getX(), player.getY(), player.getZ());\n                            }\n                        }\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE79_CARRY_REPLAY_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (!carryBaselineCaptured && createRegisteredContact && player.onGround()) {'''
if "GATE_E_PHASE79_CARRY_REPLAY" not in source:
    if telemetry_anchor not in source:
        raise SystemExit("Phase 79 could not find carry telemetry anchor")
    source = source.replace(telemetry_anchor, replay, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 79: replayed Create's own collision-filtered horizontal carry only for the exact Gate E carriage after genuine contact; harness-only functional hypothesis check")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase80.py")), run_name="__main__")
