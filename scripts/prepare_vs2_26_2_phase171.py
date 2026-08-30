#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = contact_trace.read_text(encoding="utf-8")

# Production-world #325 proves the previous double-carry edge is gone, but the bounded walk starts
# immediately before a different failure: carriage 5 contactPointMotion changes to exactly
# -40.3417956829 blocks while the player's carriage-local coordinate jumps +40.3417956829 blocks.
# The player itself has no matching horizontal delta and Phase170 reports no native application on
# that failed tick. Trace the carriage entity's own frame-to-frame position step beside Create's
# contact motion so the next real-world run can distinguish a carriage transform discontinuity
# from a missing player carry application. Diagnostic state only; no movement/physics mutation.

field_anchor = '''    private static int calls;\n'''
field_insert = '''    private static int calls;\n    private static final java.util.Map<Integer, net.minecraft.world.phys.Vec3> PHASE171_LAST_POSITION = new java.util.concurrent.ConcurrentHashMap<>();\n    private static final java.util.Map<Integer, Integer> PHASE171_LAST_PLAYER_TICK = new java.util.concurrent.ConcurrentHashMap<>();\n'''
if "PHASE171_LAST_POSITION" not in source:
    if source.count(field_anchor) != 1:
        raise SystemExit("Phase 171 expected exactly one contact trace counter anchor")
    source = source.replace(field_anchor, field_insert, 1)

log_anchor = '''        LOGGER.info(\n            "GATE_E_PHASE168_CONTACT_OWNER'''
log_insert = '''        net.minecraft.world.phys.Vec3 phase171Position = self.position();
        net.minecraft.world.phys.Vec3 phase171PreviousPosition = PHASE171_LAST_POSITION.put(self.getId(), phase171Position);
        Integer phase171PreviousPlayerTick = phase170Player == null ? null
            : PHASE171_LAST_PLAYER_TICK.put(self.getId(), phase170Player.tickCount);
        if (phase170Player != null && phase171PreviousPosition != null) {
            net.minecraft.world.phys.Vec3 phase171FrameStep = phase171Position.subtract(phase171PreviousPosition);
            net.minecraft.world.phys.Vec3 phase171MotionResidual = motion.subtract(phase171FrameStep);
            LOGGER.info(
                "GATE_E_PHASE171_CARRIAGE_FRAME_STEP player_tick={} carriage_id={} previous_player_tick={} frame_step={} contact_motion={} motion_minus_frame_step={} carriage_pos={} read_only=true diagnostic_state_only=true",
                phase170Player.tickCount, self.getId(), phase171PreviousPlayerTick,
                phase171FrameStep, motion, phase171MotionResidual, phase171Position);
        }
        LOGGER.info(
            "GATE_E_PHASE168_CONTACT_OWNER'''
if "GATE_E_PHASE171_CARRIAGE_FRAME_STEP" not in source:
    if source.count(log_anchor) != 1:
        raise SystemExit("Phase 171 expected exactly one Phase168 contact-owner log anchor")
    source = source.replace(log_anchor, log_insert, 1)

required = [
    "PHASE171_LAST_POSITION",
    "PHASE171_LAST_PLAYER_TICK",
    "GATE_E_PHASE171_CARRIAGE_FRAME_STEP",
    "phase171FrameStep",
    "motion.subtract(phase171FrameStep)",
    "diagnostic_state_only=true",
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
    "GATE_E_PHASE168_CONTACT_OWNER",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 171 lost carriage-frame telemetry anchors: " + ", ".join(missing))

inserted = field_insert + log_insert
for forbidden in [
    "setPos(", "setDeltaMovement(", ".move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 171 introduced forbidden gameplay mutation: " + forbidden)

contact_trace.write_text(source, encoding="utf-8")
print("Phase 171: traces carriage frame step versus Create contact motion across walk discontinuities; read-only only")
