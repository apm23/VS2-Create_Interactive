#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #341 proved the active carriage already applied native Create contact
# motion on walk tick 32, and Phase170 correctly observed that same-tick application, but
# the older Phase79/80 compatibility replay still ran through the Phase159 grace path.
# Suppress only that legacy replay when production-smoke fixture accounting proves any
# native ContraptionColliderClient contact application already occurred on the same player
# tick. This adds no movement vector and changes no production behavior outside the fixture.
old = '''                            && carryReplayPlayerTick != player.tickCount'''
new = '''                            && !(productionSmokeFixture
                                && Integer.toString(player.tickCount).equals(System.getProperty(
                                    "vs2.phase170NativeContactApplicationTick")))
                            && carryReplayPlayerTick != player.tickCount'''

if "phase175_same_tick_native_dedup" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 175 expected exactly one legacy carry replay tick guard, found {count}")
    source = source.replace(old, new, 1)
    marker_anchor = '''                            && carryReplayPlayerTick != player.tickCount'''
    marker_replacement = '''                            && carryReplayPlayerTick != player.tickCount // phase175_same_tick_native_dedup'''
    if source.count(marker_anchor) != 1:
        raise SystemExit("Phase 175 could not mark the deduplicated legacy replay guard")
    source = source.replace(marker_anchor, marker_replacement, 1)

# The Phase170 application log itself lives in the separate contact-trace mixin. The probe
# consumes the shared system-property seam, so validate only anchors that belong to this file.
required = [
    "GATE_E_PHASE80_REPLAY_MOTION",
    "vs2.phase170NativeContactApplicationTick",
    "productionSmokeFixture",
    "phase175_same_tick_native_dedup",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 175 lost legacy replay dedup anchors: " + ", ".join(missing))

# Phase175 modifies only a boolean eligibility predicate around the already-existing
# fixture replay. It must not introduce a new motion/world/train/physics mutation.
inserted = new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 175 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 175: suppresses legacy fixture carry replay after same-tick native Create contact application")
