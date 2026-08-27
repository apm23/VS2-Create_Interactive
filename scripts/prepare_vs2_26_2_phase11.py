#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/config/DimensionParametersResolver.kt"
t = p.read_text(encoding="utf-8")
old = '''    override fun apply(
        objects: Map<Identifier?, JsonElement?>,
        resourceManager: ResourceManager,
        profiler: ProfilerFiller
    ) {'''
new = '''    override fun apply(
        objects: Map<Identifier, JsonElement>,
        resourceManager: ResourceManager,
        profiler: ProfilerFiller
    ) {'''
if old not in t:
    raise SystemExit("Expected nullable DimensionParametersResolver apply signature not found")
t = t.replace(old, new, 1)
# Keys/values are guaranteed non-null by the 26.2 reload listener.
t = t.replace("            if (key == null || value == null) {return@forEach}\n", "", 1)
p.write_text(t, encoding="utf-8")

p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/config/MassDatapackResolver.kt"
t = p.read_text(encoding="utf-8")
old = '''        override fun apply(
            objects: MutableMap<Identifier, JsonElement>?,
            resourceManager: ResourceManager?,
            profiler: ProfilerFiller?
        ) {'''
new = '''        override fun apply(
            objects: MutableMap<Identifier, JsonElement>,
            resourceManager: ResourceManager,
            profiler: ProfilerFiller
        ) {'''
if old not in t:
    raise SystemExit("Expected nullable VSMassDataLoader apply signature not found")
t = t.replace(old, new, 1)
t = t.replace("            objects?.forEach { (location, element) ->", "            objects.forEach { (location, element) ->", 1)
p.write_text(t, encoding="utf-8")

print("Ported VS datapack reload listener apply signatures to Minecraft 26.2")
