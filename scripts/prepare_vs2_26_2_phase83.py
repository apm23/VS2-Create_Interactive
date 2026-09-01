#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Keep Create's own collidingEntities contact publication alive only across a proven short
# sampling seam. Production-world #522 showed that unconditional physical-support refresh can
# publish contact for a carriage after Create's native surface-collision/carry application has
# already stopped. Require a current- or previous-tick non-zero native Create contact application
# for this exact carriage before refreshing its lease. Phase170 publishes that evidence from the
# real ContraptionColliderClient call site. Once that native evidence exists, retain the same
# Create contact while the player is airborne but still collision-eligible and inside the carriage
# broadphase. This keeps a vanilla jump in Create's authoritative moving carriage frame instead of
# dropping the contact lease at onGround=false. No position, velocity, collision response, carry
# vector, train/world state, gravity, or VS2 physics is synthesized here.
condition_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            boolean phase83RecentNativeApplication = Integer.toString(player.tickCount).equals(\n                System.getProperty("vs2.phase170NativeContactApplicationTick." + carriage.getId()))\n                || Integer.toString(player.tickCount - 1).equals(\n                    System.getProperty("vs2.phase170NativeContactApplicationTick." + carriage.getId()));\n            boolean phase83NativeFrameEligible = phase81PhysicalSupport || !player.onGround();\n            if (carryBaselineCaptured\n                && phase83NativeFrameEligible\n                && phase83RecentNativeApplication\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method registerCollidingMethod = null;\n                    Class<?> registerOwner = carriage.getClass();\n                    while (registerOwner != null && registerCollidingMethod == null) {\n                        try {\n                            registerCollidingMethod = registerOwner.getDeclaredMethod("registerColliding", Entity.class);\n                        } catch (NoSuchMethodException ignored) {\n                            registerOwner = registerOwner.getSuperclass();\n                        }\n                    }\n                    if (registerCollidingMethod != null) {\n                        registerCollidingMethod.setAccessible(true);\n                        registerCollidingMethod.invoke(carriage, player);\n                        LOGGER.info(\n                            "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} airborne={} vertical_gap={} on_ground={} native_application_recent=true native_frame_eligible=true phase84_on_ground_independent=true",\n                            carriage.getId(), player.tickCount, phase81PhysicalSupport, !player.onGround(), phase81VerticalGap, player.onGround());\n                    } else {\n                        LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_MISSING carriage_id={}", carriage.getId());\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "phase83RecentNativeApplication" not in source:
    if condition_anchor not in source:
        raise SystemExit("Phase 85 could not find Phase 81 replay guard")
    source = source.replace(condition_anchor, condition_replacement, 1)

# Preserve the historical replay markers/body because later cumulative transforms still use them
# as stable anchors, but make the branch unreachable here, after the Phase81 active guard has
# actually been materialized by the cumulative pipeline.
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

required = [
    "phase83RecentNativeApplication",
    "phase83NativeFrameEligible",
    "phase81PhysicalSupport || !player.onGround()",
    "vs2.phase170NativeContactApplicationTick.",
    "player.tickCount - 1",
    "native_application_recent=true",
    "native_frame_eligible=true",
    "registerCollidingMethod.invoke(carriage, player)",
    "collisionEligible",
    "broadphaseOverlap",
    "GATE_E_PHASE83_CONTACT_REFRESH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 85 lost native-evidence contact refresh anchors: " + ", ".join(missing))

if disabled_replay_guard not in source:
    raise SystemExit("Phase 85 legacy LocalPlayer carry replay must remain disabled")

inserted = condition_replacement
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "getContactPointMotion(", "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 85 contact refresh introduced forbidden movement/physics mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 85: retains exact-carriage Create-native contact through airborne frame continuity and leaves legacy LocalPlayer carry replay disabled")

# Phase 86 separates the verified compatibility movement from archived-save fixture
# normalization before the client source is compiled by CI.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase86.py")), run_name="__main__")
