#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #391 proved a real one-tick carry hole at walk tick 18. The player had
# strict grounded/broadphase support on baseline carriage 2, while Create had natively carried
# the LocalPlayer on sibling carriage 4 on tick 17 and resumed that same sibling carrier on tick
# 19. On tick 18 Create executed the collider path but applied zero motion, while both sibling
# carriage frame steps were the same 8.765974 blocks; the player therefore missed exactly that
# train-frame step. Reuse the existing Create-computed, Create-collision-filtered Phase85 replay
# only for that narrowly identified previous-native-sibling gap. No new vector, teleport, direct
# movement, train/world mutation, or VS2 physics path is introduced.

support_old = '''                        boolean phase154SupportNow = phase154Broadphase && player.onGround()
                            && phase154Carriage.getId() == carryBaselineCarriageId;
'''
support_new = support_old + '''                        System.setProperty("vs2.phase189BaselineSupportTick", Integer.toString(player.tickCount));
                        System.setProperty("vs2.phase189BaselineSupportHealthy", Boolean.toString(phase154SupportNow));
                        System.setProperty("vs2.phase189BaselineSupportCarriageId", Integer.toString(phase154Carriage.getId()));
'''
if "vs2.phase189BaselineSupportTick" not in source:
    if source.count(support_old) != 1:
        raise SystemExit("Phase 189 expected exactly one Phase154 support publication site")
    source = source.replace(support_old, support_new, 1)

replay_token = "carryReplayPlayerTick != player.tickCount"
replay_pos = source.find(replay_token)
if replay_pos < 0 or source.find(replay_token, replay_pos + 1) >= 0:
    raise SystemExit("Phase 189 expected exactly one final Phase85 replay-tick predicate")
replay_if_pos = source.rfind("if (", 0, replay_pos)
if replay_if_pos < 0:
    raise SystemExit("Phase 189 could not locate final Phase85 replay guard")
line_start = source.rfind("\n", 0, replay_if_pos) + 1
indent = source[line_start:replay_if_pos]

selector = ""
if "phase189SiblingNativeGap" not in source:
    selector = (
        f'{indent}boolean phase189BaselineSupportNow = productionSmokeFixture\n'
        f'{indent}    && phase154WalkStarted && !phase154WalkFinished\n'
        f'{indent}    && Integer.toString(player.tickCount).equals(System.getProperty("vs2.phase189BaselineSupportTick"))\n'
        f'{indent}    && Boolean.parseBoolean(System.getProperty("vs2.phase189BaselineSupportHealthy", "false"))\n'
        f'{indent}    && Integer.toString(carryBaselineCarriageId).equals(System.getProperty("vs2.phase189BaselineSupportCarriageId"));\n'
        f'{indent}boolean phase189PreviousNativeSibling = phase189BaselineSupportNow\n'
        f'{indent}    && carryBaselineCarriageId != carriage.getId()\n'
        f'{indent}    && Integer.toString(player.tickCount - 1).equals(System.getProperty("vs2.phase170NativeContactApplicationTick"))\n'
        f'{indent}    && Integer.toString(carriage.getId()).equals(System.getProperty("vs2.phase170NativeContactApplicationCarriageId"));\n'
        f'{indent}boolean phase189SiblingNativeGap = productionSmoke && explicitCarryCompat\n'
        f'{indent}    && phase189PreviousNativeSibling\n'
        f'{indent}    && !phase170NativeContactAppliedThisTick\n'
        f'{indent}    && collisionEligible && broadphaseOverlap && player.onGround();\n'
        f'{indent}if (phase189SiblingNativeGap) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY carriage_id={{}} player_tick={{}} baseline_carriage_id={{}} previous_native_carriage_id={{}} baseline_support=true collision_eligible=true broadphase=true grounded=true existing_create_filtered_replay=true bounded_one_tick=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, carryBaselineCarriageId, System.getProperty("vs2.phase170NativeContactApplicationCarriageId", "unknown"));\n'
        f'{indent}}}\n\n'
    )
    source = source[:line_start] + selector + source[line_start:]
    replay_pos = source.find(replay_token, line_start + len(selector))
    replay_if_pos = source.rfind("if (", 0, replay_pos)

# Widen only the final replay guard. Cumulative phases legitimately contain more than one
# baseline-identity check inside this guard; choose the occurrence closest to the unique replay
# tick predicate, matching Phase187's structural targeting strategy instead of assuming count=1.
guard = source[replay_if_pos:replay_pos]
identity_old = "carryBaselineCarriageId == carriage.getId()"
identity_new = "(carryBaselineCarriageId == carriage.getId() || phase189SiblingNativeGap)"
if identity_new not in guard:
    identity_pos = guard.rfind(identity_old)
    if identity_pos < 0:
        raise SystemExit("Phase 189 could not find final baseline identity predicate")
    guard = guard[:identity_pos] + identity_new + guard[identity_pos + len(identity_old):]

support_variants = [
    "(phase81PhysicalSupport || phase133ReplayGrace)",
    "phase81PhysicalSupport",
]
support_done = "((phase81PhysicalSupport || phase133ReplayGrace) || phase189SiblingNativeGap)"
if support_done not in guard:
    if support_variants[0] in guard:
        guard = guard.replace(support_variants[0], support_done, 1)
    elif support_variants[1] in guard:
        guard = guard.replace(support_variants[1], "(phase81PhysicalSupport || phase189SiblingNativeGap)", 1)
    else:
        raise SystemExit("Phase 189 could not find final physical-support predicate")

source = source[:replay_if_pos] + guard + source[replay_pos:]

required = [
    "vs2.phase189BaselineSupportTick",
    "vs2.phase189BaselineSupportHealthy",
    "vs2.phase189BaselineSupportCarriageId",
    "phase189BaselineSupportNow",
    "phase189PreviousNativeSibling",
    "phase189SiblingNativeGap",
    "carryBaselineCarriageId != carriage.getId()",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "!phase170NativeContactAppliedThisTick",
    "GATE_E_PHASE189_SIBLING_NATIVE_GAP_RECOVERY",
    "existing_create_filtered_replay=true",
    "bounded_one_tick=true",
    "phase189SiblingNativeGap)",
    "GATE_E_PHASE85_CARRY_REPLAY",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 189 lost sibling native-gap recovery anchors: " + ", ".join(missing))

inserted = support_new + selector + identity_new + support_done
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 189 introduced forbidden direct gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 189: recovers only the proven one-tick previous-native sibling carry gap using existing Create-filtered Phase85 motion")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase190.py")), run_name="__main__")
