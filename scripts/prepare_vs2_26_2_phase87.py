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

print("Phase 87: added true GitHub production-smoke isolation for both LocalPlayer and ServerPlayer fixture mutations")
