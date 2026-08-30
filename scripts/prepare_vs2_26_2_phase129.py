#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #133 showed a harness race rather than a production carry failure:
# the one-shot simplified-collider normalization ran while the train was moving several
# blocks per client tick, so the carriage outran the fixture before Create could promote
# LocalPlayer to genuine contact/onGround. Re-acquire the same real Create simplified
# collider for a small bounded setup window, but only while genuine onGround contact is
# still absent. The production carry proof already requires on_ground=true, so none of
# these assisted acquisition ticks can satisfy the sustained stability gate.
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
        # Some phases wrap the condition across lines. Use a bounded multiline form,
        # still requiring fixtureColliderNormalized and the immediately following try.
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
        f'{indent}        || (productionSmokeFixture && !player.onGround() && fixtureContactAcquireTicks < 12)) {{\n'
        f'{indent}    if (productionSmokeFixture && !player.onGround()) {{\n'
        f'{indent}        fixtureContactAcquireTicks++;\n'
        f'{indent}        LOGGER.info(\n'
        f'{indent}            "GATE_E_FIXTURE_CONTACT_ACQUIRE player_tick={{}} attempt={{}} bounded=true fixture_only=true",\n'
        f'{indent}            player.tickCount, fixtureContactAcquireTicks);\n'
        f'{indent}    }}\n'
        f'{indent}    try {{'
    )
    source = source[:match.start()] + replacement + source[match.end():]

required = [
    'fixtureContactAcquireTicks < 12',
    'productionSmokeFixture && !player.onGround()',
    'GATE_E_FIXTURE_CONTACT_ACQUIRE',
    'bounded=true fixture_only=true',
    'GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK',
    'GATE_E_FIXTURE_COLLIDER_REPOSITIONED',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 129 lost bounded fixture-contact anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 129: resilient bounded fixture-only collider reacquisition until genuine Create standing contact; production carry unchanged")
