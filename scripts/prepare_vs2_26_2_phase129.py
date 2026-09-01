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
# LocalPlayer to genuine contact/onGround. Production-world #178 then reached a newly
# aligned collider on the twelfth and final attempt, but fixture assistance stopped before
# Create had another client tick to promote that alignment into contact/baseline capture.
# Production-world #187 showed the same harness race at the old 16-tick bound: baseline
# remained false through tick 38 and only captured at tick 39 after assistance had already
# stopped, producing a stale 36-block frame replay instead of a valid carry sample.
# Production-world #334 reproduced the late-promotion race after the old 32-attempt window.
# Later cumulative support/carry fixes changed that boundary: production-world #493 now
# proves genuine strict support plus exact same-carriage native Create application well
# before attempt 32, while keeping fixture retargeting active through attempt 48 leaves only
# ticks 49-50 for unassisted readiness before the finite-route frame is lost at tick 51.
# Bound acquisition at 32 again so the already-proven stable interval can be observed
# unassisted. This changes only the disposable production-smoke fixture, not gameplay carry.
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
# Once Create has captured a native carriage baseline, fixture retargeting must stop:
# continuing to chase the moving collider destroys the exact native frame we just proved.
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
        f'{indent}        || (productionSmokeFixture && !carryBaselineCaptured && fixtureContactAcquireTicks < 32)) {{\n'
        f'{indent}    if (productionSmokeFixture && !carryBaselineCaptured && fixtureContactAcquireTicks < 32) {{\n'
        f'{indent}        fixtureContactAcquireTicks++;\n'
        f'{indent}        LOGGER.info(\n'
        f'{indent}            "GATE_E_FIXTURE_CONTACT_ACQUIRE player_tick={{}} attempt={{}} bounded=true fixture_only=true",\n'
        f'{indent}            player.tickCount, fixtureContactAcquireTicks);\n'
        f'{indent}    }}\n'
        f'{indent}    try {{'
    )
    source = source[:match.start()] + replacement + source[match.end():]

# Keep carriage-local continuity telemetry out of assisted setup. As soon as Create
# captures a native baseline, assistance has ended and the production gate may observe
# the resulting unassisted frame; otherwise retain the hard 32-attempt fallback bound.
source = source.replace(
    '''if (productionSmokeFixture && player.tickCount >= 14 && player.tickCount <= 32) {''',
    '''if (productionSmokeFixture && (carryBaselineCaptured || fixtureContactAcquireTicks >= 32) && player.tickCount >= 14 && player.tickCount <= 72) {''',
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
        f'{replay_indent}if (productionSmokeFixture && (carryBaselineCaptured || fixtureContactAcquireTicks >= 32) '
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
    '!carryBaselineCaptured && fixtureContactAcquireTicks < 32',
    '(carryBaselineCaptured || fixtureContactAcquireTicks >= 32)',
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
    raise SystemExit("Phase 129 lost bounded fixture/contact telemetry anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 129: stops fixture retargeting immediately after native baseline capture; 32 attempts remain the fallback bound")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase130.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase131.py")), run_name="__main__")
