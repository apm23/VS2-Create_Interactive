#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_lease = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContactLeaseTrace.java"
source = client_probe.read_text(encoding="utf-8")
lease_source = contact_lease.read_text(encoding="utf-8")

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
old_prefix = '''                        boolean phase194DirectNativeCandidate = !phase154WalkStarted
                            && phase194ProvenNativeCarryHealth'''
new_prefix = '''                        boolean phase203CarryHealthCandidate = !phase154WalkStarted
                            && phase154SupportNow
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround()
                            && phase194ProvenNativeCarryHealth'''
if source.count(old_prefix) != 1:
    raise SystemExit("Phase 203 expected one Phase194 direct-native candidate prefix")
source = source.replace(old_prefix, new_prefix, 1)
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
            int vs2$maxGraceTicks = vs2$airborneNativeLease ? 20 : 2;

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

required = [
    "phase203CarryHealthCandidate",
    "phase154SupportNow",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase194ProvenNativeCarryHealth",
    "fixtureContactAcquireTicks >= 32",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkAge == 1",
    "phase185NativeApplicationFresh",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 203 lost bounded carry-health walk-start anchors: " + ", ".join(missing))

lease_required = [
    "vs2$airborneNativeLease",
    "vs2$nativeApplicationAge >= 0 && vs2$nativeApplicationAge <= 20",
    "vs2$maxGraceTicks = vs2$airborneNativeLease ? 20 : 2",
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
    raise SystemExit("Phase 203 lost bounded airborne native Create lease anchors: " + ", ".join(lease_missing))

inserted = new_prefix + consumer_replacement + lease_new + lease_log_new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(", "method.invoke(lease, Integer.valueOf(0))",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 203 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
contact_lease.write_text(lease_source, encoding="utf-8")
print("Phase 203: composes after tick-fresh acquisition rewrite and keeps bounded Create jump lease")
