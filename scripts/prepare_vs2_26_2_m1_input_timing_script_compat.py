#!/usr/bin/env python3
from pathlib import Path
import runpy

script = Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_input_timing.py")
source = script.read_text(encoding="utf-8")

old_wall_prefix = '''wall_direction_replacements = [
    (
        'wall_geometry_seen = any(re.search(r"(?:^|\\\\|)-?\\\\d+, [123], 2(?:\\\\||$)", m.group(4)) for m in client_state_pattern.finditer(text))','''
if old_wall_prefix in source:
    start = source.index("wall_direction_replacements = [")
    end = source.index("\nfor old_wall, new_wall in wall_direction_replacements:", start)
    new_wall_block = '''# M1_CURRENT_COORDINATE_AGNOSTIC_WALL_COMPOSER
wall_direction_replacements = [
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
    source = source[:start] + new_wall_block + source[end:]

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
        raise SystemExit("M1 input composer source compatibility expected one legacy verifier requirement block")
    source = source.replace(old_required, new_required, 1)
    script.write_text(source, encoding="utf-8")
    print("M1 input composer source compatibility: removed stale fixed wall-cell/penetration assumptions")
elif "M1_CURRENT_COORDINATE_AGNOSTIC_WALL_COMPOSER" in source:
    print("M1 input composer source compatibility already applied")
else:
    raise SystemExit("M1 input composer source compatibility could not find legacy or migrated wall block")

runpy.run_path(
    str(Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_wall_fixture_script_compat.py")),
    run_name="__main__",
)
