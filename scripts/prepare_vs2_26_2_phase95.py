#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #28 proved the exact local block face transforms cleanly into a
# stable world face/normal while the exact hit point still roundtrips with zero error.
# Construct a synthetic BlockHitResult from that resolved geometry and immediately
# validate only its stored fields. Do NOT assign client.hitResult and do NOT dispatch
# useItemOn/useItem/attack or mutate inventory/world/contraption state.
anchor = '''                                                        roundtripState = "face=" + localFace
                                                            + ";world_face=" + worldFace
                                                            + ";world_normal=" + worldNormal.x + "," + worldNormal.y + "," + worldNormal.z
                                                            + ";world_hit=" + worldHit.x + "," + worldHit.y + "," + worldHit.z'''
replacement = '''                                                        net.minecraft.core.Direction syntheticDirection =
                                                            net.minecraft.core.Direction.valueOf(worldFace);
                                                        net.minecraft.world.phys.BlockHitResult syntheticContraptionHit =
                                                            new net.minecraft.world.phys.BlockHitResult(
                                                                worldHit, syntheticDirection, nearestCell, false);
                                                        boolean syntheticFieldsMatch =
                                                            syntheticContraptionHit.getType() == net.minecraft.world.phys.HitResult.Type.BLOCK
                                                            && syntheticContraptionHit.getBlockPos().equals(nearestCell)
                                                            && syntheticContraptionHit.getDirection() == syntheticDirection
                                                            && syntheticContraptionHit.getLocation().distanceToSqr(worldHit) <= 1.0e-24D
                                                            && !syntheticContraptionHit.isInside();
                                                        LOGGER.info(
                                                            "GATE_F_SYNTHETIC_BLOCK_HIT_CONSTRUCTED carriage_id={} player_tick={} fields_match={} cell={} world_face={} world_hit={},{},{} inside={} type={}",
                                                            carriage.getId(), player.tickCount, syntheticFieldsMatch,
                                                            syntheticContraptionHit.getBlockPos().toShortString(),
                                                            syntheticContraptionHit.getDirection(),
                                                            syntheticContraptionHit.getLocation().x,
                                                            syntheticContraptionHit.getLocation().y,
                                                            syntheticContraptionHit.getLocation().z,
                                                            syntheticContraptionHit.isInside(), syntheticContraptionHit.getType());
                                                        roundtripState = "face=" + localFace
                                                            + ";world_face=" + worldFace
                                                            + ";world_normal=" + worldNormal.x + "," + worldNormal.y + "," + worldNormal.z
                                                            + ";world_hit=" + worldHit.x + "," + worldHit.y + "," + worldHit.z'''

if "GATE_F_SYNTHETIC_BLOCK_HIT_CONSTRUCTED" not in source:
    if anchor not in source:
        raise SystemExit("Phase 95 could not find Phase 94 transformed-face anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_SYNTHETIC_BLOCK_HIT_CONSTRUCTED',
    'new net.minecraft.world.phys.BlockHitResult(',
    'syntheticContraptionHit.getBlockPos().equals(nearestCell)',
    'syntheticContraptionHit.getDirection() == syntheticDirection',
    'syntheticFieldsMatch',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 95 lost construct-only synthetic-hit anchors: " + ", ".join(missing))

for forbidden in [
    'client.hitResult = syntheticContraptionHit',
    '.useItemOn(',
    '.useItem(',
    '.attack(',
]:
    if forbidden in source:
        raise SystemExit("Phase 95 construct-only guard found forbidden interaction: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 95: constructed and field-validated synthetic moving-contraption BlockHitResult; no assignment or interaction dispatch")
