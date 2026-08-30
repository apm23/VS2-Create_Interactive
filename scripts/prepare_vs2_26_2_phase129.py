#!/usr/bin/env python3
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

# Phase 86/87 deliberately wrapped the Phase 67 one-shot guard with the harness/
# productionSmokeFixture isolation boundary. Patch that final post-isolation form,
# preserving the boundary while allowing bounded retries only for productionSmokeFixture.
condition_old = '''            if ((ciHarness || productionSmokeFixture) && !fixtureColliderNormalized) {\n                try {'''
condition_new = '''            if ((ciHarness || productionSmokeFixture)\n                    && (!fixtureColliderNormalized\n                        || (productionSmokeFixture && !player.onGround() && fixtureContactAcquireTicks < 12))) {\n                if (productionSmokeFixture && !player.onGround()) {\n                    fixtureContactAcquireTicks++;\n                    LOGGER.info(\n                        "GATE_E_FIXTURE_CONTACT_ACQUIRE player_tick={} attempt={} bounded=true fixture_only=true",\n                        player.tickCount, fixtureContactAcquireTicks);\n                }\n                try {'''
if "GATE_E_FIXTURE_CONTACT_ACQUIRE" not in source:
    if condition_old not in source:
        raise SystemExit("Phase 129 could not find Phase 87 isolated collider condition")
    source = source.replace(condition_old, condition_new, 1)

required = [
    '(ciHarness || productionSmokeFixture)',
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

# This phase does not introduce a new movement primitive. It only permits the existing
# productionSmokeFixture-only Phase 67/68 re-positioner to retry during contact setup.
# Once Create reports onGround, the retry condition becomes false and normal production
# carry is solely responsible for all samples accepted by the sustained stability gate.
client_probe.write_text(source, encoding="utf-8")
print("Phase 129: bounded fixture-only collider reacquisition until genuine Create standing contact; production carry unchanged")
