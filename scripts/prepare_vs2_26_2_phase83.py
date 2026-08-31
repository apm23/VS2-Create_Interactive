#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Keep Create's own collidingEntities contact publication alive across the already
# proven short native sampling seam. Production-world-smoke #516 now proves M1
# locomotion and vanilla jump/landing with replay_free=true, so the adapter no
# longer has architectural justification to reactivate the historical LocalPlayer
# carry replay. Create remains authoritative for carriage contact/collision.
condition_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method registerCollidingMethod = null;\n                    Class<?> registerOwner = carriage.getClass();\n                    while (registerOwner != null && registerCollidingMethod == null) {\n                        try {\n                            registerCollidingMethod = registerOwner.getDeclaredMethod("registerColliding", Entity.class);\n                        } catch (NoSuchMethodException ignored) {\n                            registerOwner = registerOwner.getSuperclass();\n                        }\n                    }\n                    if (registerCollidingMethod != null) {\n                        registerCollidingMethod.setAccessible(true);\n                        registerCollidingMethod.invoke(carriage, player);\n                        LOGGER.info(\n                            "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} vertical_gap={} on_ground={} phase84_on_ground_independent=true",\n                            carriage.getId(), player.tickCount, phase81PhysicalSupport, phase81VerticalGap, player.onGround());\n                    } else {\n                        LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_MISSING carriage_id={}", carriage.getId());\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "GATE_E_PHASE83_CONTACT_REFRESH" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 85 could not find Phase 81 replay guard")
    source = source.replace(condition_anchor, condition_replacement, 1)

# Preserve the historical replay markers/body because later cumulative transforms
# still use them as stable anchors, but make the branch unreachable here, after the
# Phase 81 active guard has actually been materialized by the cumulative pipeline.
active_replay_guard = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
disabled_replay_guard = '''            if (false && carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
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

if disabled_replay_guard not in source:
    raise SystemExit("Phase 85 legacy LocalPlayer carry replay must remain disabled")

client_probe.write_text(source, encoding="utf-8")
print("Phase 85: retains Create-native physical-support contact refresh and leaves legacy LocalPlayer carry replay disabled")

# Phase 86 separates the verified compatibility movement from archived-save fixture
# normalization before the client source is compiled by CI.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase86.py")), run_name="__main__")
