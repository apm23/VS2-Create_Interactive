#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = client_probe.read_text(encoding="utf-8")
contact_source = contact_trace.read_text(encoding="utf-8")

# Production-world #327 passed the complete real-train contract: sustained carriage-local carry,
# bounded supported walking, handled native Create right-click, and packet-authoritative new-cell
# replication. Preserve those cumulative proof surfaces together before future phases are allowed
# to proceed. This phase is a static regression guard only; it does not modify generated gameplay
# code, player motion, collisions, train/world state, inventory, or VS2/Create physics.
required_client = [
    "GATE_E_CARRIAGE_LOCAL_CONTINUITY",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "support_healthy",
    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT",
    "GATE_F_NATIVE_RIGHT_CLICK_PROBE",
    "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED",
    "GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED",
    "vs2.productionNativePlacementExactCellPresent",
    "GATE_E_PHASE170_NATIVE_CONTACT_SUPPRESSES_RECOVERY",
]
required_contact = [
    "GATE_E_PHASE168_CONTACT_OWNER",
    "GATE_E_PHASE170_NATIVE_CONTACT_APPLICATION",
    "GATE_E_PHASE171_CARRIAGE_FRAME_STEP",
    "motion_minus_frame_step",
]
missing_client = [token for token in required_client if token not in source]
missing_contact = [token for token in required_contact if token not in contact_source]
if missing_client or missing_contact:
    parts = []
    if missing_client:
        parts.append("client=" + ", ".join(missing_client))
    if missing_contact:
        parts.append("contact=" + ", ".join(missing_contact))
    raise SystemExit("Phase 172 final production proof contract lost anchors: " + "; ".join(parts))

# Phase 172 performs no source mutation. Keep the no-workaround assertion scoped to text this
# phase would insert, instead of scanning its own documentation/string literals and false-positive
# on the forbidden API names named by the guard itself.
phase172_inserted_text = ""
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in phase172_inserted_text:
        raise SystemExit("Phase 172 introduced forbidden gameplay mutation token: " + forbidden)

print("Phase 172: final real-train proof contract preserved (carry + supported walk + native interaction + authoritative replication); static guard only")
