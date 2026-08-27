#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/build.gradle"
s = p.read_text(encoding="utf-8")

# Phase 48: the user's train test world serializes carriage content from both
# Steam 'n' Rails (railways:*) and Copycats+ (copycats:*). Add the exact 26.2
# CreateFly-compatible ports as runtime-only smoke dependencies before the
# world fixture is introduced, so failures remain attributable to mod runtime
# coexistence rather than save loading.
create_dep = '    runtimeOnly("maven.modrinth:dKvj0eNn:phlsMPgT") // Create Fly 26.2-rc-2-6.0.9-1\n'
railways_dep = '    runtimeOnly("maven.modrinth:f20AygJv:Z0KLlixa") // Steam n Rails 1.7.2-beta-3 for Create Fly 26.2\n'
copycats_dep = '    runtimeOnly("maven.modrinth:3yqe09Ii:BWKL0Sem") // Copycats+ CreateFly 3.0.7 mc26.2 conflict-fixed build\n'

if create_dep not in s:
    raise SystemExit("Pinned Create Fly runtime dependency missing before Phase 48")
if 'maven.modrinth:f20AygJv:Z0KLlixa' in s or 'maven.modrinth:3yqe09Ii:BWKL0Sem' in s:
    raise SystemExit("Phase 48 runtime dependencies already present")

s = s.replace(create_dep, create_dep + railways_dep + copycats_dep, 1)
p.write_text(s, encoding="utf-8")
print("Phase 48: added pinned Steam n Rails + Copycats+ CreateFly runtimes required by train test world")
