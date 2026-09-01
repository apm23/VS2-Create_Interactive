#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #365 kept the player grounded, broadphase-valid and support_healthy while
# Create legitimately transferred active support from carriage 7 to sibling carriage 4.
# Phase156/163 already reset per-tick local-step accounting on that supported handoff, but
# Phase154's final displacement still compared the carriage-7 start vector directly with the
# carriage-4 end vector, producing a meaningless 13.8-block cross-frame distance and false
# failure. Accumulate only validated within-frame local steps and use that scalar for the
# fixture proof. Test accounting only: no player/carry/train/world/physics mutation.
field_anchor = "    private static boolean phase154WalkSupportHealthy = true;\n"
field_insert = field_anchor + "    private static double phase182WalkAccumulatedLocalDistance;\n"
if "phase182WalkAccumulatedLocalDistance" not in source:
    if source.count(field_anchor) != 1:
        raise SystemExit("Phase 182 expected exactly one Phase154 support-health field")
    source = source.replace(field_anchor, field_insert, 1)

# Anchor the reset to the actual input transition, not to surrounding initialization lines.
# Later harness patches may insert accounting between phase154WalkStartLocal/PreviousLocal,
# while the validated sibling-handoff recovery never immediately presses the forward key.
start_anchor = '''                            phase154WalkSupportHealthy = true;
                            client.options.keyUp.setDown(true);
'''
start_insert = '''                            phase154WalkSupportHealthy = true;
                            phase182WalkAccumulatedLocalDistance = 0.0;
                            client.options.keyUp.setDown(true);
'''
if "phase182WalkAccumulatedLocalDistance = 0.0;" not in source:
    if source.count(start_anchor) != 1:
        raise SystemExit("Phase 182 expected exactly one Phase154 walk input-start block")
    source = source.replace(start_anchor, start_insert, 1)

marker = "GATE_E_PHASE156_WALK_FRAME_GUARD"
marker_pos = source.find(marker)
if marker_pos < 0:
    raise SystemExit("Phase 182 could not find Phase156 walk-frame guard")
assignment = "                            phase154WalkPreviousLocal = phase154Local;\n"
assignment_pos = source.find(assignment, marker_pos)
if assignment_pos < 0:
    raise SystemExit("Phase 182 could not find Phase156 previous-local update")
accumulation = '''                            if (phase154SupportNow
                                    && !phase156SiblingHandoff
                                    && !phase160PreviousReplayAccountingSeam
                                    && (phase160GuardStep <= 0.75 || phase166FixturePulseStep)) {
                                phase182WalkAccumulatedLocalDistance += phase160GuardStep;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE182_WALK_DISTANCE player_tick={} carriage_id={} guard_step={} accumulated_local_distance={} sibling_handoff={} replay_accounting_seam={} fixture_pulse_step={} support_healthy={} fixture_only=true read_only_accounting=true",
                                player.tickCount, phase154Carriage.getId(), phase160GuardStep,
                                phase182WalkAccumulatedLocalDistance, phase156SiblingHandoff,
                                phase160PreviousReplayAccountingSeam, phase166FixturePulseStep, phase154WalkSupportHealthy);
'''
if "GATE_E_PHASE182_WALK_DISTANCE" not in source:
    source = source[:assignment_pos] + accumulation + source[assignment_pos:]

old_final = '''                                double phase154LocalDistance = phase154WalkStartLocal == null
                                    ? 0.0 : phase154Local.distanceTo(phase154WalkStartLocal);'''
new_final = '''                                double phase154LocalDistance = phase182WalkAccumulatedLocalDistance;'''
if old_final in source:
    source = source.replace(old_final, new_final, 1)
elif new_final not in source:
    raise SystemExit("Phase 182 could not find Phase154 final cross-frame distance calculation")

old_proof = '''                                    && phase165WalkPathDistance >= 0.20 && phase165WalkPathDistance <= 4.00
                                    && phase154LocalDistance <= 3.00;'''
new_proof = '''                                    && phase154LocalDistance >= 0.20 && phase154LocalDistance <= 4.00;'''
if old_proof in source:
    source = source.replace(old_proof, new_proof, 1)
elif new_proof not in source:
    raise SystemExit("Phase 182 could not find cumulative Phase165 walk completion proof")

required = [
    "phase182WalkAccumulatedLocalDistance",
    "phase182WalkAccumulatedLocalDistance = 0.0",
    "GATE_E_PHASE182_WALK_DISTANCE",
    "!phase156SiblingHandoff",
    "!phase160PreviousReplayAccountingSeam",
    "phase160GuardStep <= 0.75 || phase166FixturePulseStep",
    "double phase154LocalDistance = phase182WalkAccumulatedLocalDistance;",
    "phase154LocalDistance >= 0.20",
    "phase154LocalDistance <= 4.00",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 182 lost sibling-frame walk-accounting anchors: " + ", ".join(missing))

patch_text = field_insert + start_insert + accumulation + new_final + new_proof
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 182 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 182: makes bounded walk displacement accounting sibling-carriage-frame aware; fixture accounting only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase183.py")), run_name="__main__")
