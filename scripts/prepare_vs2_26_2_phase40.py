#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# Phase 40 is intentionally verification-only. Phase 39 proved that the exact
# Create Fly 6.0.9-1 runtime can coexist with the ported VS2 core. Freeze that
# baseline before behavior work so later phases cannot silently swap Create or
# reactivate stale 1.21.x compatibility mixins.
build = (ROOT / "fabric/build.gradle").read_text(encoding="utf-8")
expected = 'runtimeOnly("maven.modrinth:dKvj0eNn:phlsMPgT")'
if build.count(expected) != 1:
    raise SystemExit(f"Expected exactly one pinned Create Fly runtime dependency, found {build.count(expected)}")

mixins_path = ROOT / "fabric/src/main/resources/valkyrienskies-fabric.mixins.json"
data = json.loads(mixins_path.read_text(encoding="utf-8"))
compat = [entry for key in ("mixins", "client") for entry in data.get(key, []) if entry.startswith("compat.")]
if compat:
    raise SystemExit(f"Legacy third-party compat mixins unexpectedly active before behavior work: {compat}")

print("Verified pinned Create Fly runtime baseline and isolated VS2 core mixin set for repeat integration smoke")
