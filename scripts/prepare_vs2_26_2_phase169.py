#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world on deb938bc proved a harness-ordering deadlock: strict support plus fresh
# native carry were healthy before the authoritative new-cell replication flag became true;
# after that flag became true, those movement prerequisites no longer overlapped. The walk
# fixture therefore never started even though carry and packet-authoritative placement were
# independently proven. Movement validation must precede interaction/placement readiness.
# Decouple only the disposable walk probe's outer scheduling gate from placement readiness;
# Phase158 still requires strict physical support and fresh native carry before any key pulse.
# No player position/velocity, collision response, train/world state, or VS2/Create physics is
# changed by this patch.
old = '''            if (productionSmokeFixture
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementExactCellPresent")
                    && !phase154WalkFinished) {'''
new = '''            if (productionSmokeFixture
                    && !phase154WalkFinished) {'''
if "GATE_E_PHASE169_WALK_BEFORE_PLACEMENT" not in source:
    if source.count(old) != 1:
        raise SystemExit("Phase 169 expected exactly one Phase154 placement-coupled walk gate")
    source = source.replace(old, new, 1)

    start_anchor = '''                            LOGGER.info(
                                "GATE_E_PHASE158_WALK_NATIVE_READY'''
    start_insert = '''                            LOGGER.info(
                                "GATE_E_PHASE169_WALK_BEFORE_PLACEMENT player_tick={} carriage_id={} exact_cell_present={} strict_support=true fresh_native_carry=true fixture_only=true",
                                player.tickCount, phase154Carriage.getId(),
                                java.lang.Boolean.getBoolean("vs2.productionNativePlacementExactCellPresent"));
                            LOGGER.info(
                                "GATE_E_PHASE158_WALK_NATIVE_READY'''
    if source.count(start_anchor) != 1:
        raise SystemExit("Phase 169 expected exactly one Phase158 walk-ready anchor")
    source = source.replace(start_anchor, start_insert, 1)

required = [
    "GATE_E_PHASE169_WALK_BEFORE_PLACEMENT",
    "if (productionSmokeFixture\n                    && !phase154WalkFinished)",
    "phase154SupportNow && phase81PhysicalSupport && phase158FreshNativeCarry",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "vs2.productionNativePlacementExactCellPresent",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 169 lost movement-first harness anchors: " + ", ".join(missing))

patch_text = new + start_insert
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in patch_text:
        raise SystemExit("Phase 169 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 169: decouples bounded walk start from placement readiness while preserving strict support plus fresh native carry")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase170.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase171.py")), run_name="__main__")
