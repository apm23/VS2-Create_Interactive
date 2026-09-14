#!/usr/bin/env python3
from pathlib import Path

script = Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_input_timing.py")
source = script.read_text(encoding="utf-8")

# The standalone M1 wall verifier is now coordinate-agnostic: it proves a stable
# same-carriage plateau and material approach without requiring a fixture cell at
# z=+/-2.  The historical input-timing composer still tries to flip those deleted
# coordinate-specific geometry/penetration anchors.  Adapt only that composer
# bookkeeping before executing it; gameplay/input/lease mutations remain exactly
# those of the authoritative input-timing script.
old_wall_block = '''wall_direction_replacements = [
    (
        'wall_geometry_seen = any(re.search(r"(?:^|\\\\|)-?\\\\d+, [123], 2(?:\\\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
        'wall_geometry_seen = any(re.search(r"(?:^|\\\\|)-?\\\\d+, [123], -2(?:\\\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))',
    ),
    (
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=2")',
        'if not wall_geometry_seen: raise SystemExit("M1 wall proof missing occupied carriage side geometry at local block z=-2")',
    ),
    (
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)\\nif max_z>=2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)\\nif min_z<=-2.0: raise SystemExit(f"M1 player penetrated occupied carriage side geometry: local_z_samples={wall_z}")',
    ),
    (
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) >= 0.02\\nmaterial_approach = max_z-start_z >= 0.015',
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02\\nmaterial_approach = start_z-min_z >= 0.015',
    ),
    (
        'if stable_plateau and (max(candidate_z)-start_z>=0.015 or strafe_requested_toward_wall):',
        'if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):',
    ),
]'''
new_wall_block = '''wall_direction_replacements = [
    (
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)',
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)',
    ),
    (
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) >= 0.02\\nmaterial_approach = max_z-start_z >= 0.015',
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02\\nmaterial_approach = start_z-min_z >= 0.015',
    ),
    (
        'if stable_plateau and (max(candidate_z)-start_z>=0.015 or strafe_requested_toward_wall):',
        'if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):',
    ),
]'''
if source.count(old_wall_block) != 1:
    raise SystemExit("M1 current input composer expected one legacy coordinate-specific wall transform block")
source = source.replace(old_wall_block, new_wall_block, 1)

old_required = '''verifier_required = [
    'local block z=-2',
    'min_z=min(wall_z)',
    'float(strafe_move.group(3)) <= -0.02',
    'start_z-min(candidate_z)>=0.015',
]'''
new_required = '''verifier_required = [
    'min_z=min(wall_z)',
    'float(strafe_move.group(3)) <= -0.02',
    'start_z-min(candidate_z)>=0.015',
    'three consecutive supported samples on one Create carriage during strafe',
]'''
if source.count(old_required) != 1:
    raise SystemExit("M1 current input composer expected one legacy coordinate-specific verifier requirement block")
source = source.replace(old_required, new_required, 1)

scope = {
    "__name__": "__main__",
    "__file__": str(script),
    "__package__": None,
}
exec(compile(source, str(script), "exec"), scope, scope)
