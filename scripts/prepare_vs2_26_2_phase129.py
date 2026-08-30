#!/usr/bin/env python3
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #133 showed a harness race rather than a production carry failure:
# the one-shot simplified-collider normalization ran while the train was moving several
# blocks per client tick, so the carriage outran the fixture before Create could promote
# LocalPlayer to genuine contact/onGround. Use a fixed, bounded 12-tick setup window to
# reacquire a real Create simplified collider. Crucially, do not use vanilla onGround as
# the stop condition: production-world #137 proved onGround can remain true after Create
# contact is already gone. After the 12 setup ticks, all fixture assistance stops and the
# sustained carry proof must be entirely unassisted.
field_old = '''    private static boolean fixtureColliderNormalized;\n'''
field_new = '''    private static boolean fixtureColliderNormalized;\n    private static int fixtureContactAcquireTicks;\n'''
if "fixtureContactAcquireTicks" not in source:
    if field_old not in source:
        raise SystemExit("Phase 129 could not find fixture collider normalization field")
    source = source.replace(field_old, field_new, 1)

# Later preparation phases may add timing predicates to the Phase 67/86/87 guard.
# Match the final guard structurally instead of pinning an exact text form: it must be
# an if-condition containing fixtureColliderNormalized and immediately enter the same
# try block. Preserve every existing predicate and only OR in bounded fixture retry.
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
        f'{indent}if (({cond})\n'
        f'{indent}        || (productionSmokeFixture && fixtureContactAcquireTicks < 12)) {{\n'
        f'{indent}    if (productionSmokeFixture && fixtureContactAcquireTicks < 12) {{\n'
        f'{indent}        fixtureContactAcquireTicks++;\n'
        f'{indent}        LOGGER.info(\n'
        f'{indent}            "GATE_E_FIXTURE_CONTACT_ACQUIRE player_tick={{}} attempt={{}} bounded=true fixture_only=true",\n'
        f'{indent}            player.tickCount, fixtureContactAcquireTicks);\n'
        f'{indent}    }}\n'
        f'{indent}    try {{'
    )
    source = source[:match.start()] + replacement + source[match.end():]

# Keep carriage-local continuity telemetry out of the assisted setup interval. The
# production gate therefore only sees samples produced after all fixture repositioning
# has stopped. Extend the observation window so CI still has enough unassisted ticks.
source = source.replace(
    '''if (productionSmokeFixture && player.tickCount >= 14 && player.tickCount <= 32) {''',
    '''if (productionSmokeFixture && fixtureContactAcquireTicks >= 12 && player.tickCount >= 14 && player.tickCount <= 40) {''',
    1,
)

# Production-world #138 still lost carry immediately after the bounded fixture window.
# Do not alter movement yet: trace every predicate that can suppress the already-validated
# Create-computed/filtered Phase85 replay, including sibling-carriage rebase settling.
# The final replay guard has been rewritten by several cumulative phases, so anchor on
# the unique replay-tick predicate and select the nearest preceding if-block that still
# contains the physical-support predicate. This keeps telemetry resilient without making
# the preparation chain depend on the exact textual order of replay predicates.
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
        f'{replay_indent}if (productionSmokeFixture && fixtureContactAcquireTicks >= 12 '
        f'&& player.tickCount >= 14 && player.tickCount <= 40) {{\n'
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
    'fixtureContactAcquireTicks < 12',
    'fixtureContactAcquireTicks >= 12',
    'GATE_E_FIXTURE_CONTACT_ACQUIRE',
    'bounded=true fixture_only=true',
    'GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK',
    'GATE_E_FIXTURE_COLLIDER_REPOSITIONED',
    'player.tickCount <= 40',
    'GATE_E_PHASE130_REPLAY_GUARD',
    'physical_support={}',
    'rebase_age={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 129 lost bounded fixture/contact telemetry anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 129: bounded fixture acquisition plus read-only post-acquisition Phase85 guard telemetry; production carry unchanged")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase130.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase131.py")), run_name="__main__")
