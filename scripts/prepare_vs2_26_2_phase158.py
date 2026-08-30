#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #278 proved the extended walk was contaminated by Phase85 compatibility
# replay immediately after supported sibling handoff. Production-world #280 then isolated that
# replay and exposed a second, independent fixture race: the walk started at tick 35 while the
# current carriage's native carry was not yet healthy; ticks 36-38 had player_delta=0 while the
# carriage moved ~1.074 blocks/tick, despite strict physical support. Native carry recovered
# exactly at ticks 39-40. Do not begin the movement proof merely because broadphase/onGround is
# true: require a fresh native-carry-health publication for the active carriage first. This is
# fixture gating only; production movement, collision, carry, train and VS2 physics are unchanged.
old = '''                                || phase150SupportReacquired))'''
new = '''                                || phase150SupportReacquired
                                || (productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished)))'''
if "productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished" not in source:
    if source.count(old) != 1:
        raise SystemExit("Phase 158 expected exactly one final Phase150 replay-suppression seam")
    source = source.replace(old, new, 1)

walk_start_old = '''                        if (!phase154WalkStarted && phase154SupportNow) {
                            phase154WalkStarted = true;'''
walk_start_new = '''                        boolean phase158FreshNativeCarry = Boolean.parseBoolean(System.getProperty(
                            "vs2.phase134NativeCarryHealthy." + phase154Carriage.getId(), "false"))
                            && (Integer.toString(player.tickCount).equals(System.getProperty(
                                    "vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId()))
                                || Integer.toString(player.tickCount - 1).equals(System.getProperty(
                                    "vs2.phase134NativeCarryHealthyTick." + phase154Carriage.getId())));
                        if (!phase154WalkStarted && phase154SupportNow && phase158FreshNativeCarry) {
                            LOGGER.info(
                                "GATE_E_PHASE158_WALK_NATIVE_READY player_tick={} carriage_id={} support_now=true native_carry_healthy=true fresh_sample=true fixture_only=true",
                                player.tickCount, phase154Carriage.getId());
                            phase154WalkStarted = true;'''
if "GATE_E_PHASE158_WALK_NATIVE_READY" not in source:
    if source.count(walk_start_old) != 1:
        raise SystemExit("Phase 158 expected exactly one Phase154 walk-start guard")
    source = source.replace(walk_start_old, walk_start_new, 1)

required = [
    "productionSmokeFixture && phase154WalkStarted && !phase154WalkFinished",
    "phase150SupportReacquired",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "phase154Step > 0.75",
    "GATE_E_PHASE158_WALK_NATIVE_READY",
    "phase158FreshNativeCarry",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "phase154SupportNow && phase158FreshNativeCarry",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 158 lost native-carry walk-isolation anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in new or forbidden in walk_start_new:
        raise SystemExit("Phase 158 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 158: isolates walk from compatibility replay and starts it only after fresh native Create carry is proven on the active carriage")
