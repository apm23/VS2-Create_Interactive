#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
data = json.loads(p.read_text(encoding="utf-8"))

# The 26.2 port deliberately parks legacy optional renderer/LOD compatibility
# sources (Iris, Sodium, Voxy) while preserving VS2's core client transforms,
# movement, collision, camera, chunk, sound, and rendering hooks.  Leaving their
# mod_compat entries registered makes a client launch fail during Mixin PREPARE
# before Minecraft can reach the title screen because the parked classes are not
# present in the compiled output.
client = data.get("client", [])
stale = [entry for entry in client if entry.startswith("mod_compat.")]
if not stale:
    raise SystemExit("Expected stale common mod_compat client mixins before Phase 42")
if "mod_compat.iris.MixinVertexArrayCacheEmulated" not in stale:
    raise SystemExit("Expected Iris stale mixin that caused the Phase 41 client crash")

# Never remove core client mixins in this compatibility cleanup.
core_guards = {
    "client.MixinCamera",
    "client.MixinMinecraft",
    "client.player.MixinLocalPlayer",
    "feature.entity_movement_packets.MixinLocalPlayer",
    "client.world.MixinClientLevel",
    "feature.shipyard_entities.MixinClientLevel",
}
missing_core = sorted(core_guards.difference(client))
if missing_core:
    raise SystemExit(f"Core VS2 client mixins missing before Phase 42: {missing_core}")

data["client"] = [entry for entry in client if not entry.startswith("mod_compat.")]
p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Removed stale optional common client mod_compat mixins while preserving VS2 core client movement/ship hooks: " + ", ".join(stale))
