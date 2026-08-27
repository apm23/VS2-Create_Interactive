#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/build.gradle"
s = p.read_text(encoding="utf-8")

# Phase 39: introduce the exact Create Fly build selected for Minecraft 26.2 as
# a runtime-only integration gate. Keep VS2 source untouched in this phase so
# any failure is attributable to loader/mixin/API coexistence, not behavioral
# changes. Modrinth version phlsMPgT is Create Fly 26.2-rc-2-6.0.9-1 and is
# explicitly marked compatible with Minecraft 26.2, Fabric, client and server.
anchor = '    implementation("net.fabricmc:fabric-loader:${rootProject.fabric_loader_version}")\n'
insert = anchor + '    runtimeOnly("maven.modrinth:dKvj0eNn:phlsMPgT") // Create Fly 26.2-rc-2-6.0.9-1\n'
if anchor not in s:
    raise SystemExit("Expected Fabric loader dependency anchor not found")
if 'maven.modrinth:dKvj0eNn:phlsMPgT' in s:
    raise SystemExit("Create Fly runtime dependency already present before Phase 39")
s = s.replace(anchor, insert, 1)
p.write_text(s, encoding="utf-8")
print("Added Create Fly 26.2-rc-2-6.0.9-1 as isolated Fabric runtime integration dependency")
