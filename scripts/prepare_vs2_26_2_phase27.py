#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/feature/water_in_ships_entity/MixinEntity.java"
s = p.read_text(encoding="utf-8")

# Minecraft 26.2 removed/reworked Entity.updateFluidHeightAndDoFluidPushing.
# The old Fabric mixin recursively re-entered that vanilla method and modified
# a set of fragile locals.  The 26.2 common Entity mixin now performs direct
# ship-space body-water detection, while ship inside-block effects cover lava/
# water contact effects.  Keep this Fabric mixin's updateFluidOnEyes support,
# but remove the obsolete body-fluid chain so the mixin can apply on 26.2.
for old in (
    '''    @Shadow\n    public abstract boolean updateFluidHeightAndDoFluidPushing(TagKey<Fluid> tagKey, double d);\n\n''',
    '''    @Shadow\n    public abstract void lavaIgnite();\n\n''',
    '''    @Shadow\n    public abstract void lavaHurt();\n\n''',
    '''    @Shadow\n    public abstract void extinguishFire();\n\n''',
):
    if old not in s:
        # upstream checkout uses CRLF on some runners after checkout; normalize
        old_crlf = old.replace("\n", "\r\n")
        if old_crlf in s:
            s = s.replace(old_crlf, "", 1)
        else:
            raise SystemExit(f"Expected obsolete shadow block not found: {old.splitlines()[-1]}")
    else:
        s = s.replace(old, "", 1)

start_marker = '''    /**\n     * used to replace updateFluidHeightAndDoFluidPushing aABB in ship context\n     * */'''
end_marker = '''    @WrapOperation(\n        at = @At(value = "INVOKE",\n            target = "Lnet/minecraft/world/level/Level;getFluidState(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/material/FluidState;"),\n        method = "updateFluidOnEyes"\n    )'''

# TextIO normalizes newlines on read, so LF markers are sufficient here.
start = s.find(start_marker)
end = s.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Could not locate obsolete body-fluid mixin chain boundaries")
s = s[:start] + '''    // MC 26.2: obsolete updateFluidHeightAndDoFluidPushing injector chain removed.\n    // Body contact is handled by the common direct ship-space fallback; eye-fluid\n    // detection below remains active for correct underwater state/rendering.\n\n''' + s[end:]

p.write_text(s, encoding="utf-8")
print("Removed obsolete 1.21 body-fluid injector chain while preserving ship eye-fluid support")
