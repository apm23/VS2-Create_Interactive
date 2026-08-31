#!/usr/bin/env python3
from pathlib import Path
import runpy

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
#
# Production-world #385 then proved phase134's health publication can be absent even while Create's
# real ContraptionColliderClient applies non-zero contact motion on the exact active carriage every
# tick: carriage 10 had strict support through ticks 51-75 and Phase170 native applications through
# ticks 51-73, yet phase158FreshNativeCarry stayed false because the phase134 health property was
# missing. For fixture readiness only, accept that exact same-tick, same-carriage Phase170 application
# as fresh native evidence. This does not synthesize/replay motion; it only lets the existing walk
# fixture start after three consecutive ticks of directly observed native Create application.

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
    settled = '''                        boolean phase185NativeApplicationFresh = Integer.toString(player.tickCount).equals(
                            System.getProperty("vs2.phase170NativeContactApplicationTick"))
                            && Integer.toString(phase154Carriage.getId()).equals(System.getProperty(
                                "vs2.phase170NativeContactApplicationCarriageId"));
                        boolean phase185FreshNativeEvidence = phase158FreshNativeCarry || phase185NativeApplicationFresh;
                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
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
                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} phase134_fresh_native={} exact_native_application={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry, phase185NativeApplicationFresh, phase185FreshNativeEvidence);
                        }
                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && phase185WalkReadyTicks >= 3) {'''
    source = source.replace(walk_gate, settled, 1)
else:
    old_ready = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase158FreshNativeCarry
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
    new_ready = '''                        boolean phase185NativeApplicationFresh = Integer.toString(player.tickCount).equals(
                            System.getProperty("vs2.phase170NativeContactApplicationTick"))
                            && Integer.toString(phase154Carriage.getId()).equals(System.getProperty(
                                "vs2.phase170NativeContactApplicationCarriageId"));
                        boolean phase185FreshNativeEvidence = phase158FreshNativeCarry || phase185NativeApplicationFresh;
                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
    if "phase185FreshNativeEvidence" not in source:
        if source.count(old_ready) != 1:
            raise SystemExit("Phase 185 could not upgrade settled walk readiness to exact native application evidence")
        source = source.replace(old_ready, new_ready, 1)
        old_log = '''                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} fresh_native_carry={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry);'''
        new_log = '''                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} phase134_fresh_native={} exact_native_application={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry, phase185NativeApplicationFresh, phase185FreshNativeEvidence);'''
        if source.count(old_log) != 1:
            raise SystemExit("Phase 185 could not upgrade settled walk readiness telemetry")
        source = source.replace(old_log, new_log, 1)

required = [
    "phase185WalkReadyCarriageId",
    "phase185WalkReadyTicks",
    "phase185WalkReadyNow",
    "phase185NativeApplicationFresh",
    "phase185FreshNativeEvidence",
    "phase154SupportNow",
    "phase81PhysicalSupport",
    "phase158FreshNativeCarry",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "player.tickCount - carryBaselineRebaseTick >= 2",
    "phase185WalkReadyTicks >= 3",
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "exact_native_application={}",
    "fresh_native_evidence={}",
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
print("Phase 185: delays fixture walk until three consecutive settled active-carriage support/native-carry ticks; exact same-carriage Phase170 application is valid fresh native evidence; accounting only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase186.py")), run_name="__main__")
