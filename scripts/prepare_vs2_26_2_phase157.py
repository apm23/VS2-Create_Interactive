#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #274 proved native Create carry is exact before normal player locomotion:
# carriage 2 ticks 34-39 report native_carry_healthy=true. Once forward input contributes
# legitimate player-relative displacement, the old drift-only classifier flips health false;
# after strict support reacquires at tick 46 this stale false classification enables Phase85
# replay at ticks 47-48, adding the train's ~2-block motion a second time and causing the exact
# carriage-local jumps that fail the walk proof. A drift metric cannot distinguish intentional
# locomotion from missing carriage carry. Preserve an already-proven healthy state only while
# a normal horizontal movement key is actively held and strict health sampling continues.
# As soon as locomotion stops, the existing drift classifier is authoritative again. This adds
# no carry vector, teleport, collision/world/train mutation, or VS2 physics change; it only
# prevents the compatibility replay selector from misclassifying intentional player motion.
old = '''boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && phase134DriftSq <= 0.01 && player.onGround();'''
new = '''boolean phase157PlayerLocomoting = client.options.keyUp.isDown()
            || client.options.keyDown.isDown()
            || client.options.keyLeft.isDown()
            || client.options.keyRight.isDown();
        boolean phase157PreviouslyHealthy = Boolean.parseBoolean(System.getProperty(phase134HealthyKey, "false"));
        boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && player.onGround()
            && (phase134DriftSq <= 0.01 || (phase157PlayerLocomoting && phase157PreviouslyHealthy));
        if (phase157PlayerLocomoting && phase157PreviouslyHealthy && phase134DriftSq > 0.01) {
            LOGGER.info(
                "GATE_E_PHASE157_LOCOMOTION_HEALTH_HOLD player_tick={} carriage_id={} drift_sq={} previous_healthy=true locomoting=true replay_suppression_preserved=true read_only_accounting=true",
                player.tickCount, carriage.getId(), phase134DriftSq);
        }'''
if "GATE_E_PHASE157_LOCOMOTION_HEALTH_HOLD" not in source:
    if old not in source:
        raise SystemExit("Phase 157 could not find Phase137 native-carry health predicate")
    source = source.replace(old, new, 1)

required = [
    "GATE_E_PHASE157_LOCOMOTION_HEALTH_HOLD",
    "phase157PlayerLocomoting",
    "client.options.keyUp.isDown()",
    "client.options.keyDown.isDown()",
    "client.options.keyLeft.isDown()",
    "client.options.keyRight.isDown()",
    "phase157PreviouslyHealthy",
    "Boolean.parseBoolean(System.getProperty(phase134HealthyKey, \"false\"))",
    "phase134DriftSq <= 0.01 || (phase157PlayerLocomoting && phase157PreviouslyHealthy)",
    "GATE_E_PHASE134_ACTIVE_SUPPORT_CARRY_BALANCE",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 157 lost locomotion-aware native health anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in new:
        raise SystemExit("Phase 157 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 157: preserves already-proven native carry health during explicit horizontal locomotion so intentional walking cannot enable duplicate compatibility replay")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase158.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase161.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase162.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase163.py")), run_name="__main__")
