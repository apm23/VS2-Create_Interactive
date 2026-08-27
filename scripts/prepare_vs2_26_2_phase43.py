#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"
accessor = "ClientLevelAccessor"
accessor_rel = Path("common/src/main/java/org/valkyrienskies/mod/mixin/accessors/client/multiplayer/ClientLevelAccessor.java")

# MC 26.2 no longer stores LevelRenderer on ClientLevel. The old accessor cannot
# be retargeted to a field that no longer exists. Before removing it from the
# active client mixin set, prove that no surviving ported source calls/casts it.
users = []
for base in (ROOT / "common/src/main", ROOT / "fabric/src/main"):
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix not in {".java", ".kt"}:
            continue
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            rel = p
        if rel == accessor_rel:
            continue
        text = p.read_text(encoding="utf-8")
        if accessor in text:
            users.append(str(rel))

if users:
    raise SystemExit("ClientLevelAccessor still has surviving source users and cannot be safely retired: " + ", ".join(users))

mixins_path = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
data = json.loads(mixins_path.read_text(encoding="utf-8"))
entry = "accessors.client.multiplayer.ClientLevelAccessor"
client = data.get("client", [])
if entry not in client:
    raise SystemExit("Expected ClientLevelAccessor entry missing before Phase 43")
data["client"] = [x for x in client if x != entry]
mixins_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Retired obsolete ClientLevel.levelRenderer accessor after proving no surviving 26.2 source users")
