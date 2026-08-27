#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/ValkyrienSkiesModFabric.kt"
t = p.read_text(encoding="utf-8")
old = '''        val isClient = FabricLoader.getInstance().environmentType == EnvType.CLIENT\n        if (isClient) {\n            // Load client render settings (config/valkyrienskies_client.json) -- e.g. ship render distance.\n            VSClientConfigLoader.loadOrCreate()\n            // Client API restoration is gated separately for MC 26.2.\n        }\n'''
if old not in t:
    raise SystemExit("Expected parked client-init block not found in ValkyrienSkiesModFabric.kt")
new = '''        // Client config/render/input restoration is gated separately for Minecraft 26.2.\n        // The physics/server core must boot independently before those client-only layers return.\n'''
t = t.replace(old, new, 1)
# Clean imports that became unused with the parked client branch.
t = t.replace("import net.fabricmc.api.EnvType\n", "")
t = t.replace("import net.fabricmc.loader.api.FabricLoader\n", "")
p.write_text(t, encoding="utf-8")
print("Removed parked VSClientConfigLoader call from the 26.2 Fabric physics-core gate")
