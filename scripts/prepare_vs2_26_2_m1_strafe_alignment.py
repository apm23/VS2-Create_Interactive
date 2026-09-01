#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
source = fixture_input.read_text(encoding="utf-8")

# Production-world #588 proved the right-strafe KeyMapping executed natively, but the
# deterministic fixture still had world yaw 0 while the train corridor runs along world X.
# That maps "right" toward carriage-local -X and off the carriage end instead of toward the
# already-verified side wall at local Z=-2. Align the disposable fixture view once, at the
# start of the strafe window, so ordinary Minecraft right-strafe exercises the intended wall.
# This changes only test orientation; movement/collision/carry remain vanilla/Create native.
anchor = '''        client.options.keyLeft.setDown(false);\n        client.options.keyRight.setDown(strafeWindow);'''
replacement = '''        client.options.keyLeft.setDown(false);\n        if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE) {\n            self.setYRot(90.0F);\n        }\n        client.options.keyRight.setDown(strafeWindow);'''

count = source.count(anchor)
if count != 2:
    raise SystemExit(f"M1 strafe alignment expected two fixture KeyMapping sites, found {count}")
source = source.replace(anchor, replacement)

required = [
    'if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE)',
    'self.setYRot(90.0F)',
    'client.options.keyRight.setDown(strafeWindow)',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("M1 strafe alignment lost fixture anchors: " + ", ".join(missing))

for forbidden in [
    'self.setPos(', 'self.setDeltaMovement(', 'self.move(', '.teleport(',
    'setBlock(', 'syncCarriage(', 'setVelocity(',
]:
    if forbidden in source:
        raise SystemExit("M1 strafe alignment found forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
print("M1 strafe alignment: points native right-strafe toward the fixture side wall; orientation-only harness change")
