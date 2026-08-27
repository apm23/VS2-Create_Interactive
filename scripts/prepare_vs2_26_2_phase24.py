#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/src/main/resources/valkyrienskies-fabric.mixins.json"
data = json.loads(p.read_text(encoding="utf-8"))

# The 26.2 core/runtime gate intentionally excludes third-party compatibility
# source sets. Remove their mixin config entries in one pass so dedicated-server
# startup tests VS2 itself instead of failing one optional addon at a time.
for key in ("mixins", "client"):
    entries = list(data.get(key, []))
    data[key] = [entry for entry in entries if not entry.startswith("compat.")]

# Assert the core server mixins we actually need are still present.
required_core = {
    "entity.MixinContainerEntity",
    "feature.explosions.ClipContextMixin",
    "feature.fix_tp_ships_cross_dimension.MixinLevelChunk",
    "feature.shipyard_entities.MixinPersistentEntitySectionManager",
    "feature.water_in_ships_entity.MixinEntity",
}
remaining = set(data.get("mixins", []))
missing = sorted(required_core - remaining)
if missing:
    raise SystemExit(f"Core VS2 mixins unexpectedly missing after compat cleanup: {missing}")

p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("Removed optional third-party Fabric compat mixins while preserving VS2 core mixins")
