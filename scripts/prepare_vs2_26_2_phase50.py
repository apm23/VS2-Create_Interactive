#!/usr/bin/env python3
from pathlib import Path
import runpy

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
    lines = s.splitlines(keepends=True)
    kept = [line for line in lines if '"feature.ai.goal.villagers.MixinInteractWith"' not in line]
    if len(kept) != len(lines) - 1:
        raise SystemExit("Could not remove exactly one MixinInteractWith config line")
    s = ''.join(kept)

p.write_text(s, encoding="utf-8")

options = ROOT / "fabric/run/options.txt"
if not options.exists():
    options.parent.mkdir(parents=True, exist_ok=True)
    options.write_text("onboardAccessibility:false\npauseOnLostFocus:false\n", encoding="utf-8")

# Phase 50 remains the workflow's terminal preparation step. Chain the
# read-only Gate D observer from here so existing build/smoke workflows gain
# deterministic in-process telemetry without needing keyboard/X11 injection.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase51.py")), run_name="__main__")

print("Phase 50: disabled obsolete MC 1.21.11 villager-socialization MixinInteractWith on 26.2; seeded CI first-run options and chained read-only Gate D telemetry; core ship/train behavior remains enabled")
