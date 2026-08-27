#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
accessor = "ClientLevelAccessor"
accessor_rel = Path("common/src/main/java/org/valkyrienskies/mod/mixin/accessors/client/multiplayer/ClientLevelAccessor.java")
expected_user = "common/src/main/java/org/valkyrienskies/mod/mixin/client/world/MixinClientChunkCache.java"

# MC 26.2 no longer stores LevelRenderer on ClientLevel. Phase 43 originally
# proved that the old accessor was still live. Keep that proof as a transition
# guard, but defer the one known renderer user to Phase 44 where it is ported to
# Minecraft.getInstance().levelRenderer before the accessor is retired.
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
        text = p.read_text(encoding="utf-8")
        if accessor in text:
            users.append(str(rel))

unexpected = [u for u in users if u != expected_user]
if unexpected:
    raise SystemExit("Unexpected ClientLevelAccessor users remain before Phase 44: " + ", ".join(unexpected))
if users != [expected_user]:
    raise SystemExit("Expected the single known ClientLevelAccessor user before Phase 44, got: " + ", ".join(users))

print("Verified sole stale ClientLevelAccessor user; deferred renderer retarget to Phase 44")
