#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #332 proved the duplicate-sibling native-carry hypothesis removed the immediate
# 6-9 block first-frame launch. The remaining failure is different: the active carriage stays in
# broadphase and LocalPlayer remains onGround, while local Y rises by ~0.1/tick and the historical
# walk support latch turns false before later horizontal drift. Do not change support thresholds or
# physics yet. Record the exact ingredients that Phase154 uses when the latch transitions so the
# next real-world run can distinguish active-carriage identity loss from broadphase/onGround/contact
# accounting. Read-only telemetry only.

anchor = '''                        boolean phase154SupportNow = phase154Broadphase && player.onGround()
                            && phase154Carriage.getId() == carryBaselineCarriageId;
'''
replacement = anchor + '''                        if (phase154WalkStarted || phase154SupportNow) {
                            LOGGER.info(
                                "GATE_E_PHASE173_WALK_SUPPORT_REASON player_tick={} carriage_id={} baseline_carriage_id={} walk_carriage_id={} local={} broadphase={} on_ground={} id_matches_baseline={} support_now={} support_latched={} native_tick={} native_carriage_id={} read_only=true",
                                player.tickCount, phase154Carriage.getId(), carryBaselineCarriageId, phase154WalkCarriageId,
                                phase154Local, phase154Broadphase, player.onGround(),
                                phase154Carriage.getId() == carryBaselineCarriageId, phase154SupportNow, phase154WalkSupportHealthy,
                                System.getProperty("vs2.phase170NativeContactApplicationTick"),
                                System.getProperty("vs2.phase170NativeContactApplicationCarriageId"));
                        }
'''
inserted = ""
if "GATE_E_PHASE173_WALK_SUPPORT_REASON" not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Phase 173 expected exactly one Phase154 support predicate")
    source = source.replace(anchor, replacement, 1)
    inserted = replacement

required = [
    "GATE_E_PHASE173_WALK_SUPPORT_REASON",
    "phase154SupportNow",
    "phase154WalkSupportHealthy",
    "carryBaselineCarriageId",
    "phase154WalkCarriageId",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 173 lost walk-support reason anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 173 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 173: traces exact bounded-walk support-latch inputs after duplicate sibling carry suppression; read-only only")
