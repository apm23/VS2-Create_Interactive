#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# The Fabric-specific PersistentEntitySectionManager mixin duplicates getLevel/
# setLevel already supplied by the common shipyard_entities mixin. At runtime
# Mixin reports overwrite conflicts and skips the Fabric methods. Keep the
# common implementation, which also owns the important processUnloads/addEntity
# shipyard hooks, and remove only the redundant Fabric registration.
config_path = ROOT / "fabric/src/main/resources/valkyrienskies-fabric.mixins.json"
data = json.loads(config_path.read_text(encoding="utf-8"))
entry = "feature.shipyard_entities.MixinPersistentEntitySectionManager"
mixins = data.get("mixins", [])
if entry not in mixins:
    raise SystemExit("Expected duplicate Fabric PersistentEntitySectionManager mixin entry not found")
if mixins.count(entry) != 1:
    raise SystemExit("Unexpected duplicate count for Fabric PersistentEntitySectionManager mixin")
mixins.remove(entry)
config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

# Also exclude the now-unregistered Fabric-only class from compilation so the
# 26.2 artifact has one authoritative implementation of the OfLevel contract.
build_path = ROOT / "fabric/build.gradle"
s = build_path.read_text(encoding="utf-8")
anchor = '            exclude "org/valkyrienskies/mod/fabric/mixin/world/level/block/FireMixin.java"\n'
addition = anchor + '            exclude "org/valkyrienskies/mod/fabric/mixin/feature/shipyard_entities/MixinPersistentEntitySectionManager.java"\n'
if anchor not in s:
    raise SystemExit("Expected Fabric source exclusion anchor not found")
if "fabric/mixin/feature/shipyard_entities/MixinPersistentEntitySectionManager.java" in s:
    raise SystemExit("Fabric PersistentEntitySectionManager source already excluded before Phase 37")
s = s.replace(anchor, addition, 1)
build_path.write_text(s, encoding="utf-8")

print("Removed redundant Fabric PersistentEntitySectionManager mixin; common shipyard implementation remains authoritative")
