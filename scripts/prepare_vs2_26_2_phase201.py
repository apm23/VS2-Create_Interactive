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

# Production-world #504 proves one destructive fixture retarget still survives the previous
# 15-attempt cap: carriage 4 is perfectly local-stable through tick 19 with zero carry drift at
# tick 17, then the fixture jumps out of that frame at tick 22 before M1 locomotion can start.
# Stop one acquisition attempt earlier so the already-established native contact remains frozen.
# Harness-only: no position, velocity, carry, collision, train/world, Create, or VS2 physics mutation.
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
probe_source = client_probe.read_text(encoding="utf-8")
old_acquire = "fixtureContactAcquireTicks < 32"
old_unassisted = "fixtureContactAcquireTicks >= 32"
acquire_count = probe_source.count(old_acquire)
unassisted_count = probe_source.count(old_unassisted)
if acquire_count < 2 or unassisted_count < 2:
    raise SystemExit(
        f"Phase 201 expected cumulative 32-attempt fixture boundaries, found acquire={acquire_count} unassisted={unassisted_count}"
    )
probe_source = probe_source.replace(old_acquire, "fixtureContactAcquireTicks < 14")
probe_source = probe_source.replace(old_unassisted, "fixtureContactAcquireTicks >= 14")
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in "fixtureContactAcquireTicks < 14 fixtureContactAcquireTicks >= 14":
        raise SystemExit("Phase 201 fixture-boundary alignment introduced forbidden gameplay mutation")
client_probe.write_text(probe_source, encoding="utf-8")
print("Phase 201: stops fixture acquisition after attempt 14, before Run 504's remaining retarget boundary")
