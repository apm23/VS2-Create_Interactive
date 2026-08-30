#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #204 proved a concrete one-tick de-dup race: native Create carry was
# exact (drift_sq=0) on a supported carriage, then Phase85 replay ran on the immediately
# following tick before the next native-carry-health sample could settle, producing roughly
# 2x carriage motion. Preserve native Create carry authority for exactly one tick after a
# proven healthy interval. If native carry actually stops, replay becomes eligible again on
# the next tick. No new vector, clamp, teleport, collision, train, or VS2 physics behavior.
old_guard = '''!(productionSmoke && explicitCarryCompat && Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false")))'''
new_guard = '''!(productionSmoke && explicitCarryCompat && (
                                Boolean.parseBoolean(System.getProperty("vs2.phase134NativeCarryHealthy." + carriage.getId(), "false"))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()))))'''
if "vs2.phase134NativeCarryHealthyTick." not in source:
    if old_guard not in source:
        raise SystemExit("Phase 137 could not find adaptive native-carry replay suppression guard")
    source = source.replace(old_guard, new_guard, 1)

health_set = '''        System.setProperty(phase134HealthyKey, Boolean.toString(phase134NativeCarryHealthy));
'''
health_set_with_tick = health_set + '''        if (phase134NativeCarryHealthy) {
            System.setProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId(), Integer.toString(player.tickCount));
        }
'''
if 'System.setProperty("vs2.phase134NativeCarryHealthyTick." + carriage.getId()' not in source:
    if health_set not in source:
        raise SystemExit("Phase 137 could not find Phase134 health publication")
    source = source.replace(health_set, health_set_with_tick, 1)

required = [
    "vs2.phase134NativeCarryHealthyTick.",
    "Integer.toString(player.tickCount - 1).equals",
    "if (phase134NativeCarryHealthy)",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE134_ACTIVE_SUPPORT_CARRY_BALANCE",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 137 lost native-carry de-dup anchors: " + ", ".join(missing))

# This phase only narrows when the already-existing replay is allowed to execute.
for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in new_guard or forbidden in health_set_with_tick:
        raise SystemExit("Phase 137 found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 137: suppresses compatibility replay for one tick after proven exact native Create carry, preventing double-carry race")
