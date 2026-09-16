#!/usr/bin/env python3
from pathlib import Path
import re

p = Path(__file__).resolve().parents[1] / "upstream/fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
s = p.read_text(encoding="utf-8")

# Keep the natural-landing proof's jump admission tied to fresh Create floor/native-contact evidence.
pattern = re.compile(r'    @Unique\n    private boolean vs2\$jumpArmReady\(LocalPlayer self\) \{.*?\n    \}', re.S)
m = pattern.search(s)
if not m:
    raise SystemExit("natural landing harness could not locate jumpArmReady")
old = m.group(0)
if "vs2.productionFixtureJumpFloorSupportNow" not in old or "vs2.phase170NativeContactApplicationTick" not in old:
    raise SystemExit("natural landing harness found unexpected jumpArmReady boundary")
new = "\n".join([
    "    @Unique",
    "    private boolean vs2$jumpArmReady(LocalPlayer self) {",
    "        if (vs2$jumpStartTick != Integer.MIN_VALUE) return !vs2$jumpLandedLogged;",
    "        if (!vs2$fixtureWalkSeen(self) || !self.onGround()) return false;",
    "        if (!Boolean.getBoolean(\"vs2.productionFixtureJumpFloorSupportNow\")) return false;",
    "        String floorTickRaw = System.getProperty(\"vs2.productionFixtureJumpFloorSupportTick\");",
    "        String nativeTickRaw = System.getProperty(\"vs2.phase170NativeContactApplicationTick\");",
    "        if (floorTickRaw == null || nativeTickRaw == null) return false;",
    "        try {",
    "            int floorTick = Integer.parseInt(floorTickRaw);",
    "            int nativeTick = Integer.parseInt(nativeTickRaw);",
    "            boolean floorFresh = floorTick == self.tickCount || floorTick == self.tickCount - 1;",
    "            boolean nativeFresh = nativeTick == self.tickCount || nativeTick == self.tickCount - 1;",
    "            return floorFresh && nativeFresh;",
    "        } catch (NumberFormatException ignored) {",
    "            return false;",
    "        }",
    "    }",
])
s = s[:m.start()] + new + s[m.end():]

old_window = '''        boolean jumpWindow = !vs2$jumpLandedLogged
            && (vs2$jumpArmReady(self) || vs2$jumpStartTick != Integer.MIN_VALUE);
'''
new_window = '''        // Natural-landing CI only: keep vanilla aiStep alive for a bounded arc even if the
        // generic onGround observer emits an early landing marker before Create support returns.
        boolean jumpWindow = vs2$jumpStartTick != Integer.MIN_VALUE
            ? self.tickCount <= vs2$jumpStartTick + 40
            : vs2$jumpArmReady(self);
'''
if s.count(old_window) != 1:
    raise SystemExit(f"natural landing harness expected one headless jumpWindow, found {s.count(old_window)}")
s = s.replace(old_window, new_window, 1)

for forbidden in ["self.setPos(", "self.setDeltaMovement(", "self.move(", ".teleport(", "setVelocity(", "setNoGravity(", "setOnGround("]:
    if forbidden in new + new_window:
        raise SystemExit("natural landing harness introduced forbidden movement mutation: " + forbidden)

p.write_text(s, encoding="utf-8")
print("REFERENCE_OWNER_V2_NATURAL_LANDING_HARNESS_V2 fixture_only=true fresh_jump_admission=true bounded_native_airstep_through_false_landing=true direct_motion_mutation=false")
