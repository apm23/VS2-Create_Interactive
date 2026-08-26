#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "build.gradle"
text = p.read_text(encoding="utf-8")

replacements = {
    '        options.release = 21\n': '        options.release = 25\n',
    '            jvmTarget = "21"\n': '            jvmTarget = "25"\n',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"Expected JVM 21 declaration not found: {old.strip()}")
    text = text.replace(old, new)

# Guard against re-introducing Java/Kotlin 21 metadata in the common build.
if 'options.release = 21' in text or 'jvmTarget = "21"' in text or 'jvmToolchain(21)' in text:
    raise SystemExit("Stale JVM 21 build target remains")

p.write_text(text, encoding="utf-8")
print("Migrated remaining Java/Kotlin target metadata from JVM 21 to JVM 25")
