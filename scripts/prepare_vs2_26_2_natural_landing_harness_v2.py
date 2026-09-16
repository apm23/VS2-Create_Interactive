#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
probe_path = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
s = p.read_text(encoding="utf-8")
probe = probe_path.read_text(encoding="utf-8")

# Preserve the production-smoke fixture's proven locomotion ordering exactly:
# forward/walk -> backward -> strafe -> settle -> jump. Keep the bounded headless
# native-aiStep fallback from v2, but make reverse/strafe acceptance wait for the
# exact Create Phase131 support result from the motion tick. Phase202 intentionally
# samples LocalPlayer motion before Create publishes grounding later in that tick, so
# acceptance must be deferred one tick rather than reading self.onGround() early.
pattern = re.compile(r'    @Unique\n    private boolean vs2\$jumpArmReady\(LocalPlayer self\) \{.*?\n    \}', re.S)
m = pattern.search(s)
if not m:
    raise SystemExit("natural landing harness could not locate jumpArmReady")
old = m.group(0)
for required in [
    "!vs2$fixtureWalkSeen(self) || !vs2$backwardConfirmed || !vs2$strafeConfirmed",
    "self.tickCount >= vs2$strafeStartTick + 15",
    "vs2.productionFixtureJumpFloorSupportNow",
    "vs2.productionFixtureJumpFloorSupportTick",
    "vs2.phase170NativeContactApplicationTick",
]:
    if required not in old:
        raise SystemExit("natural landing harness lost original jump sequencing guard: " + required)

new = "\n".join([
    "    @Unique",
    "    private boolean vs2$jumpArmReady(LocalPlayer self) {",
    "        if (!vs2$fixtureWalkSeen(self) || !vs2$backwardConfirmed || !vs2$strafeConfirmed) return false;",
    "        if (vs2$strafeStartTick == Integer.MIN_VALUE || self.tickCount < vs2$strafeStartTick + 15) return false;",
    "        if (!self.onGround() || !Boolean.getBoolean(\"vs2.productionFixtureJumpFloorSupportNow\")) return false;",
    "        String floorTickRaw = System.getProperty(\"vs2.productionFixtureJumpFloorSupportTick\");",
    "        String nativeTickRaw = System.getProperty(\"vs2.phase170NativeContactApplicationTick\");",
    "        if (floorTickRaw == null || nativeTickRaw == null) return false;",
    "        try {",
    "            int floorTick = Integer.parseInt(floorTickRaw);",
    "            int nativeTick = Integer.parseInt(nativeTickRaw);",
    "            boolean floorFresh = floorTick == self.tickCount || floorTick == self.tickCount - 1;",
    "            boolean nativeFresh = nativeTick == self.tickCount",
    "                || nativeTick == self.tickCount - 1",
    "                || nativeTick == self.tickCount - 2",
    "                || nativeTick == self.tickCount - 3;",
    "            return floorFresh && nativeFresh;",
    "        } catch (NumberFormatException ignored) {",
    "            return false;",
    "        }",
    "    }",
])
s = s[:m.start()] + new + s[m.end():]

# Phase131's original source telemetry was bounded to tick 40. Natural-landing fixture
# startup can legitimately settle later (attempt1 walked at tick41), so extend only this
# read-only telemetry window and publish the exact Phase131 physical-support result for
# deferred fixture acceptance. No collision/carry/grounding behavior changes here.
marker = '"GATE_E_PHASE131_SUPPORT_SOURCE player_tick={} carriage_id={} physical_support={}'
marker_pos = probe.find(marker)
if marker_pos < 0:
    raise SystemExit("natural landing harness could not locate Phase131 support source marker")
window_start = max(0, marker_pos - 1400)
window = probe[window_start:marker_pos]
last_guard = window.rfind('player.tickCount <= 40')
if last_guard < 0:
    raise SystemExit("natural landing harness could not locate Phase131 telemetry tick40 guard")
absolute_guard = window_start + last_guard
probe = probe[:absolute_guard] + 'player.tickCount <= 120' + probe[absolute_guard + len('player.tickCount <= 40'):]
marker_pos = probe.find(marker)
logger_pos = probe.rfind('LOGGER.info(', 0, marker_pos)
logger_line_start = probe.rfind('\n', 0, logger_pos) + 1
indent = probe[logger_line_start:logger_pos]
if 'vs2.naturalLandingPhase131SupportTick' not in probe:
    publisher = (
        f'{indent}System.setProperty("vs2.naturalLandingPhase131SupportTick", Integer.toString(player.tickCount));\n'
        f'{indent}System.setProperty("vs2.naturalLandingPhase131SupportNow", Boolean.toString(phase81PhysicalSupport));\n'
    )
    probe = probe[:logger_line_start] + publisher + probe[logger_line_start:]

field_anchor = '''    @Unique private static boolean vs2$backwardConfirmed;\n    @Unique private static boolean vs2$strafeConfirmed;\n'''
field_replacement = '''    @Unique private static boolean vs2$backwardConfirmed;\n    @Unique private static boolean vs2$strafeConfirmed;\n    @Unique private static int vs2$backwardPendingSupportTick = Integer.MIN_VALUE;\n    @Unique private static int vs2$strafePendingSupportTick = Integer.MIN_VALUE;\n'''
if s.count(field_anchor) != 1:
    raise SystemExit(f"natural landing harness expected one locomotion-confirmation field anchor, found {s.count(field_anchor)}")
s = s.replace(field_anchor, field_replacement, 1)

def method_span(text: str, name: str):
    signature = f"    private void {name}("
    start = text.find(signature)
    if start < 0:
        raise SystemExit("natural landing harness could not find method " + name)
    brace = text.find('{', start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == '{':
            depth += 1
        elif text[index] == '}':
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise SystemExit("natural landing harness could not close method " + name)

def defer_confirmation(text: str, name: str, flag: str, property_name: str, pending_field: str, marker_name: str):
    start, end = method_span(text, name)
    method = text[start:end]
    assignment = f'''            {flag} = true;\n            System.setProperty("{property_name}", "true");'''
    if method.count(assignment) != 1:
        raise SystemExit(f"natural landing harness expected one immediate confirmation assignment in {name}")
    method = method.replace(assignment, f'''            {pending_field} = self.tickCount;''', 1)
    if method.count(marker_name) != 1:
        raise SystemExit(f"natural landing harness expected one {marker_name} marker in {name}")
    method = method.replace(marker_name, marker_name.replace('_CONFIRMED', '_MOTION_PENDING'), 1)
    method = method.replace('grounding_deferred_to_create_contact=true', 'awaiting_strict_create_support=true', 1)
    return text[:start] + method + text[end:]

s = defer_confirmation(
    s,
    'vs2$sampleNativeBackward',
    'vs2$backwardConfirmed',
    'vs2.productionFixtureBackwardConfirmed',
    'vs2$backwardPendingSupportTick',
    'GATE_E_M1_NATIVE_BACKWARD_CONFIRMED',
)
s = defer_confirmation(
    s,
    'vs2$sampleNativeStrafe',
    'vs2$strafeConfirmed',
    'vs2.productionFixtureStrafeConfirmed',
    'vs2$strafePendingSupportTick',
    'GATE_E_M1_NATIVE_STRAFE_CONFIRMED',
)

helper_anchor = '''    @Unique\n    private void vs2$sampleNativeBackward(LocalPlayer self, Minecraft client, boolean backwardWindow) {'''
helper = '''    @Unique
    private boolean vs2$naturalLandingStrictSupportForTick(int supportTick) {
        String tickRaw = System.getProperty("vs2.naturalLandingPhase131SupportTick");
        if (tickRaw == null || !Boolean.getBoolean("vs2.naturalLandingPhase131SupportNow")) return false;
        try {
            return Integer.parseInt(tickRaw) == supportTick;
        } catch (NumberFormatException ignored) {
            return false;
        }
    }

    @Unique
    private void vs2$finalizeNaturalLandingLocomotionSupport(LocalPlayer self) {
        if (!vs2$backwardConfirmed
                && vs2$backwardPendingSupportTick != Integer.MIN_VALUE
                && self.tickCount > vs2$backwardPendingSupportTick) {
            int supportTick = vs2$backwardPendingSupportTick;
            if (vs2$naturalLandingStrictSupportForTick(supportTick)) {
                vs2$backwardConfirmed = true;
                System.setProperty("vs2.productionFixtureBackwardConfirmed", "true");
                VS2_FIXTURE_INPUT_LOGGER.info(
                    "GATE_E_M1_NATIVE_BACKWARD_CONFIRMED player_tick={} support_tick={} strict_create_support=true deferred_confirmation=true fixture_only=true vanilla_keymapping=true native_motion=true",
                    self.tickCount, supportTick);
            } else {
                VS2_FIXTURE_INPUT_LOGGER.info(
                    "GATE_E_M1_NATIVE_BACKWARD_REJECTED_NO_CREATE_SUPPORT player_tick={} motion_tick={} support_tick={} support_now={} fixture_only=true acceptance_only=true",
                    self.tickCount, supportTick,
                    System.getProperty("vs2.naturalLandingPhase131SupportTick"),
                    Boolean.getBoolean("vs2.naturalLandingPhase131SupportNow"));
            }
            vs2$backwardPendingSupportTick = Integer.MIN_VALUE;
        }
        if (!vs2$strafeConfirmed
                && vs2$strafePendingSupportTick != Integer.MIN_VALUE
                && self.tickCount > vs2$strafePendingSupportTick) {
            int supportTick = vs2$strafePendingSupportTick;
            if (vs2$naturalLandingStrictSupportForTick(supportTick)) {
                vs2$strafeConfirmed = true;
                System.setProperty("vs2.productionFixtureStrafeConfirmed", "true");
                VS2_FIXTURE_INPUT_LOGGER.info(
                    "GATE_E_M1_NATIVE_STRAFE_CONFIRMED player_tick={} support_tick={} strict_create_support=true deferred_confirmation=true fixture_only=true vanilla_keymapping=true native_motion=true direction=right",
                    self.tickCount, supportTick);
            } else {
                VS2_FIXTURE_INPUT_LOGGER.info(
                    "GATE_E_M1_NATIVE_STRAFE_REJECTED_NO_CREATE_SUPPORT player_tick={} motion_tick={} support_tick={} support_now={} fixture_only=true acceptance_only=true direction=right",
                    self.tickCount, supportTick,
                    System.getProperty("vs2.naturalLandingPhase131SupportTick"),
                    Boolean.getBoolean("vs2.naturalLandingPhase131SupportNow"));
            }
            vs2$strafePendingSupportTick = Integer.MIN_VALUE;
        }
    }

'''
if s.count(helper_anchor) != 1:
    raise SystemExit(f"natural landing harness expected one backward helper anchor, found {s.count(helper_anchor)}")
s = s.replace(helper_anchor, helper + helper_anchor, 1)

head_anchor = '''        if (client.player != self) return;\n        vs2$nativeAiStepTick = self.tickCount;'''
head_replacement = '''        if (client.player != self) return;\n        vs2$finalizeNaturalLandingLocomotionSupport(self);\n        vs2$nativeAiStepTick = self.tickCount;'''
if s.count(head_anchor) != 1:
    raise SystemExit(f"natural landing harness expected one LocalPlayer aiStep HEAD anchor, found {s.count(head_anchor)}")
s = s.replace(head_anchor, head_replacement, 1)

old_window = '''        boolean jumpWindow = !vs2$jumpLandedLogged
            && (vs2$jumpArmReady(self) || vs2$jumpStartTick != Integer.MIN_VALUE);
'''
new_window = '''        // Natural-landing CI only: keep vanilla aiStep alive for a bounded arc even if the
        // generic onGround observer emits an early landing marker before Create support returns.
        boolean jumpWindow = vs2$jumpStartTick != Integer.MIN_VALUE
            ? self.tickCount <= vs2$jumpStartTick + 40
            : vs2$jumpArmReady(self);
'''
if s.count(old_window) != 1:
    raise SystemExit(f"natural landing harness expected one headless jumpWindow, found {s.count(old_window)}")
s = s.replace(old_window, new_window, 1)

required_fixture = [
    'vs2$backwardPendingSupportTick',
    'vs2$strafePendingSupportTick',
    'vs2$finalizeNaturalLandingLocomotionSupport(self)',
    'GATE_E_M1_NATIVE_BACKWARD_MOTION_PENDING',
    'GATE_E_M1_NATIVE_STRAFE_MOTION_PENDING',
    'GATE_E_M1_NATIVE_BACKWARD_REJECTED_NO_CREATE_SUPPORT',
    'GATE_E_M1_NATIVE_STRAFE_REJECTED_NO_CREATE_SUPPORT',
    'strict_create_support=true',
    'self.tickCount <= vs2$jumpStartTick + 40',
]
missing_fixture = [token for token in required_fixture if token not in s]
if missing_fixture:
    raise SystemExit("natural landing harness lost deferred-support anchors: " + ", ".join(missing_fixture))

required_probe = [
    'GATE_E_PHASE131_SUPPORT_SOURCE',
    'player.tickCount <= 120',
    'vs2.naturalLandingPhase131SupportTick',
    'vs2.naturalLandingPhase131SupportNow',
    'Boolean.toString(phase81PhysicalSupport)',
]
missing_probe = [token for token in required_probe if token not in probe]
if missing_probe:
    raise SystemExit("natural landing harness lost exact Phase131 support publisher: " + ", ".join(missing_probe))

inserted = new + new_window + helper + field_replacement
for forbidden in ["self.setPos(", "self.setDeltaMovement(", "self.move(", ".teleport(", "setVelocity(", "setNoGravity(", "setOnGround("]:
    if forbidden in inserted:
        raise SystemExit("natural landing harness introduced forbidden movement mutation: " + forbidden)

p.write_text(s, encoding="utf-8")
probe_path.write_text(probe, encoding="utf-8")
print("REFERENCE_OWNER_V2_NATURAL_LANDING_HARNESS_V2 fixture_only=true original_locomotion_sequence_preserved=true deferred_phase131_support_confirmation=true phase131_telemetry_extended_to_120=true bounded_native_airstep_through_false_landing=true direct_motion_mutation=false")
