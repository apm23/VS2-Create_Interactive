#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #374 proved the bounded walk can start while the active Create carriage frame is
# still oscillating between sibling carriage entities. Delay only the disposable fixture's forward
# key pulse until the same active carriage has satisfied strict support plus fresh native evidence for
# two consecutive ticks, with no recent baseline rebase.
#
# Production-world #385 proved phase134 health publication can be absent even while the exact active
# carriage receives genuine Create native contact every tick. Keep a fallback to same-tick per-carriage
# Phase170 evidence, but only when there is no same-tick Phase161/Phase134 balance measurement.
#
# Production-world #437 proved a sibling native application can arrive on the third readiness tick
# before the walk-active Phase172 property exists. Pre-arm only that existing disposable sibling
# de-dup guard after two settled ticks.
#
# Production-world #438 then exposed the important distinction between "health sample missing" and
# "health sample measured bad": carriage 10 had a same-tick Phase170 application at tick 19, but the
# authoritative balance measurement reported player=(-8.309,0,-2), carriage=(+1.691,0,0), drift^2=104.
# The old fallback treated that explicitly bad sample as fresh merely because Phase170 ran. Reject the
# fallback whenever a current Phase161 balance measurement exists; phase158 remains authoritative for
# measured samples, while the direct Phase170 fallback is reserved strictly for the #385 missing-sample
# case. This is fixture readiness/accounting only: no position, velocity, carry vector, collision,
# train, world, inventory, or VS2/Create physics state is changed.
#
# Phase192 owns the final cumulative two-frame direct-native readiness rewrite. Keep this script's
# historical three-tick composition seam so the downstream cumulative rewrite can target it without
# weakening or changing the generated final runtime predicate.

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
                            System.getProperty("vs2.phase170NativeContactApplicationTick." + phase154Carriage.getId()));
                        boolean phase185BalanceMeasurementFresh = Integer.toString(player.tickCount).equals(
                            System.getProperty("vs2.phase161MeasurementTick." + phase154Carriage.getId()));
                        boolean phase185DirectNativeFallback = phase185NativeApplicationFresh
                            && !phase185BalanceMeasurementFresh;
                        boolean phase185FreshNativeEvidence = phase158FreshNativeCarry || phase185DirectNativeFallback;
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
                            if (phase185WalkReadyNow
                                    && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                    && phase185WalkReadyTicks >= 2) {
                                System.setProperty("vs2.phase172WalkActiveCarriageId", Integer.toString(phase154Carriage.getId()));
                                LOGGER.info(
                                    "GATE_E_PHASE185_SIBLING_GUARD_PREARM player_tick={} carriage_id={} ready_ticks={} fixture_only=true existing_guard_only=true",
                                    player.tickCount, phase154Carriage.getId(), phase185WalkReadyTicks);
                            } else if (!phase185WalkReadyNow) {
                                System.clearProperty("vs2.phase172WalkActiveCarriageId");
                            }
                            LOGGER.info(
                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} phase134_fresh_native={} exact_native_application={} balance_measurement_fresh={} direct_native_fallback={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry, phase185NativeApplicationFresh,
                                phase185BalanceMeasurementFresh, phase185DirectNativeFallback, phase185FreshNativeEvidence);
                        }
                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && phase185WalkReadyTicks >= 3) {'''
    source = source.replace(walk_gate, settled, 1)

required = [
    "phase185WalkReadyCarriageId",
    "phase185WalkReadyTicks",
    "phase185WalkReadyNow",
    "phase185NativeApplicationFresh",
    "phase185BalanceMeasurementFresh",
    "phase185DirectNativeFallback",
    "phase185FreshNativeEvidence",
    "phase154SupportNow",
    "phase81PhysicalSupport",
    "phase158FreshNativeCarry",
    "vs2.phase170NativeContactApplicationTick.",
    "vs2.phase161MeasurementTick.",
    "&& !phase185BalanceMeasurementFresh",
    "player.tickCount - carryBaselineRebaseTick >= 2",
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "GATE_E_PHASE185_SIBLING_GUARD_PREARM",
    "vs2.phase172WalkActiveCarriageId",
    "phase185WalkReadyTicks >= 2",
    "phase185WalkReadyTicks >= 3",
    "balance_measurement_fresh={}",
    "direct_native_fallback={}",
    "fresh_native_evidence={}",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 185 lost settled walk-start anchors: " + ", ".join(missing))

# Phase185 may change only fixture key-readiness accounting and the pre-existing Phase172 guard
# selector property. It must not directly mutate gameplay/physics state.
inserted = source[source.find("boolean phase185NativeApplicationFresh"):source.find("boolean phase185NativeApplicationFresh") + 7000]
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 185 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 185: preserves downstream two-frame direct-native composition seam while prearming sibling guard after two settled frames")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase186.py")), run_name="__main__")
