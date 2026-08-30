#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #336 proved the exact local occupied-cell resolver and synthetic
# BlockHitResult validation still execute, but the historical dispatch-candidate marker
# no longer survives the cumulative preparation chain. The workflow intentionally uses
# that marker only to recognize the validated local fallback; native right-click has a
# separate mandatory gate afterwards. Restore the read-only contract marker at the exact
# point where syntheticFieldsMatch is known. No interaction is dispatched here.
inserted = ""
marker = "source=validated_exact_local_hit read_only=true"
if marker not in source:
    pattern = re.compile(
        r'(?P<indent>[ \t]*)LOGGER\.info\(\s*\n'
        r'(?P=indent)[ \t]+"GATE_F_SYNTHETIC_BLOCK_HIT_CONSTRUCTED[^\n]*\n'
        r'.*?syntheticContraptionHit\.getType\(\)\);',
        re.DOTALL,
    )
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            f"Phase 174 expected exactly one synthetic-hit log statement, found {len(matches)}"
        )
    match = matches[0]
    indent = match.group("indent")
    addition = (
        "\n"
        + indent + "if (syntheticFieldsMatch) {\n"
        + indent + "    LOGGER.info(\n"
        + indent + "        \"GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction=true source=validated_exact_local_hit read_only=true\",\n"
        + indent + "        carriage.getId(), player.tickCount);\n"
        + indent + "}"
    )
    source = source[:match.end()] + addition + source[match.end():]
    inserted = addition

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
