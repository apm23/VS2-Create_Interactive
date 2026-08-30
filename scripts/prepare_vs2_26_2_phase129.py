#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #137 proved that vanilla onGround is not a valid completion signal
# for Create contact acquisition: onGround stayed true while Create contact expired and
# the moving carriage outran the LocalPlayer. Keep the archived-world setup deterministic
# by reacquiring the real simplified collider for exactly twelve bounded fixture ticks,
# regardless of vanilla onGround. Carry proof is explicitly delayed until that assisted
# setup window is over, so no repositioned sample can satisfy the production stability gate.
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

# Phase 127 continuity telemetry must only observe unassisted production carry. Extend
# its observation tail slightly, but suppress every sample until all twelve fixture-only
# acquisition attempts are complete. This prevents the setup repositions from making the
# sustained carriage-local gate pass artificially.
continuity_old = 'if (productionSmokeFixture && player.tickCount >= 14 && player.tickCount <= 32) {'
continuity_new = 'if (productionSmokeFixture && fixtureContactAcquireTicks >= 12 && player.tickCount >= 14 && player.tickCount <= 40) {'
if continuity_new not in source:
    if continuity_old not in source:
        raise SystemExit("Phase 129 could not isolate Phase 127 continuity proof from fixture acquisition")
    source = source.replace(continuity_old, continuity_new, 1)

required = [
    'productionSmokeFixture && fixtureContactAcquireTicks < 12',
    'fixtureContactAcquireTicks >= 12',
    'player.tickCount <= 40',
    'GATE_E_FIXTURE_CONTACT_ACQUIRE',
    'bounded=true fixture_only=true',
    'GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK',
    'GATE_E_FIXTURE_COLLIDER_REPOSITIONED',
    'GATE_E_CARRIAGE_LOCAL_CONTINUITY',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 129 lost bounded fixture-contact/carry-proof anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 129: bounded 12-tick fixture contact acquisition, then unassisted carriage-local carry proof; production carry unchanged")
