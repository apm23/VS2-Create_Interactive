#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/build.gradle"
s = p.read_text(encoding="utf-8")

# Phase 39: introduce the exact Create Fly build selected for Minecraft 26.2 as
# the pinned runtime integration gate. The thin compat mixins added later also
# compile against this exact same jar so their handler signatures can use Create's
# native collision types without copying/reimplementing them. Runtime ownership is
# unchanged: Create Fly remains the implementation used in-game.
anchor = '    implementation("net.fabricmc:fabric-loader:${rootProject.fabric_loader_version}")\n'
insert = anchor + '    compileOnly("maven.modrinth:dKvj0eNn:phlsMPgT") // exact Create Fly API for thin compat mixins\n    runtimeOnly("maven.modrinth:dKvj0eNn:phlsMPgT") // Create Fly 26.2-rc-2-6.0.9-1\n'
if anchor not in s:
    raise SystemExit("Expected Fabric loader dependency anchor not found")
if 'maven.modrinth:dKvj0eNn:phlsMPgT' in s:
    raise SystemExit("Create Fly dependency already present before Phase 39")
s = s.replace(anchor, insert, 1)
p.write_text(s, encoding="utf-8")
print("Added pinned Create Fly 26.2 runtime plus compile-only API for thin native compat mixins")
