#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# Phase 41 is the client-integration baseline gate. Server lifecycle is already
# repeatedly green through Phase 40, so preserve the exact Create runtime and
# verify that the Fabric client launch still contains VS2's client mixin config
# before running it under Xvfb in CI.
build = (ROOT / "fabric/build.gradle").read_text(encoding="utf-8")
expected = 'runtimeOnly("maven.modrinth:dKvj0eNn:phlsMPgT")'
if build.count(expected) != 1:
    raise SystemExit("Pinned Create Fly 6.0.9-1 runtime dependency changed before client smoke")

mixin_path = ROOT / "fabric/src/main/resources/valkyrienskies-fabric.mixins.json"
mixins = mixin_path.read_text(encoding="utf-8")
if '"client"' not in mixins:
    raise SystemExit("Fabric client mixin section missing before client smoke")

print("Verified Phase 41 pinned Create+VS2 client baseline for headless client smoke")
