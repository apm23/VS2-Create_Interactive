#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/src/main/resources/fabric.mod.json"
t = p.read_text(encoding="utf-8")
old = '    "minecraft": "1.21.11",\n'
if old not in t:
    raise SystemExit("Expected Minecraft 1.21.11 dependency not found in fabric.mod.json")
t = t.replace(old, '    "minecraft": "26.2",\n', 1)
p.write_text(t, encoding="utf-8")
print("Migrated Fabric mod metadata dependency from Minecraft 1.21.11 to 26.2")
