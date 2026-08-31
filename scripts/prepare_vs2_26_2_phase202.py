#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = contact_trace.read_text(encoding="utf-8")

# Production-world #457 proves native carry, interaction dispatch, and authoritative new-cell
# replication, but the bounded walk never starts: Phase194 arms carriage 4 on player tick 23 after
# two strict/native-supported ticks, then tick 24 loses baseline support while sibling carriage 2
# reports a large frame/contact-motion discontinuity. Do not widen replay or relax acceptance yet.
# Correlate the already-read-only Phase171 carriage frame/contact values with the one-tick Phase194
# pending-confirmation window so the next real-world run can distinguish a Create transform handoff
# from a missing carry application without changing movement, collision, train, world, or VS2 physics.

anchor = '''            LOGGER.info(\n                "GATE_E_PHASE171_CARRIAGE_FRAME_STEP player_tick={} carriage_id={} previous_player_tick={} frame_step={} contact_motion={} motion_minus_frame_step={} carriage_pos={} read_only=true diagnostic_state_only=true",\n                phase170Player.tickCount, self.getId(), phase171PreviousPlayerTick,\n                phase171FrameStep, motion, phase171MotionResidual, phase171Position);\n'''
insert = anchor + '''            String phase202PendingTickRaw = System.getProperty("vs2.phase194PendingWalkTick");\n            String phase202PendingCarriageRaw = System.getProperty("vs2.phase194PendingWalkCarriageId");\n            if (Boolean.getBoolean("vs2.productionSmokeFixture")\n                    && phase202PendingTickRaw != null && phase202PendingCarriageRaw != null) {\n                try {\n                    int phase202PendingTick = Integer.parseInt(phase202PendingTickRaw);\n                    int phase202PendingCarriage = Integer.parseInt(phase202PendingCarriageRaw);\n                    if (phase170Player.tickCount == phase202PendingTick + 1) {\n                        boolean phase202NativeApplied = Integer.toString(phase170Player.tickCount).equals(\n                            System.getProperty("vs2.phase170NativeContactApplicationTick." + self.getId()));\n                        LOGGER.info(\n                            "GATE_E_PHASE202_PENDING_CONFIRM_CONTACT player_tick={} carriage_id={} pending_carriage_id={} pending_tick={} is_pending_carriage={} frame_step={} contact_motion={} motion_minus_frame_step={} native_applied_this_tick={} carriage_pos={} fixture_only=true read_only=true diagnostic_state_only=true",\n                            phase170Player.tickCount, self.getId(), phase202PendingCarriage, phase202PendingTick,\n                            self.getId() == phase202PendingCarriage, phase171FrameStep, motion, phase171MotionResidual,\n                            phase202NativeApplied, phase171Position);\n                    }\n                } catch (NumberFormatException ignored) {\n                }\n            }\n'''

if "GATE_E_PHASE202_PENDING_CONFIRM_CONTACT" not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Phase 202 expected one Phase171 carriage-frame log anchor")
    source = source.replace(anchor, insert, 1)

required = [
    "GATE_E_PHASE202_PENDING_CONFIRM_CONTACT",
    "vs2.phase194PendingWalkTick",
    "vs2.phase194PendingWalkCarriageId",
    "phase202PendingTick + 1",
    "vs2.phase170NativeContactApplicationTick.",
    "is_pending_carriage={}",
    "motion_minus_frame_step={}",
    "fixture_only=true read_only=true diagnostic_state_only=true",
    "GATE_E_PHASE171_CARRIAGE_FRAME_STEP",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 202 lost pending-confirmation telemetry anchors: " + ", ".join(missing))

for forbidden in [
    "setPos(", "setDeltaMovement(", ".move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in insert:
        raise SystemExit("Phase 202 introduced forbidden gameplay mutation: " + forbidden)

contact_trace.write_text(source, encoding="utf-8")
print("Phase 202: correlates Phase194 pre-walk confirmation with Create carriage frame/contact discontinuity; read-only only")
