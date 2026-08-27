#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/feature/bed_fix/MixinLivingEntitySleep.java"
s = p.read_text(encoding="utf-8")

# In MC 1.21.11 stopSleeping delegated the wake-position work to a private
# synthetic helper named method_18404. In MC 26.2 Mojang inlines the same
# BedBlock.findStandUpPosition + setPos path directly inside stopSleeping.
old = '        method = "method_18404",\n'
new = '        method = "stopSleeping",\n'
if old not in s:
    raise SystemExit("Expected 1.21.11 synthetic wake helper target not found")
s = s.replace(old, new, 1)

# Keep the actual position-conversion operation and require=1 intact. If the
# invocation owner/signature changed too, runtime smoke will fail loudly rather
# than silently dropping the ship-bed wake correction.
p.write_text(s, encoding="utf-8")
print("Retargeted ship-bed wake position hook from 1.21.11 synthetic helper to MC 26.2 stopSleeping")
