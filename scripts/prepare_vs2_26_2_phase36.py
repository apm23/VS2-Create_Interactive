#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/build.gradle"
s = p.read_text(encoding="utf-8")

# Minecraft 26.2 is unobfuscated and the no-remap Loom variant does not need a
# legacy Mixin refmap. Phase 35 experimentally configured defaultRefmapName, but
# Loom 1.17 correctly warns that the legacy Mixin AP is disabled. Enabling that
# AP would reintroduce a mappings-dependent pipeline that 26.2 intentionally no
# longer uses. Remove the experimental mixin block and keep the official
# no-remap/in-place Mixin handling.
block = '''    mixin {\n        defaultRefmapName = "valkyrienskies-refmap.json"\n    }\n\n'''
if block not in s:
    raise SystemExit("Expected Phase 35 Fabric mixin refmap block not found")
s = s.replace(block, "", 1)

if "defaultRefmapName" in s or "useLegacyMixinAp" in s:
    raise SystemExit("Legacy/refmap Fabric Loom configuration remains after Phase 36")

p.write_text(s, encoding="utf-8")
print("Restored Minecraft 26.2 no-remap Mixin handling; no legacy refmap/AP required")
