#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "upstream"
p = ROOT / "fabric/src/main/resources/valkyrienskies-fabric.mixins.json"
data = json.loads(p.read_text(encoding="utf-8"))

# These ComputerCraft/CC-Restitched compatibility mixins are optional and their
# sources are not part of the 26.2 physics-core gate. Leaving stale entries in
# the mixin config makes Fabric fail before VS2 can initialize.
remove = {
    "compat.cc_restitched.MixinWirelessModemPeripheral",
    "compat.cc_restitched.MixinSpeakerSound",
}
old_mixins = list(data.get("mixins", []))
new_mixins = [m for m in old_mixins if m not in remove]
if len(new_mixins) == len(old_mixins):
    raise SystemExit("Expected CC-Restitched mixin entries were not found")
data["mixins"] = new_mixins

# MC 26.2 runs on Java 25; keep the mixin metadata aligned with the runtime.
data["compatibilityLevel"] = "JAVA_25"

p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("Removed stale optional CC-Restitched mixin entries and aligned mixin compatibility to Java 25")
