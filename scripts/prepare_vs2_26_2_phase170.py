#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = client_probe.read_text(encoding="utf-8")
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #323 reached the real train and isolated a duplicate-carry edge. At walk tick 20
# Create produced native contact motion from sibling carriage 7 (~8.913 blocks) and the fixture's
# Phase170-expanded Phase85 recovery also replayed carriage 5 motion (~5.805 blocks); their sum is
# the observed 14.718-block carriage-local discontinuity. Do not alter either carry vector. Instead,
# distinguish a real Create ContraptionColliderClient caller from GateE's diagnostic contact-motion
# calls and suppress only the fixture recovery when native Create contact was already applied in the
# same LocalPlayer tick. Production behavior remains unchanged outside productionSmokeFixture.
#
# Production-world #354 then exposed a preparation-order compatibility bug after Phase161 replaced
# its historical inline four-key predicate with phase161LocomotionWindow so the bounded one-pulse
# observation window remains eligible after key release. Phase170 now consumes that abstraction
# directly instead of pattern-matching the retired inline key clause. This is harness/recovery
# accounting only; Phase85 remains the sole producer of the existing Create-filtered carry vector.
#
# Production-world #435 proved the global Phase170 carriage id is last-writer-wins when multiple
# sibling Create carriages apply native contact in one LocalPlayer tick. Preserve the historical
# globals, but also publish a per-carriage application tick so later fixture accounting can observe
# exact active-carriage native evidence even when a sibling writes afterward in the same tick.
#
# Production-world #704 proves the same-tick suppression must also be carriage-scoped. During the
# first native locomotion handoff, strict support/active ownership moved to carriage 7 while Create
# still emitted native contact from carriage 5 for ticks 19-21. The old global tick predicate treated
# that sibling application as if carriage 7 had applied and disabled the already-existing bounded
# recovery on the actual active carriage, producing multi-block local discontinuities. Suppress only
# when the same active carriage owns the same-tick native application; no carry vector or physics is
# added here.

contact_anchor = '''        net.minecraft.world.phys.Vec3 motion = cir.getReturnValue();
        LOGGER.info(
'''
contact_insert = '''        net.minecraft.world.phys.Vec3 motion = cir.getReturnValue();
        boolean phase170NativeClientColliderCall = java.lang.StackWalker.getInstance().walk(
            frames -> frames.anyMatch(frame -> frame.getClassName().contains("ContraptionColliderClient")));
        net.minecraft.client.player.LocalPlayer phase170Player = net.minecraft.client.Minecraft.getInstance().player;
        if (phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8) {
            System.setProperty("vs2.phase170NativeContactApplicationTick", Integer.toString(phase170Player.tickCount));
            System.setProperty("vs2.phase170NativeContactApplicationCarriageId", Integer.toString(self.getId()));
            System.setProperty("vs2.phase170NativeContactApplicationTick." + self.getId(), Integer.toString(phase170Player.tickCount));
            LOGGER.info(
                "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION player_tick={} carriage_id={} motion={} application_call=true source=ContraptionColliderClient read_only=true fixture_accounting=true",
                phase170Player.tickCount, self.getId(), motion);
        }
        LOGGER.info(
'''
if "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION" not in contact_source:
    if contact_source.count(contact_anchor) != 1:
        raise SystemExit("Phase 170 expected exactly one Phase168 fully-qualified contact-motion log anchor")
    contact_source = contact_source.replace(contact_anchor, contact_insert, 1)

old_decl = "boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat"
new_decl = '''boolean phase170FixtureWalkActive = productionSmokeFixture
            && phase154WalkStarted && !phase154WalkFinished;
        boolean phase170NativeContactAppliedThisTick = Integer.toString(player.tickCount).equals(
            System.getProperty("vs2.phase170NativeContactApplicationTick"))
            && Integer.toString(carriage.getId()).equals(
                System.getProperty("vs2.phase170NativeContactApplicationCarriageId"));
        boolean phase170FixtureWalkRecoveryWindow = phase170FixtureWalkActive
            && !phase170NativeContactAppliedThisTick;
        boolean phase170RecoveryLocomotionWindow = phase170FixtureWalkRecoveryWindow
            || (!phase170FixtureWalkActive && phase161LocomotionWindow);
        boolean phase161SupportedLocomotionNativeLoss = productionSmoke && explicitCarryCompat'''
if "phase170FixtureWalkRecoveryWindow" not in source:
    if source.count(old_decl) != 1:
        raise SystemExit("Phase 170 expected exactly one Phase161 recovery declaration")
    source = source.replace(old_decl, new_decl, 1)

# Patch only the Phase161 declaration body. Older cumulative sources used an inline four-key
# expression here; current Phase161 publishes phase161LocomotionWindow. Prefer the abstraction,
# while retaining the historical fallback so this phase remains deterministic on older snapshots.
if "&& phase170RecoveryLocomotionWindow" not in source:
    decl_pos = source.find("boolean phase161SupportedLocomotionNativeLoss =")
    if decl_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 supported-loss declaration")
    decl_end = source.find(";", decl_pos)
    if decl_end < 0:
        raise SystemExit("Phase 170 could not bound Phase161 supported-loss declaration")
    predicate = source[decl_pos:decl_end + 1]

    locomotion_token = "&& phase161LocomotionWindow"
    if predicate.count(locomotion_token) == 1:
        predicate = predicate.replace(locomotion_token, "&& phase170RecoveryLocomotionWindow", 1)
    else:
        key_pattern = re.compile(
            r"\(\s*client\.options\.keyUp\.isDown\(\)\s*\|\|\s*client\.options\.keyDown\.isDown\(\)\s*"
            r"\|\|\s*client\.options\.keyLeft\.isDown\(\)\s*\|\|\s*client\.options\.keyRight\.isDown\(\)\s*\)"
        )
        predicate, key_count = key_pattern.subn(
            "phase170RecoveryLocomotionWindow",
            predicate,
            count=1,
        )
        if key_count != 1:
            raise SystemExit("Phase 170 expected exactly one locomotion-window or historical key-state clause inside Phase161 predicate")

    previous_native_pattern = re.compile(
        r"Integer\.toString\(player\.tickCount\s*-\s*1\)\.equals\(System\.getProperty\(\s*"
        r"\"vs2\.phase134NativeCarryHealthyTick\.\"\s*\+\s*carriage\.getId\(\)\s*\)\)"
    )
    predicate, native_count = previous_native_pattern.subn(
        "(phase170FixtureWalkRecoveryWindow || Integer.toString(player.tickCount - 1).equals(System.getProperty(\n"
        "                    \"vs2.phase134NativeCarryHealthyTick.\" + carriage.getId())))",
        predicate,
        count=1,
    )
    if native_count != 1:
        raise SystemExit("Phase 170 expected exactly one previous-native clause inside Phase161 predicate")
    source = source[:decl_pos] + predicate + source[decl_end + 1:]

if "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY" not in source:
    replay_marker = '"GATE_E_PHASE161_SUPPORTED_LOCOMOTION_NATIVE_LOSS_REPLAY'
    marker_pos = source.find(replay_marker)
    if marker_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 replay log marker")
    if_pos = source.rfind("if (phase161SupportedLocomotionNativeLoss) {", 0, marker_pos)
    if if_pos < 0:
        raise SystemExit("Phase 170 could not locate Phase161 replay log guard")
    line_start = source.rfind("\n", 0, if_pos) + 1
    indent = source[line_start:if_pos]
    log_insert = (
        f'{indent}if (phase170FixtureWalkActive && phase170NativeContactAppliedThisTick) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE170_NATIVE_CONTACT_SUPPRESSES_RECOVERY player_tick={{}} active_carriage_id={{}} native_contact_carriage_id={{}} same_tick_native_contact=true fixture_only=true read_only_accounting=true",\n'
        f'{indent}        player.tickCount, carriage.getId(), System.getProperty("vs2.phase170NativeContactApplicationCarriageId", "unknown"));\n'
        f'{indent}}}\n'
        f'{indent}if (phase161SupportedLocomotionNativeLoss && phase170FixtureWalkRecoveryWindow) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY carriage_id={{}} player_tick={{}} current_measurement={{}} measured_undercarry={{}} strict_support=true existing_create_filtered_replay=true fixture_only=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, phase161CurrentMeasurement, phase161MeasuredUndercarry);\n'
        f'{indent}}}\n'
    )
    source = source[:line_start] + log_insert + source[line_start:]

required = [
    "phase170FixtureWalkActive",
    "phase170NativeContactAppliedThisTick",
    "phase170FixtureWalkRecoveryWindow",
    "phase170RecoveryLocomotionWindow",
    "phase161LocomotionWindow",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "Integer.toString(carriage.getId()).equals(",
    "&& phase170RecoveryLocomotionWindow",
    "phase170FixtureWalkRecoveryWindow || Integer.toString(player.tickCount - 1)",
    "GATE_E_PHASE170_NATIVE_CONTACT_SUPPRESSES_RECOVERY",
    "GATE_E_PHASE170_FIXTURE_WALK_NATIVE_LOSS_RECOVERY",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "fixture_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 170 lost fixture-only recovery anchors: " + ", ".join(missing))

contact_required = [
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
    "ContraptionColliderClient",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "vs2.phase170NativeContactApplicationTick.",
    "java.lang.StackWalker",
    "net.minecraft.world.phys.Vec3 motion = cir.getReturnValue()",
    "read_only=true",
]
contact_missing = [token for token in contact_required if token not in contact_source]
if contact_missing:
    raise SystemExit("Phase 170 lost native contact application anchors: " + ", ".join(contact_missing))

# Phase170 adds call-site accounting and recovery suppression only. It must not add a movement,
# collision, train, world, inventory, or VS2 physics mutation.
phase170_inserted = new_decl + contact_insert + "GATE_E_PHASE170_NATIVE_CONTACT_SUPPRESSES_RECOVERY"
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in phase170_inserted:
        raise SystemExit("Phase 170 introduced direct gameplay mutation: " + forbidden)

contact_trace.write_text(contact_source, encoding="utf-8")
client_probe.write_text(source, encoding="utf-8")
print("Phase 170: consumes Phase161 locomotion-window abstraction, tracks exact native application per carriage, and suppresses fixture recovery only for same-carriage native contact")
