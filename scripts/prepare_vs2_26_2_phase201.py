#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerMoveTrace.java"
source = java.read_text(encoding="utf-8")

# Production-world #431 proves Phase200 samples KeyboardInput with key_up=true before LocalPlayer.tick,
# yet LocalPlayer.tick RETURN still has no horizontal locomotion. Do not synthesize motion. Instead,
# extend the already-proven Entity.move trace with the immediate vanilla caller during the bounded walk
# so the actual locomotion boundary can be identified from runtime evidence.
helper_anchor = '''    @Unique private int vs2$currentIndex;\n\n'''
helper = helper_anchor + '''    @Unique\n    private static String vs2$walkMoveCallerSummary() {\n        StackTraceElement[] stack = Thread.currentThread().getStackTrace();\n        StringBuilder out = new StringBuilder();\n        int emitted = 0;\n        for (StackTraceElement frame : stack) {\n            String owner = frame.getClassName();\n            if (owner.equals(Thread.class.getName())\n                    || owner.contains("MixinEntityLocalPlayerMoveTrace")\n                    || (owner.equals("net.minecraft.world.entity.Entity") && frame.getMethodName().equals("move"))) continue;\n            if (emitted++ > 0) out.append(" <- ");\n            out.append(owner).append('#').append(frame.getMethodName());\n            if (emitted >= 6) break;\n        }\n        return out.toString();\n    }\n\n'''
if "vs2$walkMoveCallerSummary" not in source:
    if source.count(helper_anchor) != 1:
        raise SystemExit("Phase 201 expected one Entity.move helper anchor")
    source = source.replace(helper_anchor, helper, 1)

# Phase 186 extends this same read-only HEAD record with player_tick. Anchor Phase 201 to the
# current generated shape rather than the pre-186 format so the prepare chain cannot fail before
# the real train world launches.
log_anchor = '''        VS2_GATE_E_ENTITY_MOVE_LOGGER.info(\n            "GATE_E_LOCALPLAYER_ENTITY_MOVE_HEAD index={} player_tick={} mover={} requested={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",\n            index, self.tickCount, String.valueOf(type), requested.x, requested.y, requested.z,\n            vs2$beforeX, vs2$beforeY, vs2$beforeZ,\n            self.getDeltaMovement().x, self.getDeltaMovement().y, self.getDeltaMovement().z,\n            self.onGround());\n'''
log_insert = log_anchor + '''        String rawWalkStart = System.getProperty("vs2.productionFixtureWalkStartTick");\n        if (Boolean.getBoolean("vs2.productionSmokeFixture") && rawWalkStart != null) {\n            try {\n                int walkStart = Integer.parseInt(rawWalkStart);\n                if (self.tickCount >= walkStart && self.tickCount <= walkStart + 7) {\n                    VS2_GATE_E_ENTITY_MOVE_LOGGER.info(\n                        "GATE_E_PHASE201_WALK_MOVE_CALLER player_tick={} mover={} requested={},{},{} delta={},{},{} callers={} fixture_only=true read_only=true",\n                        self.tickCount, String.valueOf(type), requested.x, requested.y, requested.z,\n                        self.getDeltaMovement().x, self.getDeltaMovement().y, self.getDeltaMovement().z,\n                        vs2$walkMoveCallerSummary());\n                }\n            } catch (NumberFormatException ignored) {\n            }\n        }\n'''
if "GATE_E_PHASE201_WALK_MOVE_CALLER" not in source:
    if source.count(log_anchor) != 1:
        raise SystemExit("Phase 201 expected one post-Phase186 Entity.move HEAD log anchor")
    source = source.replace(log_anchor, log_insert, 1)

required = [
    "GATE_E_PHASE201_WALK_MOVE_CALLER",
    "vs2$walkMoveCallerSummary()",
    "vs2.productionFixtureWalkStartTick",
    "fixture_only=true read_only=true",
    '@Inject(method = "move", at = @At("HEAD"), require = 0)',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 201 lost walk move-caller anchors: " + ", ".join(missing))

for forbidden in [
    "setPos(", "setDeltaMovement(", ".teleport(", "setBlock(", "setSchedule(",
    "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in source:
        raise SystemExit("Phase 201 introduced forbidden mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
print("Phase 201: traces bounded-walk Entity.move caller boundary read-only; no gameplay or physics mutation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase202.py")), run_name="__main__")

# Production-world #526 proves the fixed 14-attempt fixture cutoff is now too early after the
# native-frame lease hardening: all fourteen attempts finish before Create publishes any genuine
# ContraptionColliderClient contact application, leaving baseline_captured=false and broadphase=false.
# Keep the historical 32-attempt safety ceiling while native contact is absent.
#
# Production-world #539 then proved that testing only whether the global Phase170 application property
# exists is stale-state sensitive: an earlier native application can leave the property populated even
# though the current fixture frame has contact_now=false, causing acquisition to stop and the stationary
# player to be left behind by the moving carriage. Treat only a current-tick native Create application
# as the acquisition boundary. If native contact disappears again, fixture acquisition may continue up
# to the existing 32-attempt ceiling; walk readiness remains unassisted only on exact native-contact
# ticks or after that ceiling. Harness-only: no player motion, collision response, carry vector,
# train/world state, or VS2 physics behavior is changed.
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
probe_source = client_probe.read_text(encoding="utf-8")
old_acquire = "fixtureContactAcquireTicks < 32"
old_unassisted = "fixtureContactAcquireTicks >= 32"
new_acquire = '''(fixtureContactAcquireTicks < 32
            && !Integer.toString(player.tickCount).equals(
                System.getProperty("vs2.phase170NativeContactApplicationTick")))'''
new_unassisted = '''(fixtureContactAcquireTicks >= 32
            || Integer.toString(player.tickCount).equals(
                System.getProperty("vs2.phase170NativeContactApplicationTick")))'''
acquire_count = probe_source.count(old_acquire)
unassisted_count = probe_source.count(old_unassisted)
if acquire_count < 2 or unassisted_count < 2:
    raise SystemExit(
        f"Phase 201 expected cumulative 32-attempt fixture boundaries, found acquire={acquire_count} unassisted={unassisted_count}"
    )
probe_source = probe_source.replace(old_acquire, new_acquire)
probe_source = probe_source.replace(old_unassisted, new_unassisted)
required_fixture = [
    "vs2.phase170NativeContactApplicationTick",
    "Integer.toString(player.tickCount).equals",
    "fixtureContactAcquireTicks < 32",
    "fixtureContactAcquireTicks >= 32",
]
missing_fixture = [token for token in required_fixture if token not in probe_source]
if missing_fixture:
    raise SystemExit("Phase 201 lost tick-fresh native-contact fixture anchors: " + ", ".join(missing_fixture))
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in new_acquire + new_unassisted:
        raise SystemExit("Phase 201 fixture-boundary alignment introduced forbidden gameplay mutation")
client_probe.write_text(probe_source, encoding="utf-8")
print("Phase 201: fixture acquisition ignores stale native-contact state and stops only on tick-fresh Create contact or the 32-attempt ceiling")
