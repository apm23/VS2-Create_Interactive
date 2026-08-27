#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/feature/ai/goal/bees/MixinLocateHiveGoal.java"
s = p.read_text(encoding="utf-8")

# MC 26.2 no-remap runtime no longer exposes the old intermediary field name
# field_20375. BeeLocateHiveGoal remains a non-static inner class of Bee, so the
# outer Bee instance is carried by the synthetic this$0 field.
old = '''    @Shadow\n    @Final\n    Bee field_20375;\n'''
new = '''    @Shadow\n    @Final\n    Bee this$0;\n'''
if old not in s:
    raise SystemExit("Expected old BeeLocateHiveGoal shadow field not found")
s = s.replace(old, new, 1)
s = s.replace("this.field_20375.level()", "this.this$0.level()", 1)

p.write_text(s, encoding="utf-8")
print("Retargeted BeeLocateHiveGoal outer Bee shadow to MC 26.2 synthetic this$0")
