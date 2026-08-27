#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/feature/ai/goal/villagers/MixinSetWalkTargetFromBlockMemory.java"
s = p.read_text(encoding="utf-8")

old_method = 'method = "method_47101"'
new_method = 'method = "lambda$create$2"'

if s.count(old_method) != 1:
    raise SystemExit(f"Expected exactly one legacy SetWalkTargetFromBlockMemory target, found {s.count(old_method)}")
if new_method in s:
    raise SystemExit("Phase 49 target already present")

s = s.replace(old_method, new_method, 1)
s = s.replace('tick lambda ({@code method_47101})', 'tick lambda ({@code lambda$create$2})')
p.write_text(s, encoding="utf-8")

print("Phase 49: retargeted SetWalkTargetFromBlockMemory ship-position wrapper to MC 26.2 lambda$create$2")
