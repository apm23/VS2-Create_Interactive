#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
probe_source = client_probe.read_text(encoding="utf-8")
trace_source = contact_trace.read_text(encoding="utf-8")
fixture_source = fixture_input.read_text(encoding="utf-8")

# Production-world #457 proves native carry, interaction dispatch, and authoritative new-cell
# replication, but the bounded walk never starts: Phase194 arms carriage 4 on player tick 23 after
# two strict/native-supported ticks, then tick 24 loses baseline support while sibling carriage 2
# reports a large frame/contact-motion discontinuity. Do not widen replay or relax acceptance yet.
# Correlate the already-read-only Phase171 carriage frame/contact values with the one-tick Phase194
# pending-confirmation window so the next real-world run can distinguish a Create transform handoff
# from a missing carry application without changing movement, collision, train, world, or VS2 physics.

arm_anchor = '''                            phase194PendingWalkCarriageId = phase154Carriage.getId();\n                            phase194PendingWalkTick = player.tickCount;\n'''
arm_insert = arm_anchor + '''                            System.setProperty("vs2.phase194PendingWalkCarriageId", Integer.toString(phase194PendingWalkCarriageId));\n                            System.setProperty("vs2.phase194PendingWalkTick", Integer.toString(phase194PendingWalkTick));\n'''
if 'System.setProperty("vs2.phase194PendingWalkTick"' not in probe_source:
    if probe_source.count(arm_anchor) != 1:
        raise SystemExit("Phase 202 expected one Phase194 direct-native arm assignment")
    probe_source = probe_source.replace(arm_anchor, arm_insert, 1)

anchor = '''            LOGGER.info(\n                "GATE_E_PHASE171_CARRIAGE_FRAME_STEP player_tick={} carriage_id={} previous_player_tick={} frame_step={} contact_motion={} motion_minus_frame_step={} carriage_pos={} read_only=true diagnostic_state_only=true",\n                phase170Player.tickCount, self.getId(), phase171PreviousPlayerTick,\n                phase171FrameStep, motion, phase171MotionResidual, phase171Position);\n'''
insert = anchor + '''            String phase202PendingTickRaw = System.getProperty("vs2.phase194PendingWalkTick");\n            String phase202PendingCarriageRaw = System.getProperty("vs2.phase194PendingWalkCarriageId");\n            if (Boolean.getBoolean("vs2.productionSmokeFixture")\n                    && phase202PendingTickRaw != null && phase202PendingCarriageRaw != null) {\n                try {\n                    int phase202PendingTick = Integer.parseInt(phase202PendingTickRaw);\n                    int phase202PendingCarriage = Integer.parseInt(phase202PendingCarriageRaw);\n                    if (phase170Player.tickCount == phase202PendingTick + 1) {\n                        boolean phase202NativeApplied = Integer.toString(phase170Player.tickCount).equals(\n                            System.getProperty("vs2.phase170NativeContactApplicationTick." + self.getId()));\n                        LOGGER.info(\n                            "GATE_E_PHASE202_PENDING_CONFIRM_CONTACT player_tick={} carriage_id={} pending_carriage_id={} pending_tick={} is_pending_carriage={} frame_step={} contact_motion={} motion_minus_frame_step={} native_applied_this_tick={} carriage_pos={} fixture_only=true read_only=true diagnostic_state_only=true",\n                            phase170Player.tickCount, self.getId(), phase202PendingCarriage, phase202PendingTick,\n                            self.getId() == phase202PendingCarriage, phase171FrameStep, motion, phase171MotionResidual,\n                            phase202NativeApplied, phase171Position);\n                    }\n                } catch (NumberFormatException ignored) {\n                }\n            }\n'''

if "GATE_E_PHASE202_PENDING_CONFIRM_CONTACT" not in trace_source:
    if trace_source.count(anchor) != 1:
        raise SystemExit("Phase 202 expected one Phase171 carriage-frame log anchor")
    trace_source = trace_source.replace(anchor, insert, 1)

required_probe = [
    'System.setProperty("vs2.phase194PendingWalkCarriageId"',
    'System.setProperty("vs2.phase194PendingWalkTick"',
    "GATE_E_PHASE194_DIRECT_NATIVE_WALK_ARM",
]
required_trace = [
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
missing = [token for token in required_probe if token not in probe_source]
missing += [token for token in required_trace if token not in trace_source]
if missing:
    raise SystemExit("Phase 202 lost pending-confirmation telemetry anchors: " + ", ".join(missing))

inserted = arm_insert + insert
for forbidden in [
    "setPos(", "setDeltaMovement(", ".move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 202 introduced forbidden gameplay mutation: " + forbidden)

# Production-world #483 still proved stable carry and supported sprinting, but the fixed eight-tick
# post-walk delay did not request reverse until the finite-route support seam had already started.
# Keep the exact same vanilla KeyMapping -> LocalPlayer.aiStep path and acceptance thresholds, but
# chain reverse, right-strafe, and jump inside the already-proven supported interval. This changes
# only disposable production-smoke input timing; it does not synthesize position, velocity, carry,
# collision, gravity, train state, world state, or VS2/Create physics.
timing_replacements = [
    (
        '''        int elapsed = self.tickCount - vs2$walkConfirmedTick;\n        return elapsed >= 8 && elapsed <= 11;''',
        '''        int elapsed = self.tickCount - vs2$walkConfirmedTick;\n        return elapsed >= 1 && elapsed <= 4;''',
    ),
    (
        '''        int elapsed = self.tickCount - vs2$walkConfirmedTick;\n        return elapsed >= 13 && elapsed <= 16;''',
        '''        if (vs2$backwardStartTick == Integer.MIN_VALUE) return false;\n        int elapsed = self.tickCount - vs2$backwardStartTick;\n        return elapsed >= 2 && elapsed <= 5;''',
    ),
    (
        '''        return self.tickCount >= vs2$walkConfirmedTick + 24;''',
        '''        return vs2$strafeStartTick != Integer.MIN_VALUE && self.tickCount >= vs2$strafeStartTick + 4;''',
    ),
]
for old, new in timing_replacements:
    if fixture_source.count(old) != 1:
        raise SystemExit("Phase 202 expected one M1 fixture timing boundary: " + old.splitlines()[-1].strip())
    fixture_source = fixture_source.replace(old, new, 1)

required_fixture = [
    "return elapsed >= 1 && elapsed <= 4;",
    "self.tickCount - vs2$backwardStartTick",
    "return elapsed >= 2 && elapsed <= 5;",
    "self.tickCount >= vs2$strafeStartTick + 4",
    "GATE_E_M1_NATIVE_BACKWARD_CONFIRMED",
    "GATE_E_M1_NATIVE_STRAFE_CONFIRMED",
    "GATE_E_M1_NATIVE_JUMP_LANDED",
    "client.options.keyDown.setDown(backwardWindow)",
    "client.options.keyRight.setDown(strafeWindow)",
    "client.options.keyJump.setDown(jumpPulse)",
]
missing_fixture = [token for token in required_fixture if token not in fixture_source]
if missing_fixture:
    raise SystemExit("Phase 202 lost compact native M1 fixture anchors: " + ", ".join(missing_fixture))
for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in fixture_source:
        raise SystemExit("Phase 202 compact M1 fixture contains forbidden gameplay mutation: " + forbidden)

client_probe.write_text(probe_source, encoding="utf-8")
contact_trace.write_text(trace_source, encoding="utf-8")
fixture_input.write_text(fixture_source, encoding="utf-8")
print("Phase 202: keeps native reverse, right-strafe, and jump inside the proven support window; harness-only")
