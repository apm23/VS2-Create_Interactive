#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# 26.2 removed/reworked this old chunk rebuild task. It belongs to a legacy
# rendering compatibility path and is not required for the physics core.
aw = ROOT / "common/src/main/resources/valkyrienskies-common.accesswidener"
text = aw.read_text(encoding="utf-8")
old = "accessible\tclass\tnet/minecraft/client/renderer/chunk/SectionRenderDispatcher$RenderSection$RebuildTask\n"
if old not in text:
    old = "accessible  class   net/minecraft/client/renderer/chunk/SectionRenderDispatcher$RenderSection$RebuildTask\n"
if old in text:
    text = text.replace(old, "")
else:
    raise SystemExit("Expected legacy RebuildTask access widener entry not found")
aw.write_text(text, encoding="utf-8")

# Keep the first 26.2 source-port loop focused on VS physics/core. These are
# optional third-party compatibility sources whose dependencies/API targets are
# not part of the user's Create train acceptance path. Create integration will
# be reimplemented against Create Fly 26.2 after the core is green.
build = ROOT / "common/build.gradle"
b = build.read_text(encoding="utf-8")
needle = '            exclude "org/valkyrienskies/mod/common/item/PhysicsEntityCreatorItem.kt"\n'
if needle not in b:
    raise SystemExit("Could not find common Kotlin exclusion anchor")
insert = needle + (
    '            // 26.2 core-port isolation: optional/legacy compat only.\n'
    '            exclude "org/valkyrienskies/mod/compat/Weather2Compat.kt"\n'
    '            exclude "org/valkyrienskies/mod/compat/dynmap/**"\n'
    '            exclude "org/valkyrienskies/mod/compat/create/DeployerScrollOptionSlot.kt"\n'
)
b = b.replace(needle, insert, 1)
build.write_text(b, encoding="utf-8")

print("Removed stale 26.2 render AW entry and isolated optional compat sources")
