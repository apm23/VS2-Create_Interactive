#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #18 proved the settled vanilla client.hitResult still reports MISS
# even after the smoke camera was already aimed straight down for a later frame. Before
# attempting any use/place mutation, compare that vanilla MISS against the carriage
# entity's world-space AABB using the same eye ray. This is read-only geometry telemetry:
# no inventory, interaction manager, contraption state, player motion, or physics change.
anchor = '''                                        LOGGER.info(
                                            "GATE_F_INTERACTION_TARGET_SETTLED carriage_id={} player_tick={} hit_type={} hit_location={},{},{} detail={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(),
                                            settledHitLocation.x, settledHitLocation.y, settledHitLocation.z, settledDetail);
                                    }'''
replacement = '''                                        LOGGER.info(
                                            "GATE_F_INTERACTION_TARGET_SETTLED carriage_id={} player_tick={} hit_type={} hit_location={},{},{} detail={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(),
                                            settledHitLocation.x, settledHitLocation.y, settledHitLocation.z, settledDetail);

                                        net.minecraft.world.phys.Vec3 interactionRayStart = player.getEyePosition();
                                        net.minecraft.world.phys.Vec3 interactionRayEnd = interactionRayStart.add(
                                            player.getViewVector(1.0F).scale(5.0D));
                                        net.minecraft.world.phys.AABB carriageInteractionBounds = carriage.getBoundingBox();
                                        java.util.Optional<net.minecraft.world.phys.Vec3> carriageEnvelopeHit =
                                            carriageInteractionBounds.clip(interactionRayStart, interactionRayEnd);
                                        String carriageEnvelopeLocation = carriageEnvelopeHit
                                            .map(hit -> hit.x + "," + hit.y + "," + hit.z)
                                            .orElse("none");
                                        LOGGER.info(
                                            "GATE_F_CARRIAGE_RAY_ENVELOPE carriage_id={} player_tick={} vanilla_hit_type={} envelope_hit={} ray_start={},{},{} ray_end={},{},{} carriage_aabb={} envelope_location={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(), carriageEnvelopeHit.isPresent(),
                                            interactionRayStart.x, interactionRayStart.y, interactionRayStart.z,
                                            interactionRayEnd.x, interactionRayEnd.y, interactionRayEnd.z,
                                            carriageInteractionBounds, carriageEnvelopeLocation);
                                    }'''

if "GATE_F_CARRIAGE_RAY_ENVELOPE" not in source:
    if anchor not in source:
        raise SystemExit("Phase 90 could not find Phase 89 settled-target anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CARRIAGE_RAY_ENVELOPE',
    'carriage.getBoundingBox()',
    'carriageInteractionBounds.clip(interactionRayStart, interactionRayEnd)',
    'player.getEyePosition()',
    'player.getViewVector(1.0F).scale(5.0D)',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 90 lost carriage ray-envelope anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 90: compared settled vanilla MISS against carriage world-space ray envelope; read-only geometry telemetry")

# Phase 91 refines the broad carriage-envelope result into exact contraption-local
# block occupancy along the same eye ray. Keep it chained here so every workflow that
# already reaches Phase 90 receives the stronger read-only interaction evidence.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase91.py")), run_name="__main__")
