#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #95 proved valid direct train-frame carry (zero relative drift,
# contact + on-ground true) without a Phase85 replay in that particular run. The
# complete native interaction/placement-target telemetry pipeline was historically
# nested only under the Phase85 replay logger, so no native target could be published
# and the placement experiment never ran. Reuse that already-validated, test-only
# interaction observation block when the direct carry-delta proof is emitted too.
# This changes no carry vector, collision response, train state, inventory or world.
start_marker = '                                if (productionSmoke && explicitCarryCompat && client.hitResult != null) {'
start = source.find(start_marker)
if start < 0:
    raise SystemExit("Phase 112 could not find the fully instrumented Phase85 interaction block")

# Extract the full Java block with brace matching so all later Phase89..107 read-only
# native-ray/target-publication instrumentation comes along without duplicating it by hand.
brace_start = source.find('{', start)
depth = 0
end = None
for index in range(brace_start, len(source)):
    char = source[index]
    if char == '{':
        depth += 1
    elif char == '}':
        depth -= 1
        if depth == 0:
            end = index + 1
            break
if end is None:
    raise SystemExit("Phase 112 could not balance the Phase85 interaction block")
interaction_block = source[start:end]

# Insert immediately after the direct carry-delta LOGGER statement. That branch only
# executes after material carriage motion has already been measured; the existing
# interaction block retains all of its productionSmoke/explicitCarryCompat guards.
delta_marker = '"GATE_E_CLIENT_CARRY_DELTA carriage_id={} player_delta={},{},{} carriage_delta={},{},{} relative_drift={},{},{} drift_sq={} contact_now={} on_ground_now={}"'
delta_pos = source.find(delta_marker)
if delta_pos < 0:
    raise SystemExit("Phase 112 could not find direct carry-delta telemetry")
statement_end = source.find(');', delta_pos)
if statement_end < 0:
    raise SystemExit("Phase 112 could not find end of carry-delta LOGGER statement")
statement_end += 2

sentinel = 'GATE_F_DIRECT_CARRY_INTERACTION_PIPELINE'
if sentinel not in source:
    direct_block = '''\n                        LOGGER.info("GATE_F_DIRECT_CARRY_INTERACTION_PIPELINE carriage_id={} player_tick={} read_only=true", carriage.getId(), player.tickCount);\n''' + interaction_block
    source = source[:statement_end] + direct_block + source[statement_end:]

required = [
    sentinel,
    'GATE_F_CREATE_NATIVE_RAY_SETTLED',
    'GATE_F_NATIVE_PLACEMENT_TARGET_PUBLISHED',
    'GATE_F_NATIVE_RIGHT_CLICK_ENTRYPOINT',
    'GATE_E_CLIENT_CARRY_DELTA carriage_id={}',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 112 lost direct-carry interaction anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 112: reused the validated read-only native interaction pipeline on direct train-frame carry proof; no carry, collision, train, inventory, world, or physics mutation")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase113.py")), run_name="__main__")
