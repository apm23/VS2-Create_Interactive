#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

aw = ROOT / "common/src/main/resources/valkyrienskies-common.accesswidener"
text = aw.read_text(encoding="utf-8")
old = "accessWidener\tv2\tnamed"
if old not in text:
    raise SystemExit("Expected named access widener header not found")
text = text.replace(old, "accessWidener\tv2\tofficial", 1)
aw.write_text(text, encoding="utf-8")

print("Migrated VS2 access widener namespace from named to official")
