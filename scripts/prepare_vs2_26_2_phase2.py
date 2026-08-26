#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"


def replace(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")

# Minecraft 26.2 is distributed unobfuscated. There is no legacy Mojang mapping
# layer to request from Loom, so compile directly against the unobfuscated game.
replace(
    "build.gradle",
    '        // The following line declares the mojmap mappings, you may use other mappings as well\n        mappings loom.officialMojangMappings()\n',
    '        // Minecraft 26.2 is unobfuscated; no mapping layer is required.\n',
)

# The 1.21.11 fork explicitly forced Kotlin back to JDK 21 as a workaround for
# Kotlin 2.0.0. We already upgraded Kotlin to 2.4.10; remove that stale override
# so the compiler and Minecraft 26.2 both use Java 25 consistently.
p = ROOT / "build.gradle"
text = p.read_text(encoding="utf-8")
old = '''        // Pin the Kotlin compiler daemon to JDK 21. Without this, Gradle's
        // toolchain auto-detection can pick up a newer JDK (e.g. JDK 25) for
        // the Kotlin worker, and Kotlin 2.0.0's embedded IntelliJ JavaVersion
        // parser only handles versions up to ~24 — JDK 25 crashes compileKotlin
        // with "IllegalArgumentException: 25.0.1".
        jvmToolchain(21)
'''
if old in text:
    text = text.replace(old, '')
# Phase 1 inserts jvmToolchain(25) before compilerOptions. Assert there is no
# remaining JDK 21 toolchain so CI cannot silently compile mixed bytecode.
if "jvmToolchain(21)" in text:
    raise SystemExit("Stale Kotlin JDK 21 toolchain remains")
p.write_text(text, encoding="utf-8")

print("Applied Minecraft 26.2 unobfuscated mapping/toolchain migration")
