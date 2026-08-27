#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# Voxy is an optional distant-LOD compatibility layer, not part of VS physics.
# Phase17 excludes its 1.21.x Java implementation from the 26.2 core gate;
# remove the two Kotlin call sites as well so optional compat cannot block core.

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/assembly/ShipAssembler.kt"
t = p.read_text(encoding="utf-8")
imp = "import org.valkyrienskies.mod.compat.voxy.VoxyLodRefresh\n"
if imp not in t:
    raise SystemExit("ShipAssembler Voxy import missing")
t = t.replace(imp, "", 1)
call = "        chunkPoses.forEach { VoxyLodRefresh.mark(level, it) }\n"
if call not in t:
    raise SystemExit("ShipAssembler Voxy refresh call missing")
t = t.replace(call, "", 1)
p.write_text(t, encoding="utf-8")

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/util/RelocationUtil.kt"
t = p.read_text(encoding="utf-8")
# This file is CRLF upstream; operate with splitlines-safe text replacements.
t = t.replace("import org.valkyrienskies.mod.compat.voxy.VoxyLodRefresh\n", "")
lines = t.splitlines()
filtered = []
removed = 0
for line in lines:
    if "VoxyLodRefresh.mark(" in line:
        removed += 1
        continue
    filtered.append(line)
if removed != 2:
    raise SystemExit(f"Expected two RelocationUtil Voxy calls, removed {removed}")
p.write_text("\n".join(filtered) + "\n", encoding="utf-8")

print("Removed optional Voxy LOD refresh hooks from the 26.2 physics-core compile gate")
