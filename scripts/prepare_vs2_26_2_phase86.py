#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase 85 proved the compatibility carry itself, but GateEClientProbe also contains
# CI-only fixture normalization/repositioning used to make the archived smoke save
# deterministic. Before exposing the carry path to a normal client, separate those
# concerns: production may explicitly opt into carry compatibility while every
# fixture reposition/gravity probe remains strictly CI-harness-only.
old_enable = '''        boolean enabled = Boolean.getBoolean("vs2.gateD") || "true".equals(System.getenv("GITHUB_ACTIONS"));
        if (!enabled || installed) return;
        installed = true;
'''
new_enable = '''        boolean ciHarness = Boolean.getBoolean("vs2.gateD") || "true".equals(System.getenv("GITHUB_ACTIONS"));
        boolean explicitCarryCompat = Boolean.getBoolean("vs2.createCarryCompat");
        boolean enabled = ciHarness || explicitCarryCompat;
        if (!enabled || installed) return;
        installed = true;
        LOGGER.info("VS2_CREATE_CARRY_COMPAT_MODE ci_harness={} explicit_opt_in={}", ciHarness, explicitCarryCompat);
'''
if "VS2_CREATE_CARRY_COMPAT_MODE" not in source:
    if old_enable not in source:
        raise SystemExit("Phase 86 could not find static Gate E install guard")
    source = source.replace(old_enable, new_enable, 1)

# Phase 61: archived-save LocalPlayer block-top normalization.
old_fixture_block = '''            if (!fixtureClientNormalized && !carriageCandidates.isEmpty()) {'''
new_fixture_block = '''            if (ciHarness && !fixtureClientNormalized && !carriageCandidates.isEmpty()) {'''
if new_fixture_block not in source:
    if old_fixture_block not in source:
        raise SystemExit("Phase 86 could not find Phase 61 fixture normalization guard")
    source = source.replace(old_fixture_block, new_fixture_block, 1)

# Phase 67/68/70: simplified-collider alignment and one-shot gravity probe.
old_collider_fixture = '''            if (!fixtureColliderNormalized) {'''
new_collider_fixture = '''            if (ciHarness && !fixtureColliderNormalized) {'''
if new_collider_fixture not in source:
    if old_collider_fixture not in source:
        raise SystemExit("Phase 86 could not find Phase 67 collider fixture guard")
    source = source.replace(old_collider_fixture, new_collider_fixture, 1)

# The only LocalPlayer movement available outside ciHarness is now the strict
# Phase 85 path: Create-computed contact motion, filtered through Create's own
# ContraptionCollider.collide(), horizontal-only, and physical-support guarded.
required = [
    "GATE_E_PHASE85_CARRY_REPLAY",
    "phase81PhysicalSupport",
    "ContraptionCollider",
    "carryReplayPlayerTick",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 86 lost required carry safety anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 86: isolated CI fixture reposition/gravity probes from opt-in production Create-filtered carry compatibility")

# Keep the world-smoke preparation chain moving into the production-mode isolation
# check. Phase 87 is still non-destructive: it only changes how the harness flag is
# selected so GitHub Actions can later run with ci_harness=false explicitly.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase87.py")), run_name="__main__")
