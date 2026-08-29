#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #16 proved the smoke camera is being aimed down, but the existing
# target telemetry is sampled in the same carry callback immediately after setXRot.
# client.hitResult is prepared by Minecraft's picking path outside that assignment,
# so that same-callback sample can still describe the previous view frame. Capture
# the pitch before refreshing the fixture and add a second marker only after the
# camera was already down on entry to a later carry callback. This remains read-only
# telemetry: no use/place call, inventory mutation, train mutation, or physics change.
old = '''                                    if (productionSmokeFixture) {
                                        player.setXRot(90.0F);
                                        LOGGER.info(
                                            "GATE_F_INTERACTION_AIM_FIXTURE carriage_id={} player_tick={} pitch={}",
                                            carriage.getId(), player.tickCount, player.getXRot());
                                    }
                                    net.minecraft.world.phys.HitResult interactionHit = client.hitResult;'''
new = '''                                    float interactionPreAimPitch = player.getXRot();
                                    if (productionSmokeFixture) {
                                        player.setXRot(90.0F);
                                        LOGGER.info(
                                            "GATE_F_INTERACTION_AIM_FIXTURE carriage_id={} player_tick={} pitch={} pre_pitch={}",
                                            carriage.getId(), player.tickCount, player.getXRot(), interactionPreAimPitch);
                                    }
                                    net.minecraft.world.phys.HitResult interactionHit = client.hitResult;
                                    if (!productionSmokeFixture || Math.abs(interactionPreAimPitch - 90.0F) <= 0.01F) {
                                        net.minecraft.world.phys.Vec3 settledHitLocation = interactionHit.getLocation();
                                        String settledDetail = "generic";
                                        if (interactionHit instanceof net.minecraft.world.phys.BlockHitResult settledBlockHit) {
                                            settledDetail = "block_pos=" + settledBlockHit.getBlockPos().toShortString()
                                                + ";direction=" + settledBlockHit.getDirection()
                                                + ";inside=" + settledBlockHit.isInside();
                                        }
                                        LOGGER.info(
                                            "GATE_F_INTERACTION_TARGET_SETTLED carriage_id={} player_tick={} hit_type={} hit_location={},{},{} detail={}",
                                            carriage.getId(), player.tickCount, interactionHit.getType(),
                                            settledHitLocation.x, settledHitLocation.y, settledHitLocation.z, settledDetail);
                                    }'''

if "GATE_F_INTERACTION_TARGET_SETTLED" not in source:
    if old not in source:
        raise SystemExit("Phase 89 could not find Phase 88 aim fixture anchor")
    source = source.replace(old, new, 1)

required = [
    'interactionPreAimPitch',
    'GATE_F_INTERACTION_TARGET_SETTLED',
    'Math.abs(interactionPreAimPitch - 90.0F) <= 0.01F',
    'GATE_F_INTERACTION_TARGET',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 89 lost settled interaction-target anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 89: added settled-frame moving-train interaction target telemetry; read-only, no interaction mutation")
