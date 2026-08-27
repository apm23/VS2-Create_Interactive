#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/build.gradle"
s = p.read_text(encoding="utf-8")

# Architectury Loom injects the configured default refmap name into Fabric mixin
# configs for development launches. With no default configured, Loom 1.17 can
# inject an empty string, which Mixin then tries to parse as a resource and logs:
#   Invalid REFMAP JSON ... Expected BEGIN_OBJECT but was STRING
#   Reference map '' for valkyrienskies-fabric.mixins.json could not be read
#
# VS2 itself has historically used this exact Loom setting on its platform build.
# Restore that contract for the 26.2 Fabric port rather than shipping a dummy
# refmap or mutating the mixin JSON by hand.
anchor = '''loom {\n    accessWidenerPath = project(":common").loom.accessWidenerPath\n\n'''
replacement = '''loom {\n    accessWidenerPath = project(":common").loom.accessWidenerPath\n\n    mixin {\n        defaultRefmapName = "valkyrienskies-refmap.json"\n    }\n\n'''
if anchor not in s:
    raise SystemExit("Expected Fabric loom/accessWidener anchor not found")
if 'defaultRefmapName = "valkyrienskies-refmap.json"' in s:
    raise SystemExit("Fabric refmap configuration already present before Phase 35")
s = s.replace(anchor, replacement, 1)

p.write_text(s, encoding="utf-8")
print("Configured Fabric Loom to generate/use valkyrienskies-refmap.json instead of an empty development refmap")
