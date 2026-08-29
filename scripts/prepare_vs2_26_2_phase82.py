#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 106 proved delaying from the contact baseline is insufficient: train motion
# begins many client ticks later, so the old +4 condition is already satisfied on
# the first moving frame. Delay the read-only Phase 71 completion marker relative
# to the first *observed carriage motion* instead. This leaves the client alive for
# two additional LocalPlayer ticks so Create can populate prevPosition and Phase 81
# can evaluate a non-zero contact-point motion. CI observation timing only.
field_anchor = '''    private static boolean carryDeltaReported;\n'''
field_insert = '''    private static boolean carryDeltaReported;\n    private static int carryFirstMotionPlayerTick = Integer.MIN_VALUE;\n'''
if "carryFirstMotionPlayerTick" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 82 could not find carry delta field anchor")
    source = source.replace(field_anchor, field_insert, 1)

motion_anchor = '''                if (carriageD2 > 0.01) {\n                    double playerDx = player.getX() - carryPlayerX;'''
motion_replacement = '''                if (carriageD2 > 0.01 && carryFirstMotionPlayerTick == Integer.MIN_VALUE) {\n                    carryFirstMotionPlayerTick = player.tickCount;\n                    LOGGER.info(\n                        "GATE_E_PHASE82_FIRST_MOTION player_tick={} carriage_delta={},{},{}",\n                        player.tickCount, carriageDx, carriageDy, carriageDz);\n                }\n                if (carriageD2 > 0.01\n                    && carryFirstMotionPlayerTick != Integer.MIN_VALUE\n                    && player.tickCount >= carryFirstMotionPlayerTick + 2) {\n                    double playerDx = player.getX() - carryPlayerX;'''
if motion_anchor not in source:
    raise SystemExit("Phase 82 could not find Phase 71 carry delta threshold")
source = source.replace(motion_anchor, motion_replacement, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 82: delayed Phase 71 completion until two LocalPlayer ticks after first observed train motion; CI timing only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase83.py")), run_name="__main__")
