#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #227 proved that the readiness_source=create_native_ray_settled
# entrypoint exists at more than one generated site and the first textual occurrence is
# not necessarily the site that executes at runtime. Publish the same idempotent arm
# request after every identical settled-native-ray entrypoint instead of guessing one.
# The Boolean property guard makes the runtime request one-shot. This only publishes the
# same-JVM fixture handshake flag; it does not move the player, mutate a contraption/world
# cell, alter inventory, train state, collision, networking, or VS2 physics.
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

existing_runtime_markers = source.count("readiness_source=executed_settled_native_ray")
anchor_count = source.count(entry_anchor)
if existing_runtime_markers == 0:
    if anchor_count == 0:
        raise SystemExit("Phase 142 could not find any executed settled native-ray entrypoint logs")
    source = source.replace(entry_anchor, entry_insert)
    inserted_runtime_markers = source.count("readiness_source=executed_settled_native_ray")
    if inserted_runtime_markers != anchor_count:
        raise SystemExit(
            f"Phase 142 expected {anchor_count} executed-ray arm sites but produced {inserted_runtime_markers}"
        )
else:
    inserted_runtime_markers = existing_runtime_markers

# Keep the later legacy handshake guard non-blocking if it exists. The executed-site
# requests above are authoritative; the property check makes duplicate requests impossible.
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
print(f"Phase 142: armed held-block request at {inserted_runtime_markers} executed settled native-ray site(s)")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase143.py")), run_name="__main__")
