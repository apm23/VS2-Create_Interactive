#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #223 proved the old Phase101 arm-request guard still attaches to an
# inactive duplicate interaction site: the executed settled-ray entrypoint logged
# target_match_ready=true, but no ARM_REQUEST marker followed. Bind the request directly
# to the exact readiness_source=create_native_ray_settled LOGGER site that executed in #223.
# This only publishes the same-JVM fixture handshake flag; it does not move the player,
# mutate a contraption/world cell, alter inventory, train state, collision, or VS2 physics.
entry_anchor = '''                                                LOGGER.info(
                                                    "GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT carriage_id={} player_tick={} exact={} target_match_ready={} readiness_source=create_native_ray_settled",
                                                    carriage.getId(), player.tickCount, settledExactNativeRightClickEntrypoint,
                                                    settledExactNativeRightClickEntrypoint && settledCreateNativeRayReady);'''
entry_insert = entry_anchor + '''
                                                if (productionSmokeFixture
                                                        && settledCreateNativeRayReady
                                                        && settledExactNativeRightClickEntrypoint
                                                        && !Boolean.getBoolean("vs2.productionHeldBlockServerArmRequested")) {
                                                    System.setProperty("vs2.productionHeldBlockServerArmRequested", "true");
                                                    LOGGER.info("GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST carriage_id={} player_tick={} requested=true fixture_only=true readiness_source=executed_settled_native_ray",
                                                        carriage.getId(), player.tickCount);
                                                }'''
if "readiness_source=executed_settled_native_ray" not in source:
    if entry_anchor not in source:
        raise SystemExit("Phase 142 could not find executed settled native-ray entrypoint log")
    source = source.replace(entry_anchor, entry_insert, 1)

# Keep the later legacy handshake guard non-blocking if it exists. The new executed-site
# request above is authoritative; the property check makes any duplicate request impossible.
old = "productionSmokeFixture && player.tickCount >= 30"
region_start = source.find("GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST")
region_end = source.find("GATE_F_CONTRAPTION_MUTATION_SURFACE", region_start)
if region_start >= 0 and region_end > region_start:
    region = source[region_start:region_end]
    region = region.replace(old, "productionSmokeFixture")
    region = region.replace(
        "productionSmokeFixture\n                                                        && player.tickCount >= 30",
        "productionSmokeFixture",
    )
    source = source[:region_start] + region + source[region_end:]

required = [
    "readiness_source=executed_settled_native_ray",
    "vs2.productionHeldBlockServerArmRequested",
    "GATE_F_SERVER_HELD_BLOCK_ARM_REQUEST",
    "GATE_F_SERVER_HELD_BLOCK_ARM_WAIT",
    "GATE_F_PHASE138_NATIVE_HELD_BLOCK_DISPATCH",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 142 lost executed-ray handshake anchors: " + ", ".join(missing))

for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in entry_insert:
        raise SystemExit("Phase 142 found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 142: arms held-block request directly at the executed settled native-ray entrypoint")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase143.py")), run_name="__main__")
