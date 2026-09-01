#!/usr/bin/env python3
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #627 proved that baseline capture alone is not a safe fixture handoff.
# At tick 20 the baseline was captured on strict supported carriage 10, but ticks 21-25 still
# under-carried badly while the carriage moved several blocks per tick; because acquisition had
# already stopped, the player was left behind before Create's native carry could settle. Reuse the
# existing Phase134/137 native-carry-health publication as the handoff criterion. The disposable
# fixture may keep aligning until one real supported native carry sample is healthy, then latches
# off permanently; 32 attempts remain the hard fallback. No new carry vector or gameplay physics.
field_old = '''    private static boolean fixtureColliderNormalized;\n'''
field_new = '''    private static boolean fixtureColliderNormalized;\n    private static int fixtureContactAcquireTicks;\n    private static boolean fixtureNativeCarrySettled;\n'''
if "fixtureContactAcquireTicks" not in source:
    if field_old not in source:
        raise SystemExit("Phase 129 could not find fixture collider normalization field")
    source = source.replace(field_old, field_new, 1)
elif "fixtureNativeCarrySettled" not in source:
    field_existing = '''    private static int fixtureContactAcquireTicks;\n'''
    if field_existing not in source:
        raise SystemExit("Phase 129 could not find existing fixture acquisition counter field")
    source = source.replace(
        field_existing,
        field_existing + '''    private static boolean fixtureNativeCarrySettled;\n''',
        1,
    )

# Match the final fixture normalization guard structurally. Preserve the existing setup predicates,
# but continue bounded retargeting until already-existing native carry health says the captured frame
# is actually following the carriage. The health property is published by the later cumulative
# Phase137 preparation into the final source; this phase only consumes that established signal.
if "GATE_E_FIXTURE_CONTACT_ACQUIRE" not in source:
    pattern = re.compile(
        r'(?P<indent>\s*)if \((?P<cond>[^\n{}]*fixtureColliderNormalized[^\n{}]*)\) \{\n(?P=indent)    try \{'
    )
    match = pattern.search(source)
    if match is None:
        pattern = re.compile(
            r'(?P<indent>\s*)if \((?P<cond>[\s\S]{0,500}?fixtureColliderNormalized[\s\S]{0,500}?)\) \{\n(?P=indent)    try \{'
        )
        match = pattern.search(source)
    if match is None:
        raise SystemExit("Phase 129 could not locate final fixture collider guard")

    indent = match.group("indent")
    cond = match.group("cond").strip()
    if "productionSmokeFixture" not in cond and "ciHarness" not in cond:
        raise SystemExit("Phase 129 refused collider guard without fixture isolation boundary")

    replacement = (
        f'{indent}if (productionSmokeFixture && !fixtureNativeCarrySettled && carryBaselineCaptured '
        f'&& carryBaselineCarriageId != Integer.MIN_VALUE) {{\n'
        f'{indent}    boolean phase129NativeCarryHealthy = Boolean.parseBoolean(System.getProperty(\n'
        f'{indent}        "vs2.phase134NativeCarryHealthy." + carryBaselineCarriageId, "false"))\n'
        f'{indent}        || Integer.toString(player.tickCount - 1).equals(System.getProperty(\n'
        f'{indent}            "vs2.phase134NativeCarryHealthyTick." + carryBaselineCarriageId));\n'
        f'{indent}    if (phase129NativeCarryHealthy) {{\n'
        f'{indent}        fixtureNativeCarrySettled = true;\n'
        f'{indent}    }}\n'
        f'{indent}}}\n'
        f'{indent}if (({cond})\n'
        f'{indent}        || (productionSmokeFixture && !fixtureNativeCarrySettled && fixtureContactAcquireTicks < 32)) {{\n'
        f'{indent}    if (productionSmokeFixture && !fixtureNativeCarrySettled && fixtureContactAcquireTicks < 32) {{\n'
        f'{indent}        fixtureContactAcquireTicks++;\n'
        f'{indent}        LOGGER.info(\n'
        f'{indent}            "GATE_E_FIXTURE_CONTACT_ACQUIRE player_tick={{}} attempt={{}} bounded=true fixture_only=true",\n'
        f'{indent}            player.tickCount, fixtureContactAcquireTicks);\n'
        f'{indent}    }}\n'
        f'{indent}    try {{'
    )
    source = source[:match.start()] + replacement + source[match.end():]

# Continuity is production evidence only after assistance has actually ended. Native carry health
# is the preferred handoff; the hard 32-attempt limit remains the fallback if it never appears.
source = source.replace(
    '''if (productionSmokeFixture && player.tickCount >= 14 && player.tickCount <= 32) {''',
    '''if (productionSmokeFixture && (fixtureNativeCarrySettled || fixtureContactAcquireTicks >= 32) && player.tickCount >= 14 && player.tickCount <= 72) {''',
    1,
)

# Trace the existing replay guard only in the same unassisted observation interval.
if "GATE_E_PHASE130_REPLAY_GUARD" not in source:
    replay_tick_token = "carryReplayPlayerTick != player.tickCount"
    replay_tick_pos = source.find(replay_tick_token)
    if replay_tick_pos < 0:
        raise SystemExit("Phase 129 could not locate Phase85 replay tick predicate")

    search_start = max(0, replay_tick_pos - 5000)
    prefix = source[search_start:replay_tick_pos]
    candidates = list(re.finditer(r'(?m)^(?P<indent>[ \t]*)if \(', prefix))
    replay_match = None
    for candidate in reversed(candidates):
        absolute = search_start + candidate.start()
        segment = source[absolute:replay_tick_pos]
        if "phase81PhysicalSupport" in segment:
            replay_match = candidate
            replay_if_pos = absolute
            break
    if replay_match is None:
        raise SystemExit("Phase 129 could not locate structural Phase85 replay guard")

    replay_indent = replay_match.group("indent")
    replay_probe = (
        f'{replay_indent}if (productionSmokeFixture && (fixtureNativeCarrySettled || fixtureContactAcquireTicks >= 32) '
        f'&& player.tickCount >= 14 && player.tickCount <= 72) {{\n'
        f'{replay_indent}    LOGGER.info(\n'
        f'{replay_indent}        "GATE_E_PHASE130_REPLAY_GUARD player_tick={{}} carriage_id={{}} baseline_captured={{}} physical_support={{}} collision_eligible={{}} broadphase={{}} baseline_carriage_id={{}} rebase_tick={{}} rebase_age={{}} replay_tick={{}} read_only=true",\n'
        f'{replay_indent}        player.tickCount, carriage.getId(), carryBaselineCaptured, phase81PhysicalSupport, collisionEligible, broadphaseOverlap,\n'
        f'{replay_indent}        carryBaselineCarriageId, carryBaselineRebaseTick,\n'
        f'{replay_indent}        carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,\n'
        f'{replay_indent}        carryReplayPlayerTick);\n'
        f'{replay_indent}}}\n\n'
    )
    source = source[:replay_if_pos] + replay_probe + source[replay_if_pos:]

required = [
    'fixtureContactAcquireTicks < 32',
    'fixtureNativeCarrySettled',
    '!fixtureNativeCarrySettled && fixtureContactAcquireTicks < 32',
    '(fixtureNativeCarrySettled || fixtureContactAcquireTicks >= 32)',
    'vs2.phase134NativeCarryHealthy.',
    'vs2.phase134NativeCarryHealthyTick.',
    'GATE_E_FIXTURE_CONTACT_ACQUIRE',
    'bounded=true fixture_only=true',
    'GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK',
    'GATE_E_FIXTURE_COLLIDER_REPOSITIONED',
    'player.tickCount <= 72',
    'GATE_E_PHASE130_REPLAY_GUARD',
    'physical_support={}',
    'rebase_age={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 129 lost bounded fixture/native-carry handoff anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 129: releases fixture only after existing native carry health settles, with 32 attempts as fallback")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase130.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase131.py")), run_name="__main__")
