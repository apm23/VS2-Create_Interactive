#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #302 pinned the walk measurement to one carriage and exposed the real
# remaining false-positive: at tick 40 the player still carried 1.946 blocks while the carriage
# moved 1.986 blocks, but Phase161 treated the tiny 0.040-block along-motion deficit caused by
# intentional walking as a full native-carry loss and replayed another 1.986 blocks. Require a
# material loss of carriage-projected motion before compatibility replay can bypass native
# de-dup. This changes only recovery eligibility; the existing Create-computed/collision-filtered
# Phase85 vector remains authoritative and no player/train/world/VS2 physics mutation is added.
old = "phase161NativeCarryProjection < phase161CarriageMotionSq - 0.01"
new = "phase161NativeCarryProjection < phase161CarriageMotionSq * 0.75"
if new not in source:
    if source.count(old) != 1:
        raise SystemExit("Phase 164 expected exactly one Phase161 under-carry threshold")
    source = source.replace(old, new, 1)

required = [
    "GATE_E_PHASE161_LOCOMOTION_NATIVE_LOSS_CLASSIFICATION",
    "GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY",
    "phase161CarriageMotionSq > 1.0E-8",
    "phase161NativeCarryProjection < phase161CarriageMotionSq * 0.75",
    "phase161MeasuredUndercarry",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 164 lost material under-carry recovery anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in new:
        raise SystemExit("Phase 164 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 164: requires material carriage-projected under-carry before locomotion recovery replay")
