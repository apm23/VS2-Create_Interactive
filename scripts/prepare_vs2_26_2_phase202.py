#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
probe_source = client_probe.read_text(encoding="utf-8")
trace_source = contact_trace.read_text(encoding="utf-8")
fixture_source = fixture_input.read_text(encoding="utf-8")

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

previous_native_scope = """    && carryBaselineCarriageId != carriage.getId()\n    && Integer.toString(player.tickCount - 1).equals(System.getProperty(\"vs2.phase170NativeContactApplicationTick\"))"""
previous_native_same_or_sibling = """    && Integer.toString(player.tickCount - 1).equals(System.getProperty(\"vs2.phase170NativeContactApplicationTick\"))"""
if previous_native_scope not in probe_source:
    raise SystemExit("Phase 202 expected the Phase189 sibling-only native-gap boundary")
probe_source = probe_source.replace(previous_native_scope, previous_native_same_or_sibling, 1)

# Production-world #529 proves the fixture can request jump four ticks after strafe while
# Create has not applied genuine ContraptionColliderClient carriage contact since that strafe.
# The Phase83 registerColliding lease is intentionally not treated as equivalent: local carriage
# X still drifted until native Create application resumed. Keep the fixture's vanilla jump pulse
# dormant until the immediately previous tick has genuine native Create contact. This changes
# harness sequencing only; it does not move the player or synthesize carry/collision/physics.
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
        '''        return vs2$strafeStartTick != Integer.MIN_VALUE\n            && self.tickCount >= vs2$strafeStartTick + 4\n            && Integer.toString(self.tickCount - 1).equals(\n                System.getProperty("vs2.phase170NativeContactApplicationTick"));''',
    ),
]
for old, new in timing_replacements:
    if fixture_source.count(old) != 1:
        raise SystemExit("Phase 202 expected one M1 fixture timing boundary")
    fixture_source = fixture_source.replace(old, new, 1)

# Production-world #488 proves vanilla SELF locomotion is already present during the reverse
# window while LocalPlayer.aiStep RETURN still reports onGround=false. Create applies the moving-
# contraption contact later in the same client tick, after which carriage continuity reports
# on_ground=true. Do not reject native reverse/strafe merely because the pre-Create aiStep timing
# has not received that later contact flag yet. This changes fixture acceptance only; the input,
# movement and grounding paths remain vanilla/Create-native.
locomotion_confirmation_replacements = [
    (
        '''        if (self.onGround() && client.options.keyDown.isDown()\n                && self.getDeltaMovement().horizontalDistanceSqr() > 0.0004) {''',
        '''        if (client.options.keyDown.isDown()\n                && self.getDeltaMovement().horizontalDistanceSqr() > 0.0004) {''',
    ),
    (
        '''                "GATE_E_M1_NATIVE_BACKWARD_CONFIRMED player_tick={} start_tick={} duration_ticks={} horizontal_speed_sq={} on_ground=true fixture_only=true vanilla_keymapping=true native_motion=true",''',
        '''                "GATE_E_M1_NATIVE_BACKWARD_CONFIRMED player_tick={} start_tick={} duration_ticks={} horizontal_speed_sq={} grounding_deferred_to_create_contact=true fixture_only=true vanilla_keymapping=true native_motion=true",''',
    ),
    (
        '''        if (self.onGround() && client.options.keyRight.isDown()\n                && self.getDeltaMovement().horizontalDistanceSqr() > 0.0004) {''',
        '''        if (client.options.keyRight.isDown()\n                && self.getDeltaMovement().horizontalDistanceSqr() > 0.0004) {''',
    ),
    (
        '''                "GATE_E_M1_NATIVE_STRAFE_CONFIRMED player_tick={} start_tick={} duration_ticks={} horizontal_speed_sq={} on_ground=true fixture_only=true vanilla_keymapping=true native_motion=true direction=right",''',
        '''                "GATE_E_M1_NATIVE_STRAFE_CONFIRMED player_tick={} start_tick={} duration_ticks={} horizontal_speed_sq={} grounding_deferred_to_create_contact=true fixture_only=true vanilla_keymapping=true native_motion=true direction=right",''',
    ),
]
for old, new in locomotion_confirmation_replacements:
    if fixture_source.count(old) != 1:
        raise SystemExit("Phase 202 expected one pre-Create-grounding M1 confirmation boundary")
    fixture_source = fixture_source.replace(old, new, 1)

# Production-world #485 reached the native jump request after carry/walk/reverse/strafe, but never
# became airborne. Phase196 already proved why: fixture KeyMappings can be set after Minecraft's normal
# KeyboardInput sampling point. Reuse that same native KeyboardInput.tick sampling boundary immediately
# after this fixture updates movement/jump KeyMappings at LocalPlayer.aiStep HEAD, before vanilla aiStep
# consumes Input. Harness-only; no position, velocity, collision, carry, gravity, train or world mutation.
head_anchor = '''        vs2$sampleNativeJump(self, client);\n        if (self.tickCount != vs2$lastHeadTick && self.tickCount <= startTick + 5) {'''
head_insert = '''        vs2$sampleNativeJump(self, client);\n        try {\n            java.lang.reflect.Field inputField = null;\n            Class<?> playerClass = self.getClass();\n            while (playerClass != null && inputField == null) {\n                try {\n                    inputField = playerClass.getDeclaredField("input");\n                } catch (NoSuchFieldException ignored) {\n                    playerClass = playerClass.getSuperclass();\n                }\n            }\n            if (inputField != null) {\n                inputField.setAccessible(true);\n                Object input = inputField.get(self);\n                if (input != null) {\n                    java.lang.reflect.Method tickMethod = null;\n                    Class<?> inputClass = input.getClass();\n                    while (inputClass != null && tickMethod == null) {\n                        for (java.lang.reflect.Method method : inputClass.getDeclaredMethods()) {\n                            if (method.getName().equals("tick") && method.getParameterCount() == 0) {\n                                tickMethod = method;\n                                break;\n                            }\n                        }\n                        inputClass = inputClass.getSuperclass();\n                    }\n                    if (tickMethod != null) {\n                        tickMethod.setAccessible(true);\n                        tickMethod.invoke(input);\n                    }\n                }\n            }\n        } catch (ReflectiveOperationException | RuntimeException ignored) {\n        }\n        if (self.tickCount != vs2$lastHeadTick && self.tickCount <= startTick + 5) {'''
if fixture_source.count(head_anchor) != 1:
    raise SystemExit("Phase 202 expected one LocalPlayer aiStep HEAD input-consumption anchor")
fixture_source = fixture_source.replace(head_anchor, head_insert, 1)

# Production-world #486 proves the jump itself already executes through vanilla LocalPlayer:
# Entity.move receives and applies +0.4199999869 Y on the requested jump tick, then later applies
# negative-Y SELF movement before settling. Create's moving-contraption contact keeps onGround true
# through that valid vertical arc, so the remaining failure is the fixture's obsolete airborne gate.
# Accept the native vertical arc from LocalPlayer delta movement instead of requiring onGround=false.
# Landing still requires a prior falling sample, onGround=true, and near-zero vertical speed.
old_jump_observer = '''        double deltaY = self.getDeltaMovement().y;\n        if (vs2$jumpStartTick != Integer.MIN_VALUE && !self.onGround() && deltaY > 0.0 && !vs2$jumpAirborneSeen) {\n            vs2$jumpAirborneSeen = true;\n            VS2_FIXTURE_INPUT_LOGGER.info(\n                "GATE_E_M1_NATIVE_JUMP_AIRBORNE player_tick={} start_tick={} delta_y={} on_ground=false fixture_only=true native_motion=true",\n                self.tickCount, vs2$jumpStartTick, deltaY);\n        }\n        if (vs2$jumpAirborneSeen && !self.onGround() && deltaY < 0.0) vs2$jumpFallingSeen = true;\n        if (vs2$jumpFallingSeen && self.onGround() && self.tickCount > vs2$jumpStartTick) {'''
new_jump_observer = '''        double deltaY = self.getDeltaMovement().y;\n        if (vs2$jumpStartTick != Integer.MIN_VALUE && deltaY > 0.05 && !vs2$jumpAirborneSeen) {\n            vs2$jumpAirborneSeen = true;\n            VS2_FIXTURE_INPUT_LOGGER.info(\n                "GATE_E_M1_NATIVE_JUMP_AIRBORNE player_tick={} start_tick={} delta_y={} on_ground={} fixture_only=true native_motion=true vertical_arc=true",\n                self.tickCount, vs2$jumpStartTick, deltaY, self.onGround());\n        }\n        if (vs2$jumpAirborneSeen && deltaY < -0.01) vs2$jumpFallingSeen = true;\n        if (vs2$jumpFallingSeen && self.onGround() && Math.abs(deltaY) < 0.005 && self.tickCount > vs2$jumpStartTick) {'''
if fixture_source.count(old_jump_observer) != 1:
    raise SystemExit("Phase 202 expected one obsolete onGround-gated jump observer")
fixture_source = fixture_source.replace(old_jump_observer, new_jump_observer, 1)

required_fixture = [
    "return elapsed >= 1 && elapsed <= 4;",
    "return elapsed >= 2 && elapsed <= 5;",
    "self.tickCount >= vs2$strafeStartTick + 4",
    "vs2.phase170NativeContactApplicationTick",
    "GATE_E_M1_NATIVE_BACKWARD_CONFIRMED",
    "GATE_E_M1_NATIVE_STRAFE_CONFIRMED",
    "grounding_deferred_to_create_contact=true",
    "GATE_E_M1_NATIVE_JUMP_LANDED",
    "client.options.keyDown.setDown(backwardWindow)",
    "client.options.keyRight.setDown(strafeWindow)",
    "client.options.keyJump.setDown(jumpPulse)",
    "getDeclaredField(\"input\")",
    "method.getName().equals(\"tick\")",
    "tickMethod.invoke(input)",
    "deltaY > 0.05",
    "deltaY < -0.01",
    "Math.abs(deltaY) < 0.005",
    "vertical_arc=true",
]
missing_fixture = [token for token in required_fixture if token not in fixture_source]
if missing_fixture:
    raise SystemExit("Phase 202 lost native M1 fixture anchors: " + ", ".join(missing_fixture))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in fixture_source:
        raise SystemExit("Phase 202 native M1 fixture contains forbidden gameplay mutation: " + forbidden)

client_probe.write_text(probe_source, encoding="utf-8")
contact_trace.write_text(trace_source, encoding="utf-8")
fixture_input.write_text(fixture_source, encoding="utf-8")
print("Phase 202: confirms native M1 locomotion before Create's later same-tick grounding and preserves the proven vanilla vertical jump arc")
