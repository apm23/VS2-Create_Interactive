#!/usr/bin/env python3
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #243 showed an evidence-backed duplicate carry on carriage 10:
# strict support returned at tick 37, Phase85 immediately replayed Create's contact
# motion, and the resulting player delta exceeded carriage motion; tick 38 then replayed
# again under the one-tick grace and was exactly 2x carriage motion. Do not invent a new
# carry vector or alter VS2/Create physics. Instead, suppress the existing compatibility
# replay for exactly the first strictly-supported tick after support is reacquired, giving
# Create's native carry one observation tick. If native carry is still unhealthy on the
# following supported tick, the existing Phase131/137 evidence-driven replay path remains
# eligible as before.
replay_token = "carryReplayPlayerTick != player.tickCount"
replay_pos = source.find(replay_token)
if replay_pos < 0 or source.find(replay_token, replay_pos + 1) >= 0:
    raise SystemExit("Phase 150 expected exactly one final Phase85 replay predicate")

search_start = max(0, replay_pos - 7000)
prefix = source[search_start:replay_pos]
candidates = list(re.finditer(r'(?m)^(?P<indent>[ \t]*)if \(', prefix))
replay_if_pos = None
replay_indent = None
for candidate in reversed(candidates):
    absolute = search_start + candidate.start()
    segment = source[absolute:replay_pos]
    if "phase81PhysicalSupport" in segment and "collisionEligible" in segment:
        replay_if_pos = absolute
        replay_indent = candidate.group("indent")
        break
if replay_if_pos is None or replay_indent is None:
    raise SystemExit("Phase 150 could not locate final Phase85 replay guard")

if "GATE_E_PHASE150_SUPPORT_REACQUIRE_NATIVE_OBSERVATION" not in source:
    probe = (
        f'{replay_indent}String phase150SupportTickKey = "vs2.phase150LastStrictSupportTick." + carriage.getId();\n'
        f'{replay_indent}int phase150LastStrictSupportTick;\n'
        f'{replay_indent}try {{\n'
        f'{replay_indent}    phase150LastStrictSupportTick = Integer.parseInt(System.getProperty(phase150SupportTickKey, "-2147483648"));\n'
        f'{replay_indent}}} catch (NumberFormatException ignored) {{\n'
        f'{replay_indent}    phase150LastStrictSupportTick = Integer.MIN_VALUE;\n'
        f'{replay_indent}}}\n'
        f'{replay_indent}boolean phase150StrictSupportNow = productionSmoke && explicitCarryCompat\n'
        f'{replay_indent}    && phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround();\n'
        f'{replay_indent}boolean phase150SupportReacquired = phase150StrictSupportNow\n'
        f'{replay_indent}    && phase150LastStrictSupportTick != player.tickCount - 1;\n'
        f'{replay_indent}if (phase150StrictSupportNow) {{\n'
        f'{replay_indent}    System.setProperty(phase150SupportTickKey, Integer.toString(player.tickCount));\n'
        f'{replay_indent}}}\n'
        f'{replay_indent}if (phase150SupportReacquired) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE150_SUPPORT_REACQUIRE_NATIVE_OBSERVATION carriage_id={{}} player_tick={{}} last_strict_support_tick={{}} replay_suppressed_one_tick=true native_observation=true",\n'
        f'{replay_indent}        carriage.getId(), player.tickCount, phase150LastStrictSupportTick);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + probe + source[replay_if_pos:]

suppression_old = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))))'''
suppression_new = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))
                                || phase150SupportReacquired))'''
if suppression_new not in source:
    if suppression_old not in source:
        raise SystemExit("Phase 150 could not find Phase137 adaptive replay suppression")
    source = source.replace(suppression_old, suppression_new, 1)

required = [
    "GATE_E_PHASE150_SUPPORT_REACQUIRE_NATIVE_OBSERVATION",
    "vs2.phase150LastStrictSupportTick.",
    "phase150SupportReacquired",
    "phase150LastStrictSupportTick != player.tickCount - 1",
    "|| phase150SupportReacquired",
    "replay_suppressed_one_tick=true",
    "native_observation=true",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 150 lost support-reacquire replay guards: " + ", ".join(missing))

for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in probe if 'probe' in locals() else False:
        raise SystemExit("Phase 150 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 150: suppresses compatibility replay for one native-observation tick when strict Create support is reacquired; no new carry vector or physics mutation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase151.py")), run_name="__main__")
