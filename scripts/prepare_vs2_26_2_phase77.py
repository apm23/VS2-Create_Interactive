#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 94 proved Create calls LocalPlayer#setPos only for the initial vertical
# surface correction and a zero-horizontal carry, then the surface contact drops
# while the train continues moving. Measure Create's own client carriage frame
# (current position vs getPrevPositionVec) beside the player/contact state before
# changing any movement behavior.
anchor = '''            boolean collisionEligible = carriage.canCollideWith(player);'''
insert = '''            String clientCarriageFrameState = "unresolved";\n            try {\n                java.lang.reflect.Method prevPositionMethod = null;\n                Class<?> prevOwner = carriage.getClass();\n                while (prevOwner != null && prevPositionMethod == null) {\n                    try {\n                        prevPositionMethod = prevOwner.getDeclaredMethod("getPrevPositionVec");\n                    } catch (NoSuchMethodException ignored) {\n                        prevOwner = prevOwner.getSuperclass();\n                    }\n                }\n                if (prevPositionMethod == null) {\n                    clientCarriageFrameState = "missing";\n                } else {\n                    prevPositionMethod.setAccessible(true);\n                    Object prevObject = prevPositionMethod.invoke(carriage);\n                    if (prevObject instanceof Vec3 prev) {\n                        Vec3 now = carriage.position();\n                        Vec3 frameMotion = now.subtract(prev);\n                        clientCarriageFrameState = "owner=" + prevOwner.getName()\n                            + ";now=" + now.x + "," + now.y + "," + now.z\n                            + ";prev=" + prev.x + "," + prev.y + "," + prev.z\n                            + ";motion=" + frameMotion.x + "," + frameMotion.y + "," + frameMotion.z\n                            + ";motion_sq=" + frameMotion.lengthSqr();\n                    } else {\n                        clientCarriageFrameState = "unexpected=" + String.valueOf(prevObject);\n                    }\n                }\n            } catch (ReflectiveOperationException | RuntimeException exception) {\n                clientCarriageFrameState = "error=" + exception.getClass().getSimpleName();\n            }\n            boolean collisionEligible = carriage.canCollideWith(player);'''

if "clientCarriageFrameState" not in source:
    if anchor not in source:
        raise SystemExit("Phase 77 could not find Gate E collision eligibility anchor")
    source = source.replace(anchor, insert, 1)

old_tail = '''                    + ";contact_point_motion=" + contactPointMotionState);'''
new_tail = '''                    + ";contact_point_motion=" + contactPointMotionState\n                    + ";client_carriage_frame=" + clientCarriageFrameState);'''
if "client_carriage_frame=" not in source:
    if old_tail not in source:
        raise SystemExit("Phase 77 could not find Phase 74 state tail")
    source = source.replace(old_tail, new_tail, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 77: traced Create client carriage current-vs-prev frame motion beside LocalPlayer contact state after Run 94 proved carry setPos stops after initial contact; read-only telemetry only")
