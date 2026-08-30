#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = client_probe.read_text(encoding="utf-8")
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #355 reached the real train and held carriage 5 perfectly through walk ticks
# 20-23. At tick 24 carriage 5 itself stepped 12.6007645 blocks and Create's contact-motion API
# returned the same vector, while no ContraptionColliderClient native application was recorded for
# carriage 5. The sibling carriage-7 call was already correctly suppressed by Phase172. Phase161
# still did not classify/recover the active-carriage loss because phase134NativeCarryHealthy.5
# remained true from tick 23 even though its healthy-tick property was stale. Make native-health
# consumption tick-fresh, and publish current active-carriage contact-motion availability so a
# missing same-tick Phase161 balance sample can be distinguished from a genuine zero-motion frame.
# Recovery continues to use only the existing Phase85 Create-computed/collision-filtered vector,
# under strict support and Phase170 no-native-application guards. Fixture accounting only.

contact_anchor = "        net.minecraft.world.phys.Vec3 motion = cir.getReturnValue();\n"
contact_insert = contact_anchor + '''        net.minecraft.client.player.LocalPlayer phase179Player = net.minecraft.client.Minecraft.getInstance().player;
        if (phase179Player != null) {
            System.setProperty("vs2.phase179ContactMotionTick." + self.getId(), Integer.toString(phase179Player.tickCount));
            System.setProperty("vs2.phase179ContactMotionSq." + self.getId(), Double.toString(motion.lengthSqr()));
        }
'''
if "vs2.phase179ContactMotionTick." not in contact_source:
    count = contact_source.count(contact_anchor)
    if count != 1:
        raise SystemExit(f"Phase 179 expected exactly one contact-motion return anchor, found {count}")
    contact_source = contact_source.replace(contact_anchor, contact_insert, 1)

decl_pos = source.find("boolean phase161SupportedLocomotionNativeLoss =")
if decl_pos < 0:
    raise SystemExit("Phase 179 could not locate Phase161 supported-loss declaration")
decl_end = source.find(";", decl_pos)
if decl_end < 0:
    raise SystemExit("Phase 179 could not bound Phase161 supported-loss declaration")
predicate = source[decl_pos:decl_end + 1]

fresh_decl = '''boolean phase179NativeHealthyFlag = Boolean.parseBoolean(System.getProperty(
            "vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"));
        boolean phase179CurrentNativeHealthy = phase179NativeHealthyFlag
            && Integer.toString(player.tickCount).equals(System.getProperty(
                "vs2.phase134NativeCarryHealthyTick." + carriage.getId()));
        boolean phase179CurrentContactMotion = Integer.toString(player.tickCount).equals(System.getProperty(
            "vs2.phase179ContactMotionTick." + carriage.getId()));
        double phase179ContactMotionSq = Double.parseDouble(System.getProperty(
            "vs2.phase179ContactMotionSq." + carriage.getId(), "NaN"));
        boolean phase179ActiveContactMotionAvailable = phase179CurrentContactMotion
            && Double.isFinite(phase179ContactMotionSq) && phase179ContactMotionSq > 1.0E-8;
        boolean phase161SupportedLocomotionNativeLoss ='''

if "phase179CurrentNativeHealthy" not in source:
    source = source[:decl_pos] + fresh_decl + source[decl_pos + len("boolean phase161SupportedLocomotionNativeLoss ="):]
    decl_pos = source.find("boolean phase161SupportedLocomotionNativeLoss =")
    decl_end = source.find(";", decl_pos)
    predicate = source[decl_pos:decl_end + 1]

healthy_pattern = re.compile(
    r"!Boolean\.parseBoolean\(System\.getProperty\(\s*"
    r"\"vs2\.phase134NativeCarryHealthy\.\"\s*\+\s*carriage\.getId\(\),\s*\"false\"\s*\)\)"
)
if "!phase179CurrentNativeHealthy" not in predicate:
    predicate, healthy_count = healthy_pattern.subn("!phase179CurrentNativeHealthy", predicate, count=1)
    if healthy_count != 1:
        raise SystemExit("Phase 179 expected exactly one Phase161 current native-health boolean check")

if "phase179ActiveContactMotionAvailable" not in predicate:
    undercarry_token = "&& phase161MeasuredUndercarry"
    if predicate.count(undercarry_token) != 1:
        raise SystemExit("Phase 179 expected exactly one Phase161 measured-undercarry clause")
    predicate = predicate.replace(
        undercarry_token,
        "&& (phase161MeasuredUndercarry || (phase170FixtureWalkRecoveryWindow && phase179ActiveContactMotionAvailable))",
        1,
    )

source = source[:decl_pos] + predicate + source[decl_end + 1:]

if "GATE_E_PHASE179_STALE_NATIVE_HEALTH_RECOVERY_ELIGIBLE" not in source:
    marker = "if (phase161SupportedLocomotionNativeLoss) {"
    marker_pos = source.find(marker, decl_end)
    if marker_pos < 0:
        raise SystemExit("Phase 179 could not locate Phase161 replay-log guard")
    line_start = source.rfind("\n", 0, marker_pos) + 1
    indent = source[line_start:marker_pos]
    log_insert = (
        f'{indent}if (phase170FixtureWalkRecoveryWindow && phase179NativeHealthyFlag && !phase179CurrentNativeHealthy\n'
        f'{indent}        && phase179ActiveContactMotionAvailable) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE179_STALE_NATIVE_HEALTH_RECOVERY_ELIGIBLE carriage_id={{}} player_tick={{}} healthy_tick={{}} contact_motion_sq={{}} no_same_tick_native_application=true fixture_only=true accounting_only=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId(), "missing"), phase179ContactMotionSq);\n'
        f'{indent}}}\n'
    )
    source = source[:line_start] + log_insert + source[line_start:]

required = [
    "phase179NativeHealthyFlag",
    "phase179CurrentNativeHealthy",
    "phase179ActiveContactMotionAvailable",
    "vs2.phase179ContactMotionTick.",
    "vs2.phase179ContactMotionSq.",
    "!phase179CurrentNativeHealthy",
    "phase170FixtureWalkRecoveryWindow && phase179ActiveContactMotionAvailable",
    "GATE_E_PHASE179_STALE_NATIVE_HEALTH_RECOVERY_ELIGIBLE",
    "phase161SupportedLocomotionNativeLoss",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source and token not in contact_source]
if missing:
    raise SystemExit("Phase 179 lost stale-health recovery anchors: " + ", ".join(missing))

inserted = fresh_decl + contact_insert + "phase170FixtureWalkRecoveryWindow && phase179ActiveContactMotionAvailable"
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 179 introduced forbidden gameplay mutation token: " + forbidden)

contact_trace.write_text(contact_source, encoding="utf-8")
client_probe.write_text(source, encoding="utf-8")
print("Phase 179: treats native health as tick-fresh and bridges only missing-sample active-contact walk recovery; fixture accounting only")
