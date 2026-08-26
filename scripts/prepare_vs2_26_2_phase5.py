#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

p = ROOT / "fabric/build.gradle"
text = p.read_text(encoding="utf-8")

# Publishing integrations from the 1.21.11 project assume a remapJar task.
# Minecraft 26.2 uses the no-remap Loom plugin, so those integrations are not
# relevant to compile/smoke testing and break configuration before compilation.
for line in (
    '    id "com.matthewprenger.cursegradle"\n',
    '    id "com.modrinth.minotaur"\n',
    "apply from: '../gradle-scripts/publish-curseforge.gradle'\n",
):
    if line not in text:
        raise SystemExit(f"Expected publishing line not found: {line.strip()}")
    text = text.replace(line, '')

p.write_text(text, encoding="utf-8")
print("Disabled legacy CurseForge/Modrinth publishing configuration for 26.2 build harness")
