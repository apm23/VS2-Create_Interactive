#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 110 proved Phase 83's physical-support lease refresh is initially valid,
# but the MC 26.2 LocalPlayer onGround flag drops false immediately afterward
# while the player remains epsilon-close to the same real Create collision surface.
# Phase 84 therefore keeps the strict physical-support, collisionEligible, and
# broadphaseOverlap guards, but does not make lease continuity depend on the
# transient vanilla onGround flag. Manual Phase 81 setPos replay stays disabled;
# any horizontal movement must still come from Create's normal native client path.
# Harness-only functional hypothesis test; no VS2 physics/gameplay change.
condition_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method registerCollidingMethod = null;\n                    Class<?> registerOwner = carriage.getClass();\n                    while (registerOwner != null && registerCollidingMethod == null) {\n                        try {\n                            registerCollidingMethod = registerOwner.getDeclaredMethod("registerColliding", Entity.class);\n                        } catch (NoSuchMethodException ignored) {\n                            registerOwner = registerOwner.getSuperclass();\n                        }\n                    }\n                    if (registerCollidingMethod != null) {\n                        registerCollidingMethod.setAccessible(true);\n                        registerCollidingMethod.invoke(carriage, player);\n                        LOGGER.info(\n                            "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} vertical_gap={} on_ground={} phase84_on_ground_independent=true",\n                            carriage.getId(), player.tickCount, phase81PhysicalSupport, phase81VerticalGap, player.onGround());\n                    } else {\n                        LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_MISSING carriage_id={}", carriage.getId());\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (false && carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "GATE_E_PHASE83_CONTACT_REFRESH" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 84 could not find Phase 81 replay guard")
    source = source.replace(condition_anchor, condition_replacement, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 84: kept strict physical support/collision/broadphase lease refresh while removing transient onGround dependency; manual carry replay remains disabled; harness-only")
