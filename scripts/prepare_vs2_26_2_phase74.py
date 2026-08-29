#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 88 confirmed LocalPlayer still does not follow a moving carriage after a
# valid Create surface contact. Create's client collider carries surface contacts
# with AbstractContraptionEntity#getContactPointMotion(), then applies that result
# directly with setPos (not Entity.move). Observe that exact intended carry vector
# before changing any movement behavior.
anchor = '''            boolean collisionEligible = carriage.canCollideWith(player);'''
insert = '''            String contactPointMotionState = "unresolved";\n            try {\n                java.lang.reflect.Method contactPointMotionMethod = null;\n                Class<?> contactOwner = carriage.getClass();\n                while (contactOwner != null && contactPointMotionMethod == null) {\n                    try {\n                        contactPointMotionMethod = contactOwner.getDeclaredMethod("getContactPointMotion", Vec3.class);\n                    } catch (NoSuchMethodException ignored) {\n                        contactOwner = contactOwner.getSuperclass();\n                    }\n                }\n                if (contactPointMotionMethod == null) {\n                    contactPointMotionState = "missing";\n                } else {\n                    contactPointMotionMethod.setAccessible(true);\n                    Object contactMotionObject = contactPointMotionMethod.invoke(carriage, player.position());\n                    if (contactMotionObject instanceof Vec3 contactMotion) {\n                        contactPointMotionState = "owner=" + contactOwner.getName()\n                            + ";motion=" + contactMotion.x + "," + contactMotion.y + "," + contactMotion.z\n                            + ";motion_sq=" + contactMotion.lengthSqr();\n                    } else {\n                        contactPointMotionState = "unexpected=" + String.valueOf(contactMotionObject);\n                    }\n                }\n            } catch (ReflectiveOperationException | RuntimeException exception) {\n                contactPointMotionState = "error=" + exception.getClass().getSimpleName();\n            }\n            boolean collisionEligible = carriage.canCollideWith(player);'''

if "contactPointMotionState" not in source:
    if anchor not in source:
        raise SystemExit("Phase 74 could not find Gate E collision eligibility anchor")
    source = source.replace(anchor, insert, 1)

old_log = '''                localSupportState + ";simplified_colliders=" + simplifiedColliderState);'''
new_log = '''                localSupportState + ";simplified_colliders=" + simplifiedColliderState\n                    + ";contact_point_motion=" + contactPointMotionState);'''
if "contact_point_motion=" not in source:
    if old_log not in source:
        raise SystemExit("Phase 74 could not find Gate E state tail")
    source = source.replace(old_log, new_log, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 74: traced Create's exact getContactPointMotion carry vector beside contact state after Run 88 proved LocalPlayer remains fixed; read-only telemetry only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase75.py")), run_name="__main__")
