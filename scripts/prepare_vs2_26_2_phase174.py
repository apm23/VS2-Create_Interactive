#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #336 proved the exact local occupied-cell resolver and synthetic
# BlockHitResult validation still execute, but the historical dispatch-candidate marker
# no longer survives the cumulative preparation chain. The workflow intentionally uses
# that marker only to recognize the validated local fallback; native right-click has a
# separate mandatory gate afterwards. Restore the read-only contract marker at the exact
# point where syntheticFieldsMatch is known. No interaction is dispatched here.
anchor = '''                                                            syntheticContraptionHit.isInside(), syntheticContraptionHit.getType());
                                                        roundtripState = "face=" + localFace
'''
replacement = '''                                                            syntheticContraptionHit.isInside(), syntheticContraptionHit.getType());
                                                        if (syntheticFieldsMatch) {
                                                            LOGGER.info(
                                                                "GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction=true source=validated_exact_local_hit read_only=true",
                                                                carriage.getId(), player.tickCount);
                                                        }
                                                        roundtripState = "face=" + localFace
'''
inserted = ""
if "source=validated_exact_local_hit read_only=true" not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Phase 174 expected exactly one validated synthetic-hit anchor")
    source = source.replace(anchor, replacement, 1)
    inserted = replacement

required = [
    "GATE_F_SYNTHETIC_BLOCK_HIT_CONSTRUCTED",
    "GATE_F_CONTRAPTION_EXACT_LOCAL_HIT",
    "GATE_F_INTERACTION_DISPATCH_CANDIDATE",
    "exact_handle_player_interaction=true",
    "source=validated_exact_local_hit",
    "syntheticFieldsMatch",
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 174 lost validated interaction fallback anchors: " + ", ".join(missing))

for forbidden in [
    "client.hitResult =", ".useItemOn(", ".useItem(", ".attack(",
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 174 introduced forbidden mutation/dispatch token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 174: restores validated exact-local interaction candidate telemetry contract; read-only only")
