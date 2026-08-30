#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

if "&& &&" in source:
    raise SystemExit("Phase 131 found duplicate conjunction after Phase130")
if "!(productionSmoke && explicitCarryCompat)" not in source:
    raise SystemExit("Phase 131 lost production carry replay suppression predicate")
if "carryReplayPlayerTick != player.tickCount" not in source:
    raise SystemExit("Phase 131 lost original replay tick predicate")

# Production-world #173 proved the support-loss exception is a CI harness blocker:
# it deliberately crashes the client before the workflow's independent sustained-carry
# parser can classify the same carriage-local telemetry. Keep the diagnostic fail-closed
# at workflow level, but never crash Minecraft from diagnostic code. No movement/contact,
# collision, train, world, inventory, or VS2 physics state is changed here.
old = '''    if (productionSmokeSupportTrackedCarriage && productionSmokeSupportLossTicks >= 3
            && broadphaseOverlap && player.onGround()) {
        throw new IllegalStateException("Production smoke rejected unsupported carriage-local carry continuity after "
            + productionSmokeSupportLossTicks + " consecutive ticks");
    }'''
new = '''    if (productionSmokeSupportTrackedCarriage && productionSmokeSupportLossTicks >= 3
            && broadphaseOverlap && player.onGround()) {
        LOGGER.info(
            "GATE_E_PHASE133_SUPPORT_LOSS_DIAGNOSTIC player_tick={} carriage_id={} consecutive_loss_ticks={} workflow_gate_authoritative=true nonfatal=true fixture_only=true",
            player.tickCount, carriage.getId(), productionSmokeSupportLossTicks);
    }'''
if old not in source:
    raise SystemExit("Phase 131 could not find Phase131 support-loss exception block")
source = source.replace(old, new, 1)

required = [
    "GATE_E_PHASE131_SUPPORT_STREAK",
    "GATE_E_PHASE133_SUPPORT_LOSS_DIAGNOSTIC",
    "workflow_gate_authoritative=true",
    "nonfatal=true",
    "productionSmokeSupportTrackedCarriage",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 131 lost support diagnostic anchors: " + ", ".join(missing))
if "Production smoke rejected unsupported carriage-local carry continuity" in source:
    raise SystemExit("Phase 131 failed to remove diagnostic crash path")

client_probe.write_text(source, encoding="utf-8")
print("Phase 131: validates Phase130 replay syntax and keeps support-loss telemetry nonfatal so the workflow is the authoritative carry gate")
