#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 100 loaded Phase 79 but emitted no replay marker. Do not change movement
# semantics yet; expose the exact guard state and contact motion for the carriage
# that captured the genuine Create contact baseline.
field_anchor = '''    private static int carryReplayPlayerTick = Integer.MIN_VALUE;\n'''
field_insert = '''    private static int carryReplayPlayerTick = Integer.MIN_VALUE;\n    private static int carryReplayGuardSamples;\n'''
if "carryReplayGuardSamples" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 80 could not find Phase 79 field anchor")
    source = source.replace(field_anchor, field_insert, 1)

guard_anchor = '''            if (carryBaselineCaptured\n                && carryCarriageEntityId == carriage.getId()'''
guard_insert = '''            if (carryBaselineCaptured && carryReplayGuardSamples < 32) {\n                carryReplayGuardSamples++;\n                LOGGER.info(\n                    "GATE_E_PHASE80_REPLAY_GUARD sample={} baseline={} saved_carriage_id={} current_carriage_id={} same_carriage={} player_tick={} last_replay_tick={} on_ground={} collision_eligible={} broadphase_overlap={} carriage_pos={},{},{} player_pos={},{},{}",\n                    carryReplayGuardSamples, carryBaselineCaptured, carryCarriageEntityId, carriage.getId(),\n                    carryCarriageEntityId == carriage.getId(), player.tickCount, carryReplayPlayerTick,\n                    player.onGround(), collisionEligible, broadphaseOverlap,\n                    carriage.getX(), carriage.getY(), carriage.getZ(),\n                    player.getX(), player.getY(), player.getZ());\n            }\n\n            if (carryBaselineCaptured\n                && carryCarriageEntityId == carriage.getId()'''
if "GATE_E_PHASE80_REPLAY_GUARD" not in source:
    if guard_anchor not in source:
        raise SystemExit("Phase 80 could not find Phase 79 replay guard")
    source = source.replace(guard_anchor, guard_insert, 1)

motion_anchor = '''                        if (rawMotion instanceof Vec3 contactMotion\n                            && (contactMotion.x * contactMotion.x + contactMotion.z * contactMotion.z) > 1.0E-10) {'''
motion_insert = '''                        if (rawMotion instanceof Vec3 contactMotion) {\n                            if (carryReplayGuardSamples <= 32) {\n                                LOGGER.info(\n                                    "GATE_E_PHASE80_REPLAY_MOTION carriage_id={} player_tick={} motion={},{},{} motion_sq={}",\n                                    carriage.getId(), player.tickCount,\n                                    contactMotion.x, contactMotion.y, contactMotion.z, contactMotion.lengthSqr());\n                            }\n                            if ((contactMotion.x * contactMotion.x + contactMotion.z * contactMotion.z) > 1.0E-10) {'''
if "GATE_E_PHASE80_REPLAY_MOTION" not in source:
    if motion_anchor not in source:
        raise SystemExit("Phase 80 could not find Phase 79 motion guard")
    source = source.replace(motion_anchor, motion_insert, 1)
    # Close the extra nested motion-magnitude if before the rawMotion block closes.
    close_anchor = '''                                    player.getX(), player.getY(), player.getZ());\n                            }\n                        }\n                    }'''
    close_replacement = '''                                    player.getX(), player.getY(), player.getZ());\n                            }\n                            }\n                        }\n                    }'''
    if close_anchor not in source:
        raise SystemExit("Phase 80 could not close nested motion guard")
    source = source.replace(close_anchor, close_replacement, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 80: traced Phase 79 carry replay guard state and exact saved-carriage contact motion; no additional movement behavior")
