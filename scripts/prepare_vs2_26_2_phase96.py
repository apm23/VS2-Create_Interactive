#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #30 proved a synthetic moving-contraption BlockHitResult can be
# constructed with matching type/cell/face/world-hit fields. Before allowing any
# interaction consumer to observe it, exercise only the MinecraftClient hitResult
# assignment seam under the dedicated production smoke fixture and restore the exact
# original reference immediately in the same callback. No frame, renderer, input,
# useItemOn/useItem/attack, inventory, world, contraption, position, or velocity state
# is allowed to observe/persist the synthetic result.
anchor = '''                                                        LOGGER.info(
                                                            "GATE_F_SYNTHETIC_BLOCK_HIT_CONSTRUCTED carriage_id={} player_tick={} fields_match={} cell={} world_face={} world_hit={},{},{} inside={} type={}",
                                                            carriage.getId(), player.tickCount, syntheticFieldsMatch,
                                                            syntheticContraptionHit.getBlockPos().toShortString(),
                                                            syntheticContraptionHit.getDirection(),
                                                            syntheticContraptionHit.getLocation().x,
                                                            syntheticContraptionHit.getLocation().y,
                                                            syntheticContraptionHit.getLocation().z,
                                                            syntheticContraptionHit.isInside(), syntheticContraptionHit.getType());'''
replacement = anchor + '''
                                                        if (productionSmokeFixture && syntheticFieldsMatch) {
                                                            net.minecraft.world.phys.HitResult originalClientHit = client.hitResult;
                                                            client.hitResult = syntheticContraptionHit;
                                                            boolean assignedIdentity = client.hitResult == syntheticContraptionHit;
                                                            client.hitResult = originalClientHit;
                                                            boolean restoredIdentity = client.hitResult == originalClientHit;
                                                            LOGGER.info(
                                                                "GATE_F_SYNTHETIC_HIT_EPHEMERAL_ASSIGN carriage_id={} player_tick={} assigned_identity={} restored_identity={} original_type={} synthetic_type={}",
                                                                carriage.getId(), player.tickCount, assignedIdentity, restoredIdentity,
                                                                originalClientHit == null ? "null" : originalClientHit.getType(),
                                                                syntheticContraptionHit.getType());
                                                        }'''

if "GATE_F_SYNTHETIC_HIT_EPHEMERAL_ASSIGN" not in source:
    if anchor not in source:
        raise SystemExit("Phase 96 could not find Phase 95 synthetic-hit log anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_SYNTHETIC_HIT_EPHEMERAL_ASSIGN',
    'client.hitResult = syntheticContraptionHit',
    'client.hitResult = originalClientHit',
    'assignedIdentity',
    'restoredIdentity',
    'productionSmokeFixture && syntheticFieldsMatch',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 96 lost ephemeral-assignment anchors: " + ", ".join(missing))

for forbidden in [
    '.useItemOn(',
    '.useItem(',
    '.attack(',
    'gameMode.use',
]:
    if forbidden in source:
        raise SystemExit("Phase 96 found forbidden interaction dispatch: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 96: assigned synthetic contraption hitResult only ephemerally and restored original identity in the same callback; no interaction dispatch")

# After the assign/restore seam is proven, inspect Create's public interaction-looking
# API surface without invoking anything. This keeps the next interaction bridge based
# on actual runtime capabilities rather than guessing a vanilla world-coordinate path.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase97.py")), run_name="__main__")
