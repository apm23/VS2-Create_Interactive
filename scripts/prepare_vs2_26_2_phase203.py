#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #549 proves standing carry itself is stable on carriage 10 at ticks 31-32,
# but the later Phase185 readiness gate remains permanently false because it requires a fresh
# native-contact sample long after that already-proven carry interval. Preserve the strict support,
# same-carriage and carry-health requirements, but let the direct-native candidate arm from the
# bounded Phase137 carry-health proof without additionally requiring the stale Phase185 readiness
# sample. The next-tick confirmation remains exact-native and same-carriage in Phase194, so a sibling
# handoff or missing Create application still rejects walk start. Fixture acceptance only: no player
# position/velocity, collision response, carry vector, train/world state, Create behavior or VS2
# physics mutation.
old = '''                        boolean phase194DirectNativeCandidate = !phase154WalkStarted
                            && phase194ProvenNativeCarryHealth;'''
new = '''                        boolean phase203CarryHealthCandidate = !phase154WalkStarted
                            && phase154SupportNow
                            && phase154Carriage.getId() == carryBaselineCarriageId
                            && collisionEligible && broadphaseOverlap && player.onGround()
                            && phase194ProvenNativeCarryHealth;
                        boolean phase194DirectNativeCandidate = phase203CarryHealthCandidate;'''
if source.count(old) != 1:
    raise SystemExit("Phase 203 expected one Phase194 direct-native candidate")
source = source.replace(old, new, 1)

required = [
    "phase203CarryHealthCandidate",
    "phase154SupportNow",
    "phase154Carriage.getId() == carryBaselineCarriageId",
    "collisionEligible && broadphaseOverlap && player.onGround()",
    "phase194ProvenNativeCarryHealth",
    "phase194ConfirmedDirectNativeReady",
    "phase194PendingWalkAge == 1",
    "phase185NativeApplicationFresh",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 203 lost bounded carry-health walk-start anchors: " + ", ".join(missing))

inserted = new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 203 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 203: arms direct-native walk from bounded proven carry health while retaining exact next-tick same-carriage confirmation")
