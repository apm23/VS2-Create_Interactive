#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"
source = ROOT / "common/src/main/java/org/valkyrienskies/mod/mixin/client/world/MixinClientChunkCache.java"
text = source.read_text(encoding="utf-8")
old_import = "import org.valkyrienskies.mod.mixin.accessors.client.multiplayer.ClientLevelAccessor;\n"
if old_import not in text:
    raise SystemExit("Expected ClientLevelAccessor import missing before Phase 44")
text = text.replace(old_import, "")
old = "((LevelRendererAccessor) ((ClientLevelAccessor) level).getLevelRenderer()).getViewArea()"
count = text.count(old)
if count != 3:
    raise SystemExit(f"Expected 3 stale ClientLevelAccessor renderer call-sites, found {count}")
text = text.replace(old, "((LevelRendererAccessor) Minecraft.getInstance().levelRenderer).getViewArea()")
if "ClientLevelAccessor" in text:
    raise SystemExit("ClientLevelAccessor reference survived Phase 44 source retarget")
source.write_text(text, encoding="utf-8")

# Prove the accessor has no surviving source users before retiring it from the
# active common client mixin list.
accessor = "ClientLevelAccessor"
accessor_rel = Path("common/src/main/java/org/valkyrienskies/mod/mixin/accessors/client/multiplayer/ClientLevelAccessor.java")
users = []
for base in (ROOT / "common/src/main", ROOT / "fabric/src/main"):
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix not in {".java", ".kt"}:
            continue
        rel = p.relative_to(ROOT)
        if rel == accessor_rel:
            continue
        if accessor in p.read_text(encoding="utf-8"):
            users.append(str(rel))
if users:
    raise SystemExit("ClientLevelAccessor still has source users after Phase 44: " + ", ".join(users))

mixins_path = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
data = json.loads(mixins_path.read_text(encoding="utf-8"))
entry = "accessors.client.multiplayer.ClientLevelAccessor"
client = data.get("client", [])
if entry not in client:
    raise SystemExit("Expected ClientLevelAccessor mixin entry missing before Phase 44 retirement")
data["client"] = [x for x in client if x != entry]
mixins_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Retargeted ship-chunk vanilla renderer access to Minecraft.getInstance().levelRenderer and retired obsolete ClientLevelAccessor")
