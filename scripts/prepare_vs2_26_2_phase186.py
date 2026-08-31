#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
move_java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerMoveTrace.java"
setpos_java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerSetPosTrace.java"

# Production-world #376 proved Create's native active-carriage contact motion exactly matches the
# carriage frame step, yet the LocalPlayer develops an alternating ~0.60-block carriage-relative
# residual after a valid sibling handoff while remaining grounded, broadphase-valid and
# support_healthy. The historical move/setPos probes stop after fixed call-count caps long before
# this tick window, so the actual position-mutating call site is invisible. Keep those probes
# read-only, but retain them specifically for the bounded production-smoke walk window and add
# player_tick to the records. No movement/collision/carry/train/world/physics behavior is changed.

move = move_java.read_text(encoding="utf-8")
move = move.replace(
    "        if (index > 220) return;\n",
    "        boolean phase186WalkWindow = java.lang.Boolean.getBoolean(\"vs2.productionSmokeFixture\")\n"
    "            && self.tickCount >= 20 && self.tickCount <= 55;\n"
    "        if (index > 220 && !phase186WalkWindow) return;\n",
    1,
)
move = move.replace(
    '            "GATE_E_LOCALPLAYER_ENTITY_MOVE_HEAD index={} mover={} requested={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",\n'
    '            index, String.valueOf(type), requested.x, requested.y, requested.z,\n',
    '            "GATE_E_LOCALPLAYER_ENTITY_MOVE_HEAD index={} player_tick={} mover={} requested={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",\n'
    '            index, self.tickCount, String.valueOf(type), requested.x, requested.y, requested.z,\n',
    1,
)
move = move.replace(
    "        if (index <= 0 || index > 220) return;\n",
    "        boolean phase186WalkWindow = java.lang.Boolean.getBoolean(\"vs2.productionSmokeFixture\")\n"
    "            && self.tickCount >= 20 && self.tickCount <= 55;\n"
    "        if (index <= 0 || (index > 220 && !phase186WalkWindow)) return;\n",
    1,
)
move = move.replace(
    '            "GATE_E_LOCALPLAYER_ENTITY_MOVE_RETURN index={} mover={} requested={},{},{} actual={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",\n'
    '            index, String.valueOf(type), requested.x, requested.y, requested.z,\n',
    '            "GATE_E_LOCALPLAYER_ENTITY_MOVE_RETURN index={} player_tick={} mover={} requested={},{},{} actual={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",\n'
    '            index, self.tickCount, String.valueOf(type), requested.x, requested.y, requested.z,\n',
    1,
)
if "phase186WalkWindow" not in move or "player_tick={}" not in move:
    raise SystemExit("Phase 186 could not extend Entity.move telemetry into bounded walk window")
move_java.write_text(move, encoding="utf-8")

setpos = setpos_java.read_text(encoding="utf-8")
setpos = setpos.replace(
    "        if (index > 180) return;\n",
    "        boolean phase186WalkWindow = java.lang.Boolean.getBoolean(\"vs2.productionSmokeFixture\")\n"
    "            && self.tickCount >= 20 && self.tickCount <= 55;\n"
    "        if (index > 180 && !phase186WalkWindow) return;\n",
    1,
)
setpos = setpos.replace(
    '            "GATE_E_LOCALPLAYER_SET_POS index={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",\n'
    '            index,\n',
    '            "GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",\n'
    '            index, self.tickCount,\n',
    1,
)
if "phase186WalkWindow" not in setpos or "player_tick={}" not in setpos:
    raise SystemExit("Phase 186 could not extend setPos telemetry into bounded walk window")
setpos_java.write_text(setpos, encoding="utf-8")

for text in (move, setpos):
    for forbidden in ["setDeltaMovement(", ".teleport(", "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue("]:
        if forbidden in text and forbidden not in ("setDeltaMovement(",):
            raise SystemExit("Phase 186 encountered unexpected mutation token: " + forbidden)

print("Phase 186: extends read-only LocalPlayer move/setPos caller telemetry through the bounded walk window")
