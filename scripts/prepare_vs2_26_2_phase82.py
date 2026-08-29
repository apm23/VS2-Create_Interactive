#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 104 proved Phase 81 reaches the physically supporting sibling carriage,
# but the workflow exits on the first GATE_E_CLIENT_CARRY_DELTA frame. On that
# first frame the new carriage has prev == now, so Create's contact-point motion
# is still zero. Delay only the read-only Phase 71 completion marker by four
# LocalPlayer ticks so the existing Phase 81 harness replay gets subsequent
# client frames. This changes CI observation timing only.
field_anchor = '''    private static boolean carryDeltaReported;\n'''
field_insert = '''    private static boolean carryDeltaReported;\n    private static int carryBaselinePlayerTick = Integer.MIN_VALUE;\n'''
if "carryBaselinePlayerTick" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 82 could not find carry delta field anchor")
    source = source.replace(field_anchor, field_insert, 1)

capture_anchor = '''                carryBaselineCaptured = true;\n                carryPlayerX = player.getX();'''
capture_insert = '''                carryBaselineCaptured = true;\n                carryBaselinePlayerTick = player.tickCount;\n                carryPlayerX = player.getX();'''
if "carryBaselinePlayerTick = player.tickCount;" not in source:
    if capture_anchor not in source:
        raise SystemExit("Phase 82 could not find carry baseline capture anchor")
    source = source.replace(capture_anchor, capture_insert, 1)

motion_anchor = '''                if (carriageD2 > 0.01) {\n'''
motion_replacement = '''                if (carriageD2 > 0.01 && player.tickCount >= carryBaselinePlayerTick + 4) {\n'''
if motion_anchor not in source:
    raise SystemExit("Phase 82 could not find Phase 71 carry delta threshold")
source = source.replace(motion_anchor, motion_replacement, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 82: delayed only the Phase 71 carry-delta completion marker by four client ticks so Phase 81 can observe post-motion frames; CI timing only")
