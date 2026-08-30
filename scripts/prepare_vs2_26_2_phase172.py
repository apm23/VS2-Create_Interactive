#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = client_probe.read_text(encoding="utf-8")
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #331 isolated the first walk-frame discontinuity to Create itself: active
# carriage 5 applied its exact 2.9776-block native contact motion, then sibling carriage 7 applied
# another 6.0569-block native contact motion in the same LocalPlayer tick, yielding the measured
# 9.0345-block player delta. Before changing production behavior, prove the minimal hypothesis in
# the disposable production smoke fixture: once the walk's active carriage has already supplied a
# native contact motion in a tick, suppress only a later non-active sibling contact motion in that
# same tick. No vector is synthesized or clamped; the active Create-computed motion remains intact.
# Outside productionSmokeFixture this phase does not alter Create/VS2 movement behavior.

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
contact_replacement = '''        if (phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8) {\n            String phase172ActiveCarriageId = System.getProperty("vs2.phase172WalkActiveCarriageId");\n            boolean phase172FixtureWalkActive = java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")\n                && phase172ActiveCarriageId != null;\n            boolean phase172ActiveAlreadyAppliedThisTick = phase172FixtureWalkActive\n                && Integer.toString(phase170Player.tickCount).equals(System.getProperty("vs2.phase170NativeContactApplicationTick"))\n                && phase172ActiveCarriageId.equals(System.getProperty("vs2.phase170NativeContactApplicationCarriageId"));\n            boolean phase172DuplicateSiblingNativeCarry = phase172ActiveAlreadyAppliedThisTick\n                && !phase172ActiveCarriageId.equals(Integer.toString(self.getId()));\n            if (phase172DuplicateSiblingNativeCarry) {\n                LOGGER.info(\n                    "GATE_E_PHASE172_DUPLICATE_SIBLING_NATIVE_CARRY_SUPPRESSED player_tick={} active_carriage_id={} sibling_carriage_id={} sibling_motion={} active_already_applied=true fixture_only=true hypothesis_guard=true",\n                    phase170Player.tickCount, phase172ActiveCarriageId, self.getId(), motion);\n                cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO);\n                return;\n            }\n            System.setProperty("vs2.phase170NativeContactApplicationTick", Integer.toString(phase170Player.tickCount));\n            System.setProperty("vs2.phase170NativeContactApplicationCarriageId", Integer.toString(self.getId()));'''
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
    "phase172DuplicateSiblingNativeCarry",
    "cir.setReturnValue(net.minecraft.world.phys.Vec3.ZERO)",
    "cancellable = true",
    "fixture_only=true",
]
missing = [token for token in required_client if token not in source] + [token for token in required_contact if token not in contact_source]
if missing:
    raise SystemExit("Phase 172 lost duplicate-native-carry proof anchors: " + ", ".join(missing))

# The only mutation introduced here is cancellation of a proven duplicate sibling return value in
# the disposable fixture. It must not reposition the player, invent a carry vector, mutate trains,
# blocks/world state, inventory, or VS2 physics.
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 172 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
contact_trace.write_text(contact_source, encoding="utf-8")
print("Phase 172: fixture-only proof suppresses a second sibling native Create carry after active-carriage carry already applied in the same tick")
