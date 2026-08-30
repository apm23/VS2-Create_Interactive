#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = client_probe.read_text(encoding="utf-8")
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #331 isolated duplicate sibling native carry after active-carriage carry.
# Production-world #352 exposed the inverse ordering: at walk tick 33 sibling carriage 4 applied
# -26.2664 before the still-active carriage 7 applied its exact -8.6833 motion. The old Phase172
# guard only suppressed siblings after the active carriage had already applied in the same tick,
# so sibling-first ordering escaped the guard and produced the exact 26.2664 local jump. In the
# disposable production smoke fixture only, also suppress a non-active sibling arriving first
# when the tracked active carriage was proven native-healthy on the immediately previous tick.
# A validated Phase156/176 handoff updates the active carriage id, so a real supported handoff is
# not permanently pinned to the old entity. No vector is synthesized or clamped; this only
# cancels a sibling Create return that is inconsistent with the currently proven active frame.

walk_anchor = '''                            phase154WalkCarriageId = phase154Carriage.getId();\n                            phase154WalkStartLocal = phase154Local;'''
walk_replacement = '''                            phase154WalkCarriageId = phase154Carriage.getId();\n                            System.setProperty("vs2.phase172WalkActiveCarriageId", Integer.toString(phase154WalkCarriageId));\n                            phase154WalkStartLocal = phase154Local;'''
inserted = ""
if "vs2.phase172WalkActiveCarriageId" not in source:
    if source.count(walk_anchor) != 1:
        raise SystemExit("Phase 172 expected exactly one Phase154 active-carriage start anchor")
    source = source.replace(walk_anchor, walk_replacement, 1)
    inserted += walk_replacement

inject_old = '''@Inject(method = "getContactPointMotion", at = @At("RETURN"), remap = false, require = 0)'''
inject_new = '''@Inject(method = "getContactPointMotion", at = @At("RETURN"), remap = false, require = 0, cancellable = true)'''
if "cancellable = true" not in contact_source:
    if contact_source.count(inject_old) != 1:
        raise SystemExit("Phase 172 expected exactly one contact-motion RETURN injection")
    contact_source = contact_source.replace(inject_old, inject_new, 1)
    inserted += inject_new

contact_anchor = '''        if (phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8) {\n            System.setProperty("vs2.phase170NativeContactApplicationTick", Integer.toString(phase170Player.tickCount));\n            System.setProperty("vs2.phase170NativeContactApplicationCarriageId", Integer.toString(self.getId()));'''
contact_replacement = '''        if (phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8) {\n            String phase172ActiveCarriageId = System.getProperty("vs2.phase172WalkActiveCarriageId");\n            boolean phase172FixtureWalkActive = java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")\n                && phase172ActiveCarriageId != null;\n            boolean phase172ActiveAlreadyAppliedThisTick = phase172FixtureWalkActive\n                && Integer.toString(phase170Player.tickCount).equals(System.getProperty("vs2.phase170NativeContactApplicationTick"))\n                && phase172ActiveCarriageId.equals(System.getProperty("vs2.phase170NativeContactApplicationCarriageId"));\n            boolean phase172ActiveHealthyPreviousTick = phase172FixtureWalkActive\n                && java.lang.Boolean.parseBoolean(System.getProperty(\n                    "vs2.phase134NativeCarryHealthy." + phase172ActiveCarriageId, "false"))\n                && Integer.toString(phase170Player.tickCount - 1).equals(System.getProperty(\n                    "vs2.phase134NativeCarryHealthyTick." + phase172ActiveCarriageId));\n            boolean phase172NonActiveSibling = phase172FixtureWalkActive\n                && !phase172ActiveCarriageId.equals(Integer.toString(self.getId()));\n            boolean phase172DuplicateSiblingNativeCarry = phase172NonActiveSibling\n                && (phase172ActiveAlreadyAppliedThisTick || phase172ActiveHealthyPreviousTick);\n            if (phase172DuplicateSiblingNativeCarry) {\n                LOGGER.info(\n                    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} active_already_applied={} active_healthy_previous_tick={} sibling_first_guard={} fixture_only=true hypothesis_guard=true",\n                    phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion,\n                    phase172ActiveAlreadyAppliedThisTick, phase172ActiveHealthyPreviousTick,\n                    !phase172ActiveAlreadyAppliedThisTick && phase172ActiveHealthyPreviousTick);\n                cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO);\n                return;\n            }\n            System.setProperty("vs2.phase170NativeContactApplicationTick", Integer.toString(phase170Player.tickCount));\n            System.setProperty("vs2.phase170NativeContactApplicationCarriageId", Integer.toString(self.getId()));'''
if "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED" not in contact_source:
    if contact_source.count(contact_anchor) != 1:
        raise SystemExit("Phase 172 expected exactly one Phase170 native-application publication block")
    contact_source = contact_source.replace(contact_anchor, contact_replacement, 1)
    inserted += contact_replacement

required_client = [
    "GATE_E_CARRIAGE_LOCAL_CONTINUITY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED",
    "vs2.phase172WalkActiveCarriageId",
]
required_contact = [
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
    "GATE_E_PHASE171_CARRIAGE_FRAME_STEP",
    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED",
    "phase172ActiveAlreadyAppliedThisTick",
    "phase172ActiveHealthyPreviousTick",
    "phase172NonActiveSibling",
    "phase172DuplicateSiblingNativeCarry",
    "vs2.phase134NativeCarryHealthy.",
    "vs2.phase134NativeCarryHealthyTick.",
    "sibling_first_guard={}",
    "cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO)",
    "cancellable = true",
    "fixture_only=true",
]
missing = [token for token in required_client if token not in source] + [token for token in required_contact if token not in contact_source]
if missing:
    raise SystemExit("Phase 172 lost duplicate-native-carry proof anchors: " + ", ".join(missing))

# The only mutation introduced here is cancellation of a proven duplicate/inconsistent sibling
# return value in the disposable fixture. It must not reposition the player, invent a carry vector,
# mutate trains, blocks/world state, inventory, or VS2 physics.
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 172 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
contact_trace.write_text(contact_source, encoding="utf-8")
print("Phase 172: fixture-only proof suppresses sibling native carry both after same-tick active carry and before active carry when the active frame was healthy on the previous tick")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase173.py")), run_name="__main__")
