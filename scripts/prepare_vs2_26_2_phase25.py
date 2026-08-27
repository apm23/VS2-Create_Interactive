#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/entity/MixinEntity.java"
s = p.read_text(encoding="utf-8")

# MC 26.2 removed Entity.fluidOnEyes. The sealed-air-pocket wrapper only needs
# to suppress the eye-in-water state; retaining the obsolete @Shadow makes the
# entire core Entity mixin fail during class transformation before the server can boot.
old = '''        if (vs$isInSealedArea() && ValkyrienSkies.isConnectivityEnabled(level.isClientSide)) {
            this.wasEyeInWater = false;
            this.fluidOnEyes.clear();
            return;
        }'''
new = '''        if (vs$isInSealedArea() && ValkyrienSkies.isConnectivityEnabled(level.isClientSide)) {
            this.wasEyeInWater = false;
            return;
        }'''
if old not in s:
    raise SystemExit("Expected sealed-area fluidOnEyes block not found")
s = s.replace(old, new, 1)

old_shadow = '''    @Shadow
    @Final
    private Set<TagKey<Fluid>> fluidOnEyes;

'''
if old_shadow not in s:
    raise SystemExit("Expected obsolete fluidOnEyes @Shadow not found")
s = s.replace(old_shadow, "", 1)

# Remove imports that became unused solely because of the deleted field.
s = s.replace("import java.util.Set;\n", "")

p.write_text(s, encoding="utf-8")
print("Adapted core Entity mixin to MC 26.2 fluidOnEyes removal")
