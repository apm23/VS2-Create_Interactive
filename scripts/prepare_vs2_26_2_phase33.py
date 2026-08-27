#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/server/MixinMinecraftServer.java"
s = p.read_text(encoding="utf-8")

# MC 26.2 changed the internals of MinecraftServer#createLevels. The old 1.21.11
# injector targeted a specific getDataStorage() INVOKE and silently stopped firing,
# leaving shipWorld/vsPipeline null until the first tick. Retarget to TAIL: all
# ServerLevels and overworld data storage exist, but the first server tick has not
# happened yet, preserving the original lifecycle intent.
old = '''    @Inject(\n        method = "createLevels",\n        at = @At(\n            value = "INVOKE",\n            target = "Lnet/minecraft/server/level/ServerLevel;getDataStorage()Lnet/minecraft/world/level/storage/DimensionDataStorage;"\n        )\n    )\n    private void postCreateLevels(final CallbackInfo ci) {\n'''
new = '''    @Inject(method = "createLevels", at = @At("TAIL"))\n    private void postCreateLevels(final CallbackInfo ci) {\n'''
if old not in s:
    raise SystemExit("Expected 1.21.11 createLevels injection anchor not found")
s = s.replace(old, new, 1)

# Unique mixin instance-field initializers are not a lifecycle contract we want to
# rely on across the 26.2 transformer. Make the two mutable lifecycle containers
# explicitly initializable and initialize them in beforeInitServer, which is known
# to fire before createLevels/ticks.
s = s.replace(
    '    private Set<String> loadedLevels = new HashSet<>();\n',
    '    private Set<String> loadedLevels;\n',
    1,
)
s = s.replace(
    '    private final Map<String, ServerLevel> dimensionToLevelMap = new HashMap<>();\n',
    '    private Map<String, ServerLevel> dimensionToLevelMap;\n',
    1,
)
anchor = '''    private void beforeInitServer(final CallbackInfo info) {\n        ValkyrienSkiesMod.setCurrentServer(MinecraftServer.class.cast(this));\n    }\n'''
replacement = '''    private void beforeInitServer(final CallbackInfo info) {\n        loadedLevels = new HashSet<>();\n        dimensionToLevelMap = new HashMap<>();\n        ValkyrienSkiesMod.setCurrentServer(MinecraftServer.class.cast(this));\n    }\n'''
if anchor not in s:
    raise SystemExit("beforeInitServer anchor not found")
s = s.replace(anchor, replacement, 1)

# Defensive shutdown guard for partially-started servers. This is not the primary
# fix (createLevels TAIL is); it only keeps shutdown deterministic if startup aborts
# before beforeInitServer/createLevels on a future runtime regression.
s = s.replace(
    '        dimensionToLevelMap.clear();\n',
    '        if (dimensionToLevelMap != null) dimensionToLevelMap.clear();\n',
    1,
)

p.write_text(s, encoding="utf-8")
print("Retargeted VS2 server-world lifecycle init to MC 26.2 createLevels TAIL and hardened lifecycle containers")
