#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
collide = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderTrace.java"
setpos = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerSetPosTrace.java"

# Ceiling proof correlation only. Add player tick to already-existing read-only
# local-frame/collide/setPos telemetry. Later composition phases may already have
# added the same tick field, so each anchor is deliberately idempotent.
# No movement, collision, input, world, train, camera, ownership, or physics
# value is changed.
s = probe.read_text(encoding="utf-8")
ready = '"GATE_E_CLIENT_STATE player_tick={} player_pos={},{},{} player_box='
if ready not in s:
    old = '"GATE_E_CLIENT_STATE player_pos={},{},{} player_box='
    new = ready
    if old not in s:
        raise SystemExit("ceiling trace could not find GateE state format")
    s = s.replace(old, new, 1)
    old_args = '''                player.getX(), player.getY(), player.getZ(),\n                playerBox.minX'''
    new_args = '''                player.tickCount,\n                player.getX(), player.getY(), player.getZ(),\n                playerBox.minX'''
    if old_args not in s:
        raise SystemExit("ceiling trace could not find GateE state arguments")
    s = s.replace(old_args, new_args, 1)
probe.write_text(s, encoding="utf-8")

s = collide.read_text(encoding="utf-8")
ready = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}"'
if ready not in s:
    old = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",\n            index,'
    new = '"GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",\n            index, entity.tickCount,'
    if old not in s:
        raise SystemExit("ceiling trace could not find nonzero LocalPlayer collide marker")
    s = s.replace(old, new, 1)
collide.write_text(s, encoding="utf-8")

s = setpos.read_text(encoding="utf-8")
ready = '"GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}"'
if ready not in s:
    old = '"GATE_E_LOCALPLAYER_SET_POS index={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",\n            index,'
    new = '"GATE_E_LOCALPLAYER_SET_POS index={} player_tick={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",\n            index, self.tickCount,'
    if old not in s:
        raise SystemExit("ceiling trace could not find LocalPlayer setPos marker")
    s = s.replace(old, new, 1)
setpos.write_text(s, encoding="utf-8")

for text, required in [
    (probe.read_text(encoding="utf-8"), "GATE_E_CLIENT_STATE player_tick={}"),
    (collide.read_text(encoding="utf-8"), "GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} player_tick={}"),
    (setpos.read_text(encoding="utf-8"), "GATE_E_LOCALPLAYER_SET_POS index={} player_tick={}"),
]:
    if required not in text:
        raise SystemExit("ceiling trace verification failed: " + required)

print("M1_CEILING_CONTACT_CORRELATION_TRACE prepared=true read_only=true idempotent_tick_anchors=true local_frame=create_worldToLocalPos gameplay_mutated=false collision_mutated=false input_mutated=false camera_mutated=false")
