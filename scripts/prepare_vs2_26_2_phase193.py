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
# Read-only diagnostics only: no movement, carry, collision, train/world, inventory, or physics state
# is changed.
old_log = '''                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} strict_support={} phase134_fresh_native={} exact_native_application={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase81PhysicalSupport, phase158FreshNativeCarry, phase185NativeApplicationFresh, phase185FreshNativeEvidence);'''
new_log = '''                                "GATE_E_PHASE185_SETTLED_WALK_READY player_tick={} carriage_id={} ready_now={} ready_ticks={} baseline_rebase_age={} support_now={} strict_support={} vertical_gap={} collider_state={} on_ground={} collision_eligible={} broadphase_overlap={} phase134_fresh_native={} exact_native_application={} fresh_native_evidence={} fixture_only=true accounting_only=true",
                                player.tickCount, phase154Carriage.getId(), phase185WalkReadyNow, phase185WalkReadyTicks,
                                carryBaselineRebaseTick == Integer.MIN_VALUE ? -1 : player.tickCount - carryBaselineRebaseTick,
                                phase154SupportNow, phase81PhysicalSupport, phase81VerticalGap, simplifiedColliderState,
                                player.onGround(), collisionEligible, broadphaseOverlap,
                                phase158FreshNativeCarry, phase185NativeApplicationFresh, phase185FreshNativeEvidence);'''
if new_log not in source:
    count = source.count(old_log)
    if count != 1:
        raise SystemExit(f"Phase 193 expected one Phase185 readiness logger, found {count}")
    source = source.replace(old_log, new_log, 1)

required = [
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "support_now={}",
    "strict_support={}",
    "vertical_gap={}",
    "collider_state={}",
    "collision_eligible={}",
    "broadphase_overlap={}",
    "phase154SupportNow",
    "phase81PhysicalSupport",
    "phase81VerticalGap",
    "simplifiedColliderState",
    "phase185NativeApplicationFresh",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 193 lost strict-support diagnostic anchors: " + ", ".join(missing))

inserted = new_log
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 193 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 193: traces strict-support components during exact native walk readiness; read-only only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase194.py")), run_name="__main__")
