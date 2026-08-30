#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #344 proves Phase172's duplicate-native-carry fixture guard keeps the
# carriage id captured at walk start even after Phase156 legitimately rebases the active walk
# carriage. Tick 36 therefore applies active carriage 4 native motion and then sibling carriage
# 5 native motion; the measured 3.048444 local discontinuity exactly equals the second sibling
# motion. Keep the existing Phase172 hypothesis guard, but publish the newly accepted active
# carriage whenever Phase156 performs its already-validated strict sibling handoff. Fixture
# bookkeeping only: no vector, player movement, collision, train/world state, or VS2 physics.

old = '''                                phase154WalkCarriageId = phase154Carriage.getId();
                            }
                            boolean phase160PreviousReplayAccountingSeam'''
new = '''                                phase154WalkCarriageId = phase154Carriage.getId();
                                System.setProperty("vs2.phase172WalkActiveCarriageId", Integer.toString(phase154WalkCarriageId));
                                LOGGER.info(
                                    "GATE_E_PHASE176_ACTIVE_CARRIAGE_HANDOFF_SYNC player_tick={} active_carriage_id={} phase172_guard_updated=true fixture_only=true read_only_accounting=true",
                                    player.tickCount, phase154WalkCarriageId);
                            }
                            boolean phase160PreviousReplayAccountingSeam'''

if "GATE_E_PHASE176_ACTIVE_CARRIAGE_HANDOFF_SYNC" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 176 expected exactly one Phase156 accepted-handoff assignment, found {count}")
    source = source.replace(old, new, 1)

# Validate only durable semantic anchors. The exact historical Phase156 handoff predicate has
# been reformatted by later cumulative phases; requiring its old textual spelling is brittle and
# caused production-world #346 to stop during preparation before runtime.
required = [
    "GATE_E_PHASE156_WALK_SIBLING_HANDOFF",
    "phase154WalkCarriageId = phase154Carriage.getId()",
    "vs2.phase172WalkActiveCarriageId",
    "GATE_E_PHASE176_ACTIVE_CARRIAGE_HANDOFF_SYNC",
    "phase172_guard_updated=true",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 176 lost active-carriage handoff sync anchors: " + ", ".join(missing))

inserted = new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 176 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 176: keeps Phase172 duplicate-native-carry active carriage synchronized with validated Phase156 sibling handoffs")
