#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
source = fixture_input.read_text(encoding="utf-8")

# Production-world #648 proves the three-tick native forward/sprint proof completes on a still-
# grounded, supported frame, but the boolean walk-confirm publication arrives after LocalPlayer's
# aiStep HEAD for that same tick. Phase203 therefore cannot actually put reverse into vanilla input
# until the following tick, exactly the stale one-tick boundary it was intended to remove. Sequence
# the disposable follow-up inputs from the already-known end of the bounded forward pulse instead.
# The production verifier still independently requires GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED, so
# this does not weaken acceptance or bypass native Create/Minecraft locomotion. It only makes the
# ordinary KeyMapping available at the correct sampling tick; no position, velocity, collision,
# carry, gravity, train, or world state is written.
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
            if (self.tickCount >= startTick + 3) {
                vs2$walkConfirmedTick = startTick + 3;
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
    'self.tickCount >= startTick + 3',
    'vs2$walkConfirmedTick = startTick + 3',
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
print("M1 input timing: starts post-walk vanilla KeyMapping sequence on the proven three-tick pulse boundary")
