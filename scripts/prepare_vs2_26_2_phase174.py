#!/usr/bin/env python3
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #336 proved the exact local occupied-cell resolver and synthetic
# BlockHitResult validation still execute, but the historical dispatch-candidate marker
# no longer survives the cumulative preparation chain. The workflow intentionally uses
# that marker only to recognize the validated local fallback; native right-click has a
# separate mandatory gate afterwards. Restore the read-only contract marker at every
# validated synthetic-hit site because the cumulative probe intentionally has two settled
# ray execution sites. No interaction is dispatched here.
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
    if not matches:
        raise SystemExit("Phase 174 found no synthetic-hit log statements")
    pieces = []
    cursor = 0
    additions = []
    for match in matches:
        indent = match.group("indent")
        addition = (
            "\n"
            + indent + "if (syntheticFieldsMatch) {\n"
            + indent + "    LOGGER.info(\n"
            + indent + "        \"GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction=true source=validated_exact_local_hit read_only=true\",\n"
            + indent + "        carriage.getId(), player.tickCount);\n"
            + indent + "}"
        )
        pieces.append(source[cursor:match.end()])
        pieces.append(addition)
        additions.append(addition)
        cursor = match.end()
    pieces.append(source[cursor:])
    source = "".join(pieces)
    inserted = "".join(additions)

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
print("Phase 174: restores validated exact-local interaction candidate telemetry contract at all synthetic-hit sites; read-only only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase175.py")), run_name="__main__")
