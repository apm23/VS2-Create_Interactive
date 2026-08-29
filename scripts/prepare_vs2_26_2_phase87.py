#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
source = client_probe.read_text(encoding="utf-8")

# Phase 86 separated fixture behavior from the carry compatibility path, but its
# ciHarness switch still implicitly treated every GitHub Actions JVM as a fixture
# run. Preserve existing CI behavior for regression stability while adding an
# explicit production-smoke escape hatch. A runner launched with
# -Dvs2.productionSmoke=true can now exercise ci_harness=false even inside Actions.
old = '''        boolean ciHarness = Boolean.getBoolean("vs2.gateD") || "true".equals(System.getenv("GITHUB_ACTIONS"));'''
new = '''        boolean productionSmoke = Boolean.getBoolean("vs2.productionSmoke");
        boolean ciHarness = Boolean.getBoolean("vs2.gateD") || ("true".equals(System.getenv("GITHUB_ACTIONS")) && !productionSmoke);'''
if new not in source:
    if old not in source:
        raise SystemExit("Phase 87 could not find Phase 86 ciHarness switch")
    source = source.replace(old, new, 1)

required = [
    'boolean explicitCarryCompat = Boolean.getBoolean("vs2.createCarryCompat")',
    'VS2_CREATE_CARRY_COMPAT_MODE ci_harness={} explicit_opt_in={}',
    'if (ciHarness && !fixtureClientNormalized',
    'if (ciHarness && !fixtureColliderNormalized',
    'GATE_E_PHASE85_CARRY_REPLAY',
    'vs2.productionSmoke',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 87 lost production/harness isolation anchors: " + ", ".join(missing))

# Production-world run 2 proved the explicit compatibility path can load the real
# train world with ci_harness=false and observe genuine carriage motion, but Phase
# 85 never fires because its historical smoke-only guard still requires
# carryBaselineCaptured. That baseline was created by the CI normalization/contact
# fixture and is intentionally unavailable in production mode. The actual safety
# predicate we validated is the current Create simplified collider directly under
# the LocalPlayer, plus collisionEligible+broadphaseOverlap and Create's own
# getContactPointMotion -> ContraptionCollider.collide result. Allow explicit
# production opt-in to use that strict current physical-support predicate without
# requiring a prior CI-only contact baseline. CI behavior remains unchanged.
old_carry_guard = '''            if (carryBaselineCaptured
                && phase81PhysicalSupport'''
new_carry_guard = '''            if ((carryBaselineCaptured || explicitCarryCompat)
                && phase81PhysicalSupport'''
carry_guard_count = source.count(old_carry_guard)
if carry_guard_count < 2:
    raise SystemExit(f"Phase 87 expected both Phase 85 production carry guards, found {carry_guard_count}")
source = source.replace(old_carry_guard, new_carry_guard, 2)

# Production-world run 3 still emitted no Phase 85 replay marker. The old Phase 81
# support-continuity telemetry itself was also hidden behind carryBaselineCaptured,
# so the failed run could not tell whether strict physical support, collision
# eligibility, or broadphase overlap was the blocker. Expose at most 40 samples
# whenever explicit production compatibility is enabled. This is read-only
# telemetry; no position, velocity, contact lease, train control, or collision
# response is changed.
old_support_log = '''            if (carryBaselineCaptured && carryReplayGuardSamples <= 40) {
                LOGGER.info('''
new_support_log = '''            if ((carryBaselineCaptured || explicitCarryCompat) && carryReplayGuardSamples < 40) {
                carryReplayGuardSamples++;
                LOGGER.info('''
if old_support_log not in source:
    raise SystemExit("Phase 87 could not find Phase 81 support-continuity telemetry guard")
source = source.replace(old_support_log, new_support_log, 1)

production_required = [
    '(carryBaselineCaptured || explicitCarryCompat)',
    'phase81PhysicalSupport',
    'collisionEligible',
    'broadphaseOverlap',
    'GATE_E_PHASE85_CARRY_REPLAY',
    'GATE_E_PHASE81_SUPPORT_CONTINUITY',
]
production_missing = [token for token in production_required if token not in source]
if production_missing:
    raise SystemExit("Phase 87 lost strict production carry anchors: " + ", ".join(production_missing))

client_probe.write_text(source, encoding="utf-8")

# The server-side Gate D fixture normalization from Phases 60/69/70 is also a
# deliberate smoke-harness mutation. Without this guard, a GitHub production-smoke
# JVM would still reposition ServerPlayer and apply the one-shot gravity probe even
# though the LocalPlayer fixture path is disabled. Keep normal CI unchanged, but
# make productionSmoke a strict no-fixture boundary on both sides.
server = server_probe.read_text(encoding="utf-8")
old_server_guard = '''            if (!fixturePlayerChecked) {'''
new_server_guard = '''            if (!java.lang.Boolean.getBoolean("vs2.productionSmoke") && !fixturePlayerChecked) {'''
if new_server_guard not in server:
    if old_server_guard not in server:
        raise SystemExit("Phase 87 could not find Gate D fixture normalization guard")
    server = server.replace(old_server_guard, new_server_guard, 1)

server_required = [
    'java.lang.Boolean.getBoolean("vs2.productionSmoke")',
    'GATE_D_FIXTURE_PLAYER_REPOSITIONED',
    'gravity_probe_y=-0.08',
]
server_missing = [token for token in server_required if token not in server]
if server_missing:
    raise SystemExit("Phase 87 lost server fixture isolation anchors: " + ", ".join(server_missing))
server_probe.write_text(server, encoding="utf-8")

print("Phase 87: production isolation plus bounded physical-support telemetry for strict carry diagnosis")
