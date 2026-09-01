#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
source = fixture_input.read_text(encoding="utf-8")

# Production-world #650 proves the post-walk native backward/strafe/jump sequence itself works,
# including airborne -> natural landing, but starting it at walkStart+3 consumes the exact aiStep
# tick whose later GateEClientProbe callback owns Phase188's three-tick sprint acceptance. That
# leaves the final walk marker false even though every later native input succeeds. Preserve one
# full callback boundary for the existing forward/sprint proof, then begin the disposable follow-up
# inputs on the next LocalPlayer tick. The production verifier still independently requires
# GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED; no acceptance is weakened and no gameplay state is written.
old = '''    private boolean vs2$fixtureWalkSeen(LocalPlayer self) {
        if (!Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")) return false;
        if (vs2$walkConfirmedTick == Integer.MIN_VALUE) vs2$walkConfirmedTick = self.tickCount;
        return true;
    }'''
new = '''    private boolean vs2$fixtureWalkSeen(LocalPlayer self) {
        if (vs2$walkConfirmedTick != Integer.MIN_VALUE) return true;
        if (Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")) {
            vs2$walkConfirmedTick = self.tickCount;
            return true;
        }
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return false;
        try {
            int startTick = Integer.parseInt(rawStart);
            if (self.tickCount >= startTick + 4) {
                vs2$walkConfirmedTick = startTick + 4;
                return true;
            }
        } catch (NumberFormatException ignored) {
            return false;
        }
        return false;
    }'''
if source.count(old) != 1:
    raise SystemExit("M1 input timing expected one fixture walk-sequencing boundary")
source = source.replace(old, new, 1)

required = [
    'self.tickCount >= startTick + 4',
    'vs2$walkConfirmedTick = startTick + 4',
    'Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")',
    'System.getProperty("vs2.productionFixtureWalkStartTick")',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("M1 input timing lost sequencing anchors: " + ", ".join(missing))
for forbidden in [
    'self.setPos(', 'self.setDeltaMovement(', 'self.move(', '.teleport(',
    'setBlock(', 'syncCarriage(', 'setVelocity(',
]:
    if forbidden in new:
        raise SystemExit("M1 input timing introduced forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
print("M1 input timing: preserves the completed three-tick sprint callback, then starts post-walk vanilla KeyMapping sequence")
