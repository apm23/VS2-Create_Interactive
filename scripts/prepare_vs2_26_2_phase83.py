#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 107 proved the Create-native carry vector and ContraptionCollider.collide()
# are healthy: once a physically supporting sibling carriage has a valid prev
# frame, Phase 81's harness replay moves LocalPlayer by exactly the allowed motion.
# Test the actual remaining hypothesis without manual movement: while the Gate E
# LocalPlayer is still onGround and within 0.05 block of a real simplified Create
# collider, refresh Create's own public registerColliding(Entity) lease on that
# physically supporting carriage. Disable the Phase 81 setPos replay so any later
# horizontal Create setPos comes from Create's normal client collision/carry path.
# Harness-only functional test; no VS2 physics or production gameplay patch yet.
condition_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && player.onGround()\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method registerCollidingMethod = null;\n                    Class<?> registerOwner = carriage.getClass();\n                    while (registerOwner != null && registerCollidingMethod == null) {\n                        try {\n                            registerCollidingMethod = registerOwner.getDeclaredMethod("registerColliding", Entity.class);\n                        } catch (NoSuchMethodException ignored) {\n                            registerOwner = registerOwner.getSuperclass();\n                        }\n                    }\n                    if (registerCollidingMethod != null) {\n                        registerCollidingMethod.setAccessible(true);\n                        registerCollidingMethod.invoke(carriage, player);\n                        LOGGER.info(\n                            "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} vertical_gap={} on_ground={}",\n                            carriage.getId(), player.tickCount, phase81PhysicalSupport, phase81VerticalGap, player.onGround());\n                    } else {\n                        LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_MISSING carriage_id={}", carriage.getId());\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (false && carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "GATE_E_PHASE83_CONTACT_REFRESH" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 83 could not find Phase 81 replay guard")
    source = source.replace(condition_anchor, condition_replacement, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 83: refreshed Create's own contact lease only on strict physical support and disabled manual carry replay, so normal Create carry can be tested in isolation; harness-only")
