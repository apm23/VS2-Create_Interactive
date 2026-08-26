#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"


def replace(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")

# Minecraft 26.2 must use Architectury Loom's no-remap plugin variant. The
# normal plugin still expects a mappings dependency even though the game is
# shipped unobfuscated.
replace(
    "build.gradle",
    'id "dev.architectury.loom" version "1.17.483" apply false',
    'id "dev.architectury.loom-no-remap" version "1.17.483" apply false',
)
replace(
    "build.gradle",
    '    apply plugin: "dev.architectury.loom"',
    '    apply plugin: "dev.architectury.loom-no-remap"',
)

# No-remap builds consume already-official/unobfuscated dependencies directly.
# Convert Loom remapping configurations to their ordinary Gradle equivalents.
for rel in ("common/build.gradle", "fabric/build.gradle"):
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    for old, new in (
        ("modImplementation", "implementation"),
        ("modApi", "api"),
        ("modCompileOnly", "compileOnly"),
        ("modRuntimeOnly", "runtimeOnly"),
    ):
        text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")

# Modern Shadow is required by Gradle 9. Keep shading, but stop relying on the
# obsolete John Rengelman 7.x plugin.
replace(
    "fabric/build.gradle",
    'id "com.github.johnrengelman.shadow" version "7.1.2"',
    'id "com.gradleup.shadow" version "9.6.1"',
)

# No-remap Architectury does not expose the old namedElements/remap output
# pipeline. Common code is already in the same official namespace, so consume
# the normal project output for compilation and shading.
replace(
    "fabric/build.gradle",
    '    common(project(path: ":common", configuration: "namedElements")) {',
    '    common(project(path: ":common")) {',
)
replace(
    "fabric/build.gradle",
    '    shadowCommon(project(path: ":common", configuration: "transformProductionFabric")) {',
    '    shadowCommon(project(path: ":common")) {',
)

# remapJar is invalid in a no-remap build. Make shadowJar the production jar.
p = ROOT / "fabric/build.gradle"
text = p.read_text(encoding="utf-8")
text = text.replace('    archiveClassifier.set "dev-shadow"', '    archiveClassifier.set null')
text, count = re.subn(
    r'\nremapJar \{\n.*?\n\}\n\njar \{',
    '\njar {',
    text,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"Expected exactly one remapJar block, found {count}")
p.write_text(text, encoding="utf-8")

print("Migrated VS2 build to Architectury Loom no-remap for Minecraft 26.2")
