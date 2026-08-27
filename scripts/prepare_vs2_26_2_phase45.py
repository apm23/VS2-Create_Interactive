#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
source = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/world/MixinClientLevel.java"
text = source.read_text(encoding="utf-8")

old_import = "import net.minecraft.client.renderer.LevelRenderer;\n"
new_import = "import net.minecraft.client.renderer.extract.LevelExtractor;\n"
if old_import not in text:
    raise SystemExit("Expected LevelRenderer import missing before Phase 45")
text = text.replace(old_import, new_import, 1)

old_sig = "ResourceKey resourceKey, Holder holder, int i, int j, LevelRenderer levelRenderer,\n        boolean bl, long l, int k, CallbackInfo ci)"
new_sig = "ResourceKey resourceKey, Holder holder, int i, int j, LevelExtractor levelExtractor,\n        boolean bl, long l, int k, CallbackInfo ci)"
if old_sig not in text:
    raise SystemExit("Expected ClientLevel constructor injection signature missing before Phase 45")
text = text.replace(old_sig, new_sig, 1)

if "LevelRenderer levelRenderer" in text or "import net.minecraft.client.renderer.LevelRenderer;" in text:
    raise SystemExit("Stale LevelRenderer constructor descriptor survived Phase 45")

source.write_text(text, encoding="utf-8")
print("Ported MixinClientLevel constructor injection from LevelRenderer to MC 26.2 LevelExtractor")
