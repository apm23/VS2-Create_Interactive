#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "common/src/main/resources/valkyrienskies-common.mixins.json"
s = p.read_text(encoding="utf-8")

entry = '    "feature.ai.goal.villagers.MixinInteractWith",\n'
entry_crlf = '    "feature.ai.goal.villagers.MixinInteractWith",\r\n'

count = s.count('"feature.ai.goal.villagers.MixinInteractWith"')
if count != 1:
    raise SystemExit(f"Expected exactly one MixinInteractWith config entry, found {count}")

if entry_crlf in s:
    s = s.replace(entry_crlf, '', 1)
elif entry in s:
    s = s.replace(entry, '', 1)
else:
    # read_text() may normalize line endings; remove the exact logical line safely.
    lines = s.splitlines(keepends=True)
    kept = [line for line in lines if '"feature.ai.goal.villagers.MixinInteractWith"' not in line]
    if len(kept) != len(lines) - 1:
        raise SystemExit("Could not remove exactly one MixinInteractWith config line")
    s = ''.join(kept)

p.write_text(s, encoding="utf-8")

# GitHub Actions checks out a fresh client run directory. On a first Minecraft
# launch, absence of options.txt enables Accessibility Onboarding, which owns
# the callback that would otherwise execute --quickPlaySingleplayer. Seed only
# the first-run option required by this headless smoke; never overwrite an
# existing player/developer options file.
options = ROOT / "fabric/run/options.txt"
if not options.exists():
    options.parent.mkdir(parents=True, exist_ok=True)
    options.write_text("onboardAccessibility:false\npauseOnLostFocus:false\n", encoding="utf-8")

print("Phase 50: disabled obsolete MC 1.21.11 villager-socialization MixinInteractWith on 26.2; seeded CI first-run options so quick-play can execute; core ship/train behavior remains enabled")
