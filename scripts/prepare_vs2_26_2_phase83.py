#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Keep Create's own collidingEntities contact publication alive only after genuine native
# Create contact application for this exact carriage. Production-world #528 proved the old
# current/previous-tick evidence window expires before a normal vanilla jump even becomes
# airborne: the last exact-carriage native application was tick 34, jump began at tick 38,
# and carriage-local X then drifted every airborne tick until the player fell through the
# moving frame. Preserve Create's contact lease across one bounded vanilla airborne arc when
# the same carriage has recent genuine native evidence and remains collision-eligible/in
# broadphase. This only calls Create's registerColliding; it does not synthesize position,
# velocity, gravity, collision response, or a carry vector. The 20-tick age ceiling prevents
# stale carriage contact from surviving an unrelated long fall.
condition_anchor = '''            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
condition_replacement = '''            String phase83NativeApplicationTickValue = System.getProperty(\n                "vs2.phase170NativeContactApplicationTick." + carriage.getId());\n            int phase83NativeApplicationAge = Integer.MAX_VALUE;\n            if (phase83NativeApplicationTickValue != null) {\n                try {\n                    phase83NativeApplicationAge = player.tickCount - Integer.parseInt(phase83NativeApplicationTickValue);\n                } catch (NumberFormatException ignored) {\n                    phase83NativeApplicationAge = Integer.MAX_VALUE;\n                }\n            }\n            boolean phase83RecentNativeApplication = phase83NativeApplicationAge >= 0\n                && phase83NativeApplicationAge <= 1;\n            boolean phase83AirborneNativeLease = !player.onGround()\n                && phase83NativeApplicationAge >= 0\n                && phase83NativeApplicationAge <= 20;\n            boolean phase83NativeFrameEligible = phase81PhysicalSupport || phase83AirborneNativeLease;\n            if (carryBaselineCaptured\n                && phase83NativeFrameEligible\n                && (phase83RecentNativeApplication || phase83AirborneNativeLease)\n                && collisionEligible\n                && broadphaseOverlap) {\n                try {\n                    java.lang.reflect.Method registerCollidingMethod = null;\n                    Class<?> registerOwner = carriage.getClass();\n                    while (registerOwner != null && registerCollidingMethod == null) {\n                        try {\n                            registerCollidingMethod = registerOwner.getDeclaredMethod("registerColliding", Entity.class);\n                        } catch (NoSuchMethodException ignored) {\n                            registerOwner = registerOwner.getSuperclass();\n                        }\n                    }\n                    if (registerCollidingMethod != null) {\n                        registerCollidingMethod.setAccessible(true);\n                        registerCollidingMethod.invoke(carriage, player);\n                        LOGGER.info(\n                            "GATE_E_PHASE83_CONTACT_REFRESH carriage_id={} player_tick={} physical_support={} airborne={} vertical_gap={} on_ground={} native_application_age={} airborne_native_lease={} native_frame_eligible=true phase84_on_ground_independent=true",\n                            carriage.getId(), player.tickCount, phase81PhysicalSupport, !player.onGround(), phase81VerticalGap, player.onGround(),\n                            phase83NativeApplicationAge, phase83AirborneNativeLease);\n                    } else {\n                        LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_MISSING carriage_id={}", carriage.getId());\n                    }\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_PHASE83_CONTACT_REFRESH_ERROR type={}", exception.getClass().getSimpleName());\n                }\n            }\n\n            if (carryBaselineCaptured\n                && phase81PhysicalSupport\n                && carryReplayPlayerTick != player.tickCount'''
if "phase83NativeApplicationAge" not in source:
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
    "phase83NativeApplicationTickValue",
    "phase83NativeApplicationAge",
    "phase83RecentNativeApplication",
    "phase83AirborneNativeLease",
    "phase83NativeFrameEligible",
    "phase81PhysicalSupport || phase83AirborneNativeLease",
    "vs2.phase170NativeContactApplicationTick.",
    "phase83NativeApplicationAge <= 20",
    "airborne_native_lease={}",
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
print("Phase 85: retains exact-carriage native Create contact through one bounded airborne arc; legacy replay remains disabled")

# Phase 86 separates the verified compatibility movement from archived-save fixture
# normalization before the client source is compiled by CI.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase86.py")), run_name="__main__")
