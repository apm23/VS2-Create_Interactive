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

# Production-world #589 proves the wall fixture was armed only after the already-confirmed
# forward sprint had carried the disposable player out of carriage broadphase. The native walk
# proof itself completed before that loss of support. Stop the bounded forward KeyMapping as soon
# as the existing walk-confirmed property becomes authoritative, leaving the later reverse/strafe
# inputs to run from the still-supported carriage surface. Harness input only; no player transform,
# velocity, collision, carry, train, or world state is synthesized.
pulse_anchor = 'boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3;'
pulse_replacement = 'boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
pulse_count = source.count(pulse_anchor)
if pulse_count != 1:
    raise SystemExit(f"M1 forward-stop expected one LocalPlayer forward pulse boundary, found {pulse_count}")
source = source.replace(pulse_anchor, pulse_replacement, 1)

walk_window_anchor = 'boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3;'
walk_window_replacement = 'boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3 && !Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");'
walk_window_count = source.count(walk_window_anchor)
if walk_window_count != 1:
    raise SystemExit(f"M1 forward-stop expected one headless forward pulse boundary, found {walk_window_count}")
source = source.replace(walk_window_anchor, walk_window_replacement, 1)

required = [
    'if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE)',
    'self.setYRot(90.0F)',
    'client.options.keyRight.setDown(strafeWindow)',
    '!Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("M1 strafe/forward fixture lost anchors: " + ", ".join(missing))

for forbidden in [
    'self.setPos(', 'self.setDeltaMovement(', 'self.move(', '.teleport(',
    'setBlock(', 'syncCarriage(', 'setVelocity(',
]:
    if forbidden in source:
        raise SystemExit("M1 strafe/forward fixture found forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
print("M1 fixture alignment: stops forward input after native walk proof and points right-strafe toward the side wall")
