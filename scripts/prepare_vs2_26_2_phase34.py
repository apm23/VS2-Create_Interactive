#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

loaded_mods = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/compat/LoadedMods.kt"
s = loaded_mods.read_text(encoding="utf-8")

# RecipeOverrides contains compatibility recipes whose ids/results live in Eureka
# (vs_eureka:*).  On a VS2-only runtime those registry entries do not exist, so
# feeding the overrides to RecipeManager creates noisy parse failures.  Reuse VS2's
# existing class-presence compatibility abstraction instead of introducing a
# loader-specific dependency in common code.
anchor = '''    @JvmStatic\n    val create by CompatInfo("com.simibubi.create.AllMountedDispenseItemBehaviors")\n'''
replacement = '''    @JvmStatic\n    val create by CompatInfo("com.simibubi.create.AllMountedDispenseItemBehaviors")\n\n    @JvmStatic\n    val eureka by CompatInfo("org.valkyrienskies.eureka.EurekaMod")\n'''
if 'val eureka by CompatInfo("org.valkyrienskies.eureka.EurekaMod")' not in s:
    if anchor not in s:
        raise SystemExit("LoadedMods Create compatibility anchor not found")
    s = s.replace(anchor, replacement, 1)
    loaded_mods.write_text(s, encoding="utf-8")

recipes = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/config/RecipeOverrides.kt"
s = recipes.read_text(encoding="utf-8")

import_anchor = 'import org.valkyrienskies.mod.util.logger\n'
if 'import org.valkyrienskies.mod.compat.LoadedMods\n' not in s:
    if import_anchor not in s:
        raise SystemExit("RecipeOverrides logger import anchor not found")
    s = s.replace(
        import_anchor,
        'import org.valkyrienskies.mod.compat.LoadedMods\n' + import_anchor,
        1,
    )

load_anchor = '''    private fun load() {\n        val overrides = LinkedHashMap<String, JsonObject>()\n        val removals = LinkedHashSet<String>()\n        try {\n'''
load_replacement = '''    private fun load() {\n        val overrides = LinkedHashMap<String, JsonObject>()\n        val removals = LinkedHashSet<String>()\n\n        // These overrides only repair Eureka's legacy recipes.  A standalone VS2\n        // install has no vs_eureka registry entries, so leave the caches empty and\n        // do not create/read the Eureka recipe config at all unless Eureka exists.\n        if (!LoadedMods.eureka) {\n            overrideCache = overrides\n            removalCache = removals\n            return\n        }\n\n        try {\n'''
if 'if (!LoadedMods.eureka)' not in s:
    if load_anchor not in s:
        raise SystemExit("RecipeOverrides load anchor not found")
    s = s.replace(load_anchor, load_replacement, 1)
    recipes.write_text(s, encoding="utf-8")

print("Gated Eureka recipe overrides behind VS2 LoadedMods.eureka compatibility detection")
