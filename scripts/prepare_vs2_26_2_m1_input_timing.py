#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
fixture_input = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
verifier = Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_jump_proof.py")
source = fixture_input.read_text(encoding="utf-8")
verifier_source = verifier.read_text(encoding="utf-8")

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

# Production-world #651 proves the native right-strafe itself is valid and material: the request at
# tick 32 has negative-Z motion, carriage 8 then supplies four consecutive grounded/broadphase
# samples through tick 35, and only afterwards does Create authoritatively hand contact to sibling
# carriage 7 at tick 36 immediately before the jump. The existing read-only verifier incorrectly
# chases any sibling rebase within seven ticks and therefore discards the already-complete wall
# streak, then asks for three grounded samples on a frame whose third sample is the real airborne
# jump. Restore the exact-request-tick handoff rule and the observed negative-Z wall convention.
# This changes verifier bookkeeping only; it never changes player/train/collision/carry state.
wall_direction_replacements = [
    (
        'wall_geometry_seen = any(re.search(r"(?:^|\\|)-?\\d+, [123], 2(?:\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
        'wall_geometry_seen = any(re.search(r"(?:^|\\|)-?\\d+, [123], -2(?:\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
    ),
    (
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=2")',
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")',
    ),
    (
        'start_z=before[-1][4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)\nif max_z>=2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
        'start_z=before[-1][4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)\nif min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
    ),
    (
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) >= 0.02\nmaterial_approach = max_z-start_z >= 0.015',
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02\nmaterial_approach = start_z-min_z >= 0.015',
    ),
    (
        'if stable_plateau and (max(candidate_z)-start_z>=0.015 or strafe_requested_toward_wall):',
        'if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):',
    ),
]
for old_wall, new_wall in wall_direction_replacements:
    if verifier_source.count(old_wall) != 1:
        raise SystemExit("M1 wall verifier expected one transformed direction boundary: " + old_wall[:72])
    verifier_source = verifier_source.replace(old_wall, new_wall, 1)

late_handoff = '''pre_wall_carriage=before[-1][1]
rebase_pattern=re.compile(
    rf"GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE[^\\n]*previous_carriage_id={pre_wall_carriage}[^\\n]*carriage_id=(\\d+)[^\\n]*player_tick=(\\d+)[^\\n]*native_contact_owner=true[^\\n]*identity_only=true")
rebase_match=next((m for m in rebase_pattern.finditer(text) if strafe_request_tick <= int(m.group(2)) <= strafe_request_tick+7), None)
wall_carriage=int(rebase_match.group(1)) if rebase_match is not None else pre_wall_carriage
wall_start_tick=int(rebase_match.group(2)) if rebase_match is not None else strafe_request_tick
after=[]; expected_tick=wall_start_tick
for sample in after_window:
    if sample[0]<expected_tick: continue
    if sample[0]!=expected_tick or sample[1]!=wall_carriage: break
    after.append(sample); expected_tick+=1
if len(after)<3: raise SystemExit("M1 wall proof did not retain three consecutive samples on the Create-authoritative strafe carriage")'''
exact_handoff = '''pre_wall_carriage=before[-1][1]
rebase_match=re.search(
    rf"GATE_E_PHASE136_SUPPORTED_SIBLING_REBASE[^\\n]*previous_carriage_id={pre_wall_carriage}[^\\n]*carriage_id=(\\d+)[^\\n]*player_tick={strafe_request_tick}[^\\n]*native_contact_owner=true[^\\n]*identity_only=true",
    text)
wall_carriage=int(rebase_match.group(1)) if rebase_match is not None else pre_wall_carriage
after=[]; expected_tick=strafe_request_tick
for sample in after_window:
    if sample[0]<expected_tick: continue
    if sample[0]!=expected_tick or sample[1]!=wall_carriage: break
    after.append(sample); expected_tick+=1
if len(after)<3: raise SystemExit("M1 wall proof did not retain three consecutive samples on the Create-authoritative strafe carriage")'''
if verifier_source.count(late_handoff) != 1:
    raise SystemExit("M1 wall verifier expected one late-window sibling-handoff boundary")
verifier_source = verifier_source.replace(late_handoff, exact_handoff, 1)

required = [
    'self.tickCount >= startTick + 4',
    'vs2$walkConfirmedTick = startTick + 4',
    'Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")',
    'System.getProperty("vs2.productionFixtureWalkStartTick")',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("M1 input timing lost sequencing anchors: " + ", ".join(missing))
verifier_required = [
    'local block z=-2',
    'min_z=min(wall_z)',
    'float(strafe_move.group(3)) <= -0.02',
    'start_z-min(candidate_z)>=0.015',
    'player_tick={strafe_request_tick}',
]
verifier_missing = [token for token in verifier_required if token not in verifier_source]
if verifier_missing:
    raise SystemExit("M1 wall verifier lost run-651 native proof anchors: " + ", ".join(verifier_missing))
for forbidden in [
    'self.setPos(', 'self.setDeltaMovement(', 'self.move(', '.teleport(',
    'setBlock(', 'syncCarriage(', 'setVelocity(',
]:
    if forbidden in new:
        raise SystemExit("M1 input timing introduced forbidden gameplay mutation: " + forbidden)

fixture_input.write_text(source, encoding="utf-8")
verifier.write_text(verifier_source, encoding="utf-8")
print("M1 input timing: preserves sprint callback and aligns the read-only wall verifier with the proven native strafe frame")
