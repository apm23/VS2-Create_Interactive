#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_lease = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContactLeaseTrace.java"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
source = client_probe.read_text(encoding="utf-8")
lease_source = contact_lease.read_text(encoding="utf-8")
fixture_source = fixture_input.read_text(encoding="utf-8")

# Production-world #549 proves standing carry itself is stable on carriage 10 at ticks 31-32,
# but the later Phase185 readiness gate remains permanently false because it requires a fresh
# native-contact sample long after that already-proven carry interval. Preserve the strict support,
# same-carriage and carry-health requirements, but let the direct-native candidate arm from the
# bounded Phase137 carry-health proof without additionally requiring the stale Phase185 readiness
# sample. The next-tick confirmation remains exact-native and same-carriage in Phase194, so a sibling
# handoff or missing Create application still rejects walk start. Fixture acceptance only: no player
# position/velocity, collision response, carry vector, train/world state, Create behavior or VS2
# physics mutation.
#
# Production-world #596/#597 stopped in cumulative prepare because Phase201 deliberately rewrites
# every 32-tick acquisition expression into its tick-fresh-native equivalent after Phase194, so an
# exact whole-statement Phase194 anchor is not composition-stable. Rewrite only the unique candidate
# prefix and preserve whichever existing acquisition expression follows it, then alias the stricter
# Phase203 candidate before the immediate-ready consumer. Harness composition only.
#
# Production-world #678 proves the remaining blocker is fixture admission rather than moving-train
# carry: after the hard 32-attempt fixture acquisition boundary, carriage 2 supplies six consecutive
# grounded, broadphase, strict-support, exact native Create applications with zero carriage-local
# displacement, while Phase194's historical carry-health publication is absent and the walk never
# arms. Treat that direct unassisted exact-native same-carriage state as carry proof for this fixture
# branch only. Phase194's existing next-tick exact-native confirmation still rejects stale/sibling
# ownership. This changes admission accounting only; no player/train/collision/physics state.
#
# Production-world #679 then failed before Minecraft launch because the #678 rewrite first replaced
# the Phase194 candidate prefix and immediately tried to match the consumed pre-rewrite health+gate
# fragment a second time. Rewrite the complete candidate atomically instead. This is cumulative-prepare
# correctness only and leaves the intended fixture admission semantics unchanged.
old_candidate = '''                        boolean phase194DirectNativeCandidate = !phase154WalkStarted
                            && phase194ProvenNativeCarryHealth
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32);'''
new_candidate = '''                        boolean phase203DirectNativeCarryProof = productionSmokeFixture
                            && fixtureContactAcquireTicks >= 32
                            && phase81PhysicalSupport
                            && Integer.toString(player.tickCount).equals(System.getProperty(
                                "vs2.phase170NativeContactApplicationTick." + phase154Carriage.getId()));
                        boolean phase203CarryHealthCandidate = !phase154WalkStarted
                            && phase154SupportNow
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround()
                            && (phase194ProvenNativeCarryHealth || phase203DirectNativeCarryProof)
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 32 || phase185WalkReadyTicks >= 2);'''
if source.count(old_candidate) != 1:
    raise SystemExit("Phase 203 expected one complete Phase194 direct-native candidate")
source = source.replace(old_candidate, new_candidate, 1)

consumer_anchor = '''                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate'''
consumer_replacement = '''                        boolean phase194DirectNativeCandidate = phase203CarryHealthCandidate;
                        boolean phase194ImmediateHealthyNativeReady = phase194DirectNativeCandidate'''
if source.count(consumer_anchor) != 1:
    raise SystemExit("Phase 203 expected one Phase194 immediate-ready consumer")
source = source.replace(consumer_anchor, consumer_replacement, 1)

# Production-world #585 proves the next M1 boundary directly. The native jump executes through
# vanilla LocalPlayer (Entity.move applies +0.4199999869 Y), Create applies the exact carriage
# contact through tick 40, then its collidingEntities lease expires for the airborne player. The
# player remains in the correct moving reference frame but the native Create contact disappears
# during descent; it later reacquires a sibling carriage and the player passes through the train
# floor before landing on world Y=-60. Preserve Create's own already-existing contact lease at its
# expiry edge while airborne, but only for the exact carriage that itself published native contact
# within the preceding 20 ticks. We do not manufacture contact age 0, collision normals, movement,
# velocity or gravity: this only keeps Create's native contact/collision ownership alive across the
# bounded jump interval, analogous to the existing two-tick grounded lease bridge.
#
# Production-world #618 proves the same native-ownership boundary now fails while grounded before
# locomotion starts: exact same-carriage Create applications stop at tick 19, the native lease reaches
# age 3 at tick 23, and the existing two-tick grounded bridge expires at tick 24 while the player is
# still onGround and overlapping the same carriage. Keep that already-existing Create lease at age 2
# for the same bounded 20-tick recent-native window used by airborne continuity. This does not replay
# motion or synthesize velocity; it preserves Create's own collision/contact ownership only while the
# player remains grounded, overlapping, and recently owned by that exact carriage.
lease_old = '''            boolean graced = false;
            if (allowGrace
                    && Boolean.getBoolean("vs2.createCarryCompat")
                    && lease != null
                    && age >= 3
                    && vs2$leaseGraceTicks < 2
                    && player.onGround()
                    && self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox())) {'''
lease_new = '''            int vs2$nativeApplicationAge = Integer.MAX_VALUE;
            String vs2$nativeApplicationTick = System.getProperty(
                "vs2.phase170NativeContactApplicationTick." + self.getId());
            if (vs2$nativeApplicationTick != null) {
                try {
                    vs2$nativeApplicationAge = player.tickCount - Integer.parseInt(vs2$nativeApplicationTick);
                } catch (NumberFormatException ignored) {
                    vs2$nativeApplicationAge = Integer.MAX_VALUE;
                }
            }
            boolean vs2$airborneNativeLease = !player.onGround()
                && vs2$nativeApplicationAge >= 0 && vs2$nativeApplicationAge <= 20;
            boolean vs2$groundedNativeLease = player.onGround()
                && self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox())
                && vs2$nativeApplicationAge >= 0 && vs2$nativeApplicationAge <= 20;
            int vs2$maxGraceTicks = (vs2$airborneNativeLease || vs2$groundedNativeLease) ? 20 : 2;

            boolean graced = false;
            if (allowGrace
                    && Boolean.getBoolean("vs2.createCarryCompat")
                    && lease != null
                    && age >= 3
                    && vs2$leaseGraceTicks < vs2$maxGraceTicks
                    && (player.onGround() || vs2$airborneNativeLease)
                    && (vs2$airborneNativeLease
                        || self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox()))) {'''
if "vs2$airborneNativeLease" not in lease_source:
    if lease_source.count(lease_old) != 1:
        raise SystemExit("Phase 203 expected one Phase78 native Create lease boundary")
    lease_source = lease_source.replace(lease_old, lease_new, 1)
else:
    lease_previous = '''            boolean graced = false;
            if (allowGrace
                    && Boolean.getBoolean("vs2.createCarryCompat")
                    && lease != null
                    && age >= 3
                    && vs2$leaseGraceTicks < vs2$maxGraceTicks
                    && (player.onGround() || vs2$airborneNativeLease)
                    && self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox())) {'''
    if lease_source.count(lease_previous) != 1:
        raise SystemExit("Phase 203 expected one existing airborne lease overlap boundary")
    lease_source = lease_source.replace(lease_previous, '''            boolean graced = false;
            if (allowGrace
                    && Boolean.getBoolean("vs2.createCarryCompat")
                    && lease != null
                    && age >= 3
                    && vs2$leaseGraceTicks < vs2$maxGraceTicks
                    && (player.onGround() || vs2$airborneNativeLease)
                    && (vs2$airborneNativeLease
                        || self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox()))) {''', 1)

lease_log_old = '''                        "GATE_E_CREATE_CONTACT_LEASE_GRACE carriage_id={} player_tick={} grace_tick={}/2 native_create_lease=true bounded_bridge=true adapter_only=true",
                        self.getId(), player.tickCount, vs2$leaseGraceTicks);'''
lease_log_new = '''                        "GATE_E_CREATE_CONTACT_LEASE_GRACE carriage_id={} player_tick={} grace_tick={}/{} airborne={} native_application_age={} native_create_lease=true bounded_bridge=true adapter_only=true",
                        self.getId(), player.tickCount, vs2$leaseGraceTicks, vs2$maxGraceTicks,
                        vs2$airborneNativeLease, vs2$nativeApplicationAge);'''
if lease_log_old in lease_source:
    lease_source = lease_source.replace(lease_log_old, lease_log_new, 1)
elif "native_application_age={}" not in lease_source:
    raise SystemExit("Phase 203 could not update Create lease-grace accounting")

# Production-world #620 proves the post-walk fixture itself now burns the last stable support tick:
# forward sprint is confirmed at tick 61, tick 62 is still exactly carriage-local stable, but the
# old reverse window waits until tick 63. By then local Y has already fallen below the floor plane;
# reverse/strafe are subsequently accepted from vanilla horizontal velocity even though native Create
# applications have stopped and the player later lags a full carriage behind. Start reverse on the
# already-stable confirmation tick and allow strafe one tick after reverse begins. This changes only
# disposable KeyMapping timing; it does not move the player or alter Create/VS2 collision/carry.
backward_old = '''        int elapsed = self.tickCount - vs2$walkConfirmedTick;
        return elapsed >= 1 && elapsed <= 4;'''
backward_new = '''        int elapsed = self.tickCount - vs2$walkConfirmedTick;
        return elapsed >= 0 && elapsed <= 3;'''
strafe_old = '''        int elapsed = self.tickCount - vs2$backwardStartTick;
        return elapsed >= 2 && elapsed <= 5;'''
strafe_new = '''        int elapsed = self.tickCount - vs2$backwardStartTick;
        return elapsed >= 1 && elapsed <= 4;'''
if fixture_source.count(backward_old) != 1:
    raise SystemExit("Phase 203 expected one post-Phase202 reverse timing boundary")
if fixture_source.count(strafe_old) != 1:
    raise SystemExit("Phase 203 expected one post-Phase202 strafe timing boundary")
fixture_source = fixture_source.replace(backward_old, backward_new, 1)
fixture_source = fixture_source.replace(strafe_old, strafe_new, 1)

# Production-world #639 proves the jump request and first vanilla +Y SELF move are correct, but the
# headless fixture executes no further LocalPlayer.aiStep while airborne. The existing Phase198
# fallback is incorrectly gated by vs2$jumpArmReady(self), and Phase202 intentionally makes that
# admission predicate require self.onGround(). Once the jump starts, that gate becomes false on the
# next tick, freezing vanilla gravity at the apex while EntityDragger continues only frame translation.
# Keep the already-existing headless native-aiStep fallback alive after the jump has started until its
# natural landing observer completes. This invokes vanilla LocalPlayer.aiStep only; it does not write
# position/velocity, synthesize gravity/carry, or alter Create/VS2 collision.
jump_fallback_old = '''        boolean jumpWindow = vs2$jumpArmReady(self) && !vs2$jumpLandedLogged;'''
jump_fallback_new = '''        boolean jumpWindow = !vs2$jumpLandedLogged
            && (vs2$jumpArmReady(self) || vs2$jumpStartTick != Integer.MIN_VALUE);'''
if fixture_source.count(jump_fallback_old) != 1:
    raise SystemExit("Phase 203 expected one Phase198 headless jump-window boundary")
fixture_source = fixture_source.replace(jump_fallback_old, jump_fallback_new, 1)

required = [
    "phase203DirectNativeCarryProof",
    "phase203CarryHealthCandidate",
    "phase154SupportNow",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase194ProvenNativeCarryHealth || phase203DirectNativeCarryProof",
    "fixtureContactAcquireTicks >= 32",
    "vs2.phase170NativeContactApplicationTick.",
    "phase185WalkReadyTicks >= 2",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkAge == 1",
    "phase185NativeApplicationFresh",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 203 lost bounded carry-health walk-start anchors: " + ", ".join(missing))

lease_required = [
    "vs2$airborneNativeLease",
    "vs2$groundedNativeLease",
    "vs2$nativeApplicationAge >= 0 && vs2$nativeApplicationAge <= 20",
    "(vs2$airborneNativeLease || vs2$groundedNativeLease) ? 20 : 2",
    "vs2$leaseGraceTicks < vs2$maxGraceTicks",
    "player.onGround() || vs2$airborneNativeLease",
    "vs2$airborneNativeLease\n                        || self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox())",
    "method.invoke(lease, Integer.valueOf(2))",
    "native_application_age={}",
    "native_create_lease=true",
    "bounded_bridge=true",
]
lease_missing = [token for token in lease_required if token not in lease_source]
if lease_missing:
    raise SystemExit("Phase 203 lost bounded native Create lease anchors: " + ", ".join(lease_missing))

fixture_required = [
    "return elapsed >= 0 && elapsed <= 3;",
    "return elapsed >= 1 && elapsed <= 4;",
    "client.options.keyDown.setDown(backwardWindow)",
    "client.options.keyRight.setDown(strafeWindow)",
    "vs2$jumpArmReady(self) || vs2$jumpStartTick != Integer.MIN_VALUE",
]
fixture_missing = [token for token in fixture_required if token not in fixture_source]
if fixture_missing:
    raise SystemExit("Phase 203 lost compact native M1 fixture timing anchors: " + ", ".join(fixture_missing))

inserted = new_candidate + consumer_replacement + lease_new + lease_log_new + backward_new + strafe_new + jump_fallback_new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(", "method.invoke(lease, Integer.valueOf(0))",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 203 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
contact_lease.write_text(lease_source, encoding="utf-8")
fixture_input.write_text(fixture_source, encoding="utf-8")
print("Phase 203: preserves bounded Create contact ownership, admits unassisted exact-native carry proof for fixture locomotion, starts native reverse/strafe before fixture support decays, and keeps native aiStep alive through the headless jump arc")