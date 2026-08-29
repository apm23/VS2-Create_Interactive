#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase 86 separated fixture behavior from the carry compatibility path, but its
# ciHarness switch still implicitly treated every GitHub Actions JVM as a fixture
# run. Make the harness opt-in via the existing vs2.gateD property so CI can also
# execute a genuine production-mode client with ci_harness=false.
old = '''        boolean ciHarness = Boolean.getBoolean("vs2.gateD") || "true".equals(System.getenv("GITHUB_ACTIONS"));'''
new = '''        boolean ciHarness = Boolean.getBoolean("vs2.gateD");'''
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
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 87 lost production/harness isolation anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 87: made Gate E CI harness explicit so GitHub Actions can exercise true production carry mode")
