#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #278 proved the extended walk is contaminated by Phase85 compatibility
# replay immediately after supported sibling handoff: the replay starts before the rebased
# carriage has a fresh native-carry health sample, and the resulting carriage-local step
# exceeds the strict 0.75-block walk guard. Isolate the disposable Phase154 walk fixture from
# compatibility replay so the next real-world smoke measures Create's native carry while
# normal forward input is active. This is fixture-only diagnostic isolation: production
# behavior outside productionSmokeFixture is unchanged, all existing walk drift/support gates
# remain strict, and no movement/vector/world/train/physics mutation is introduced here.
old = '''                                || phase150SupportReacquired))'''
new = '''                                || phase150SupportReacquired
                                || (productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished)))'''
if "productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished" not in source:
    if source.count(old) != 1:
        raise SystemExit("Phase 158 expected exactly one final Phase150 replay-suppression seam")
    source = source.replace(old, new, 1)

required = [
    "productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished",
    "phase150SupportReacquired",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "phase154Step > 0.75",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 158 lost native-carry walk-isolation anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in new:
        raise SystemExit("Phase 158 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 158: suppresses compatibility carry replay only during the disposable 20-tick walk fixture so native Create carry is measured without replay contamination")
