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
#
# Production-world #613 proves this tick-fresh rewrite must not relax Phase194/203's separate hard
# 32-tick walk-start acquisition invariant. The old global >=32 replacement also rewrote
# (!productionSmokeFixture || fixtureContactAcquireTicks >= 32), allowing exact native contact to
# start locomotion around tick 18 and contaminate the standing-carry verifier. Protect that existing
# walk gate while rewriting the acquisition/unassisted boundaries, then restore it unchanged.
#
# Production-world #614 isolates the remaining harness loop: after one genuine current-tick Phase170
# native contact, an intermittent following tick can make Phase119's test-only nearest-collider retarget
# eligible again before the hard 32-tick standing-acquisition gate. Latch only that current-pass exact
# native contact in this fresh client probe instance, then freeze further fixture retarget mutation while
# passive acquisition accounting continues to 32. This changes only disposable smoke-fixture ownership;
# Create carry/collision and VS2 physics remain untouched.
#
# Production-world #619 proved the latch accidentally stopped the acquisition counter itself: the first
# native application arrived at tick 14 after attempt 11, after which no more acquire attempts were
# published, so the mandatory >=32 walk gate became unreachable even though real native carry later
# stabilized on carriage 2 at ticks 56-58. Keep the latch only on the retarget mutation. Acquisition
# accounting must continue to the existing 32-attempt ceiling so the hard walk gate can actually open.
#
# Production-world #647 proves the remaining latch must be carriage-scoped. A native application from
# carriage 8 at tick 14 set the old global boolean, while the fixture's active nearest-collider candidate
# moved to carriage 10 on the following ticks. The global latch then froze Phase119 retargeting for the
# wrong carriage, so baseline capture never occurred and the moving train outran the fixture. Preserve
# the anti-churn latch, but only suppress retargeting when the currently examined carriage is the exact
# native owner that established the latch. Harness ownership only; no player/carry/physics mutation.
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
hard_walk_gate = "(!productionSmokeFixture || fixtureContactAcquireTicks >= 32)"
protected_walk_gate = "(!productionSmokeFixture || VS2_PHASE201_HARD_WALK_ACQUIRE)"
hard_walk_gate_count = probe_source.count(hard_walk_gate)
if hard_walk_gate_count < 1:
    raise SystemExit("Phase 201 expected the Phase194/203 hard 32-tick walk acquisition gate")
probe_source = probe_source.replace(hard_walk_gate, protected_walk_gate)
acquire_count = probe_source.count(old_acquire)
unassisted_count = probe_source.count(old_unassisted)
if acquire_count < 2 or unassisted_count < 1:
    raise SystemExit(
        f"Phase 201 expected cumulative fixture boundaries after protecting walk gate, found acquire={acquire_count} unassisted={unassisted_count}"
    )
probe_source = probe_source.replace(old_acquire, new_acquire)
probe_source = probe_source.replace(old_unassisted, new_unassisted)
probe_source = probe_source.replace(protected_walk_gate, hard_walk_gate)
if probe_source.count(hard_walk_gate) != hard_walk_gate_count:
    raise SystemExit("Phase 201 failed to preserve every hard 32-tick walk acquisition gate")

class_anchor = "public final class GateEClientProbe implements ClientModInitializer {\n"
field_insert = class_anchor + (
    "    private static boolean vs2Phase201NativeAcquired;\n"
    "    private static int vs2Phase201NativeAcquiredCarriageId = Integer.MIN_VALUE;\n"
)
if "private static boolean vs2Phase201NativeAcquired;" not in probe_source:
    if probe_source.count(class_anchor) != 1:
        raise SystemExit("Phase 201 expected one GateE client class declaration for native-acquisition latch")
    probe_source = probe_source.replace(class_anchor, field_insert, 1)
else:
    existing_field = "    private static boolean vs2Phase201NativeAcquired;\n"
    if "vs2Phase201NativeAcquiredCarriageId" not in probe_source:
        if probe_source.count(existing_field) != 1:
            raise SystemExit("Phase 201 expected one existing native-acquisition latch field")
        probe_source = probe_source.replace(existing_field, field_insert[len(class_anchor):], 1)

player_anchor = "            var player = client.player;\n"
latch_block = player_anchor + '''            if (Boolean.getBoolean("vs2.productionSmokeFixture")
                    && Integer.toString(player.tickCount).equals(
                        System.getProperty("vs2.phase170NativeContactApplicationTick"))) {
                vs2Phase201NativeAcquired = true;
                try {
                    vs2Phase201NativeAcquiredCarriageId = Integer.parseInt(System.getProperty(
                        "vs2.phase170NativeContactApplicationCarriageId", "-2147483648"));
                } catch (NumberFormatException ignored) {
                    vs2Phase201NativeAcquiredCarriageId = Integer.MIN_VALUE;
                }
            }
'''
if "vs2Phase201NativeAcquired = true;" not in probe_source:
    if probe_source.count(player_anchor) != 1:
        raise SystemExit("Phase 201 expected one GateE client player acquisition anchor")
    probe_source = probe_source.replace(player_anchor, latch_block, 1)
else:
    old_latch = player_anchor + '''            if (Boolean.getBoolean("vs2.productionSmokeFixture")
                    && Integer.toString(player.tickCount).equals(
                        System.getProperty("vs2.phase170NativeContactApplicationTick"))) {
                vs2Phase201NativeAcquired = true;
            }
'''
    if probe_source.count(old_latch) != 1:
        raise SystemExit("Phase 201 expected one existing global native-acquisition latch block")
    probe_source = probe_source.replace(old_latch, latch_block, 1)

latched_acquire = '''(fixtureContactAcquireTicks < 32)'''
latched_unassisted = '''(fixtureContactAcquireTicks >= 32
            || vs2Phase201NativeAcquired)'''
new_acquire_count = probe_source.count(new_acquire)
new_unassisted_count = probe_source.count(new_unassisted)
if new_acquire_count < 2 or new_unassisted_count < 1:
    raise SystemExit(
        f"Phase 201 expected tick-fresh boundaries before latching, found acquire={new_acquire_count} unassisted={new_unassisted_count}"
    )
probe_source = probe_source.replace(new_acquire, latched_acquire)
probe_source = probe_source.replace(new_unassisted, latched_unassisted)

retarget_old = "best < 0 && productionSmokeFixture && colliderCount > 0"
retarget_previous = "best < 0 && productionSmokeFixture && !vs2Phase201NativeAcquired && colliderCount > 0"
retarget_new = "best < 0 && productionSmokeFixture && vs2Phase201NativeAcquiredCarriageId != carriage.getId() && colliderCount > 0"
if retarget_new not in probe_source:
    if probe_source.count(retarget_previous) == 1:
        probe_source = probe_source.replace(retarget_previous, retarget_new, 1)
    elif probe_source.count(retarget_old) == 1:
        probe_source = probe_source.replace(retarget_old, retarget_new, 1)
    else:
        raise SystemExit("Phase 201 expected one Phase119 fixture nearest-collider retarget boundary")

required_fixture = [
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "Integer.toString(player.tickCount).equals",
    "private static boolean vs2Phase201NativeAcquired;",
    "private static int vs2Phase201NativeAcquiredCarriageId = Integer.MIN_VALUE;",
    "vs2Phase201NativeAcquired = true;",
    "vs2Phase201NativeAcquiredCarriageId = Integer.parseInt",
    "fixtureContactAcquireTicks < 32",
    "fixtureContactAcquireTicks >= 32",
    "vs2Phase201NativeAcquiredCarriageId != carriage.getId() && colliderCount > 0",
    hard_walk_gate,
]
missing_fixture = [token for token in required_fixture if token not in probe_source]
if missing_fixture:
    raise SystemExit("Phase 201 lost carriage-scoped native-contact latch anchors: " + ", ".join(missing_fixture))
if "fixtureContactAcquireTicks < 32\n            && !vs2Phase201NativeAcquired" in probe_source:
    raise SystemExit("Phase 201 native latch still blocks passive acquisition accounting")
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in latched_acquire + latched_unassisted + retarget_new + latch_block:
        raise SystemExit("Phase 201 fixture-boundary latch introduced forbidden gameplay mutation")
client_probe.write_text(probe_source, encoding="utf-8")
print("Phase 201: native latch freezes retarget only for the exact native-owning carriage while passive acquisition accounting reaches the hard walk gate")
