#!/usr/bin/env python3
from pathlib import Path

script = Path(__file__).resolve().with_name("prepare_vs2_26_2_m1_wall_fixture_window.py")
source = script.read_text(encoding="utf-8")

marker = "M1_CURRENT_COORDINATE_AGNOSTIC_WALL_FIXTURE_COMPOSER"
if marker not in source:
    start = source.index("replacements = [")
    end = source.index("\nfixture_input.write_text", start)
    new_block = '''# M1_CURRENT_COORDINATE_AGNOSTIC_WALL_FIXTURE_COMPOSER
replacements = [
    (
        'after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+9, request_tick-1) and s[5] and s[6] and s[7]]',
        'after_window=[s for s in samples if strafe_request_tick<=s[0]<=min(strafe_request_tick+14, request_tick-1) and s[5] and s[6] and s[7]]',
    ),
    (
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; min_z=min(wall_z)',
        'start_z=start_sample[4]; wall_z=[s[4] for s in after]; max_z=max(wall_z)',
    ),
    (
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) <= -0.02\\nmaterial_approach = start_z-min_z >= 0.015',
        'strafe_requested_toward_wall = strafe_move is not None and float(strafe_move.group(3)) >= 0.02\\nmaterial_approach = max_z-start_z >= 0.015',
    ),
    (
        'if stable_plateau and (start_z-min(candidate_z)>=0.015 or strafe_requested_toward_wall):',
        'if stable_plateau and (max(candidate_z)-start_z>=0.015 or strafe_requested_toward_wall):',
    ),
]
for old, new in replacements:
    old_count = verifier_source.count(old)
    new_count = verifier_source.count(new)
    if old_count == 1 and new_count == 0:
        verifier_source = verifier_source.replace(old, new, 1)
    elif old_count == 0 and new_count == 1:
        # An earlier composer already produced the exact target boundary. Preserve it.
        pass
    else:
        raise SystemExit(
            "M1 wall fixture lost both legacy and target verifier boundaries: " + old[:80]
        )'''
    source = source[:start] + new_block + source[end:]
    script.write_text(source, encoding="utf-8")
    print("M1 wall fixture source compatibility: made coordinate-agnostic window/direction composition idempotent")
else:
    print("M1 wall fixture source compatibility already applied")
