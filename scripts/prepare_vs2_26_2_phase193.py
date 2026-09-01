#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #414 proved a six-tick stable Create-native contact/application interval on
# carriage 10 (ticks 52-57), while Phase185 still reported strict_support=false on every tick and
# therefore never started the disposable walk. Do not weaken the strict support requirement without
# knowing which support component disagrees. Expand only the existing readiness telemetry with the
# Phase81 vertical gap / simplified-collider source plus the other already-computed support inputs.
#
# Production-world #439 never reached the world because Phase185 added explicit
# balance_measurement_fresh/direct_native_fallback readiness fields and this diagnostic phase still
# matched the older logger shape. Retarget Phase193 to the current Phase185 contract while preserving
# those new fields. Read-only diagnostics only: no movement, carry, collision, train/world, inventory,
# or physics state is changed.
#
# Production-world #575 proved the Phase81 support snapshot can be stale within the same client tick:
# Phase81 reported vertical_gap=NaN/physical_support=false, while this later Phase185 boundary saw the
# current Create simplified collider with xz_inside_any=true and vertical_gap=0/0.0001. Preserve the
# exact Phase81 support semantics but refresh those existing local variables from the current collider
# state here, immediately before Phase194 consumes them. Fixture readiness only; no player motion,
# carry vector, collision response, train/world state, Create behavior, or VS2 physics is changed.
# Production-world #576 then proved the first implementation spliced statements into the argument
# list of LOGGER.info, producing an illegal-start-of-expression compile failure. Replace the complete
# LOGGER.info call so the refresh executes immediately before the logger rather than inside it.
old_log = '''                            LOGGER.info(
                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} phase134_fresh_native={} exact_native_application={} balance_measurement_fresh={} direct_native_fallback={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry, phase185NativeApplicationFresh,
                                phase185BalanceMeasurementFresh, phase185DirectNativeFallback, phase185FreshNativeEvidence);'''
new_log = '''                            if (simplifiedColliderState.contains(";xz_inside_any=true")) {
                                int phase193GapIndex = simplifiedColliderState.lastIndexOf(";vertical_gap=");
                                if (phase193GapIndex >= 0) {
                                    String phase193GapText = simplifiedColliderState.substring(phase193GapIndex + 14);
                                    try {
                                        phase81VerticalGap = Double.parseDouble(phase193GapText);
                                        phase81PhysicalSupport = Double.isFinite(phase81VerticalGap)
                                            && Math.abs(phase81VerticalGap) <= 0.05;
                                    } catch (NumberFormatException ignored) {
                                        phase81VerticalGap = Double.NaN;
                                        phase81PhysicalSupport = false;
                                    }
                                } else {
                                    phase81VerticalGap = Double.NaN;
                                    phase81PhysicalSupport = false;
                                }
                            } else {
                                phase81VerticalGap = Double.NaN;
                                phase81PhysicalSupport = false;
                            }
                            LOGGER.info(
                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} support_now={} strict_support={} vertical_gap={} collider_state={} on_ground={} collision_eligible={} broadphase_overlap={} phase134_fresh_native={} exact_native_application={} balance_measurement_fresh={} direct_native_fallback={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase154SupportNow, phase81PhysicalSupport, phase81VerticalGap, simplifiedColliderState,
                                player.onGround(), collisionEligible, broadphaseOverlap,
                                phase158FreshNativeCarry, phase185NativeApplicationFresh,
                                phase185BalanceMeasurementFresh, phase185DirectNativeFallback, phase185FreshNativeEvidence);'''
if new_log not in source:
    count = source.count(old_log)
    if count != 1:
        raise SystemExit(f"Phase 193 expected one complete current Phase185 readiness logger, found {count}")
    source = source.replace(old_log, new_log, 1)

required = [
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "support_now={}",
    "strict_support={}",
    "vertical_gap={}",
    "collider_state={}",
    "collision_eligible={}",
    "broadphase_overlap={}",
    "balance_measurement_fresh={}",
    "direct_native_fallback={}",
    "phase154SupportNow",
    "phase81PhysicalSupport",
    "phase81VerticalGap",
    "simplifiedColliderState",
    "phase185NativeApplicationFresh",
    "phase185BalanceMeasurementFresh",
    "phase185DirectNativeFallback",
    "phase193GapIndex",
    "phase193GapText",
    "Double.parseDouble(phase193GapText)",
    "Math.abs(phase81VerticalGap) <= 0.05",
    "xz_inside_any=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 193 lost strict-support readiness anchors: " + ", ".join(missing))

inserted = new_log
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 193 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 193: refreshes strict support before the complete Phase185 readiness logger; fixture accounting only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase194.py")), run_name="__main__")
