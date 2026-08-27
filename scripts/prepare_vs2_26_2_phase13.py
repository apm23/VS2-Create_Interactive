#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# The Create compat Kotlin file lives under src/main/java, so the earlier Kotlin
# source exclusion did not catch it. Exclude it from Java source discovery too;
# Create 26.2 integration will be implemented separately after VS core is green.
p = ROOT / "common/build.gradle"
t = p.read_text(encoding="utf-8")
anchor = '''        java {
            // 1.21.11 port: exclude third-party mod-compat mixins'''
if anchor not in t:
    raise SystemExit("Could not find common Java source-set anchor")
t = t.replace(
    anchor,
    '''        java {
            exclude "org/valkyrienskies/mod/compat/create/DeployerScrollOptionSlot.kt"
            // 1.21.11 port: exclude third-party mod-compat mixins''',
    1,
)
p.write_text(t, encoding="utf-8")

# Use the stable static Vec3 center helper. Kotlin/no-remap symbol exposure for
# BlockPos#getCenter differs from the decompiled reference source.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/CompatUtil.kt"
t = p.read_text(encoding="utf-8")
t = t.replace("level.getHeightmapPos(types, pos).getCenter()", "Vec3.atCenterOf(level.getHeightmapPos(types, pos))")
t = t.replace("worldHeight.getCenter()", "Vec3.atCenterOf(worldHeight)")
t = t.replace("pos.getCenter()", "Vec3.atCenterOf(pos)")
p.write_text(t, encoding="utf-8")

# LevelRenderer#needsUpdate is not visible in the 26.2 compile namespace used
# by this no-remap Loom setup. allChanged() is public and provides the required
# renderer invalidation when changing mounted camera perspective.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/client/ShipMountPerspective.kt"
t = p.read_text(encoding="utf-8")
if t.count("mc.levelRenderer.needsUpdate()") < 2:
    raise SystemExit("Expected mounted-camera renderer invalidations not found")
t = t.replace("mc.levelRenderer.needsUpdate()", "mc.levelRenderer.allChanged()")
p.write_text(t, encoding="utf-8")

# Player#displayClientMessage was removed. Preserve the exact actionbar/overlay
# behavior by sending the 26.2 system-chat packet with overlay=true.
p = ROOT / "common/src/main/kotlin/org/valkyrienskies/mod/common/entity/ShipMountingEntity.kt"
t = p.read_text(encoding="utf-8")
import_anchor = "import net.minecraft.server.level.ServerPlayer\n"
if import_anchor not in t:
    raise SystemExit("ServerPlayer import anchor not found")
if "import net.minecraft.network.protocol.game.ClientboundSystemChatPacket\n" not in t:
    t = t.replace(import_anchor, import_anchor + "import net.minecraft.network.protocol.game.ClientboundSystemChatPacket\n", 1)
old = ".displayClientMessage(SEATED_PROMPT, true)"
if t.count(old) != 2:
    raise SystemExit("Expected two seated actionbar messages")
t = t.replace(old, ".connection.send(ClientboundSystemChatPacket(SEATED_PROMPT, true))")
p.write_text(t, encoding="utf-8")

print("Ported renderer invalidation, seat overlay messaging, center helpers, and Java-side compat isolation")
