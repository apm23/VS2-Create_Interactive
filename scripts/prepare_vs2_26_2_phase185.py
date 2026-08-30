#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #374 proved the bounded walk can start while the active Create carriage frame is
# still oscillating between sibling carriage entities: the fixture started on carriage 5 at tick 15,
# then observed 5 -> 7 -> 5 -> 7 before any stable walk interval existed. That makes later local-step
# failures ambiguous and can mark support unhealthy before the locomotion hypothesis is actually tested.
# Delay only the disposable fixture's forward-key pulse until the same active carriage has satisfied
# the existing strict-support + fresh-native-carry start predicate for three consecutive ticks, with no
# recent baseline rebase. No player position/velocity, collision, carry vector, train/world state, or
# VS2/Create physics behavior is changed.

field_anchor = "    private static boolean phase154WalkStarted;\n"
field_insert = field_anchor + (
    "    private static int phase185WalkReadyCarriageId = -1;\n"
    "    private static int phase185WalkReadyTicks = 0;\n"
)
if "phase185WalkReadyTicks" not in source:
    if source.count(field_anchor) != 1:
        raise SystemExit("Phase 185 could not locate unique Phase154 walk-start field")
    source = source.replace(field_anchor, field_insert, 1)

walk_gate = "                        if (!phase154WalkStarted && phase154SupportNow && phase81PhysicalSupport && phase158FreshNativeCarry) {"
if "GATE_E_PHASE185_SETTLED_WALK_READY" not in source:
    if source.count(walk_gate) != 1:
        raise SystemExit("Phase 185 expected exactly one cumulative walk-start predicate")
    settled = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase158FreshNativeCarry
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);
                        if (!phase154WalkStarted) {
                            if (phase185WalkReadyNow) {
                                if (phase185WalkReadyCarriageId == phase154Carriage.getId()) {
                                    phase185WalkReadyTicks++;
                                } else {
                                    phase185WalkReadyCarriageId = phase154Carriage.getId();
                                    phase185WalkReadyTicks = 1;
                                }
                            } else {
                                phase185WalkReadyCarriageId = -1;
                                phase185WalkReadyTicks = 0;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} fresh_native_carry={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry);
                        }
                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && phase185WalkReadyTicks >= 3) {'''
    source = source.replace(walk_gate, settled, 1)

required = [
    "phase185WalkReadyCarriageId",
    "phase185WalkReadyTicks",
    "phase185WalkReadyNow",
    "phase154SupportNow",
    "phase81PhysicalSupport",
    "phase158FreshNativeCarry",
    "player.tickCount - carryBaselineRebaseTick >= 2",
    "phase185WalkReadyTicks >= 3",
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 185 lost settled walk-start anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in settled if 'settled' in locals() else False:
        raise SystemExit("Phase 185 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 185: delays fixture walk until three consecutive settled active-carriage support/native-carry ticks; accounting only")
