#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #368 reached the real moving train with strict support, native Create carry,
# interaction and authoritative placement intact, but the walk proof saw a same-carriage local
# coordinate oscillation at ticks 32-33 (about 5.376 blocks each way) while the player remained
# grounded/broadphase-supported and the native contact application came from that same carriage.
# Before changing any carry/collision behavior, compare Create's toLocalVector at partial ticks
# 0.0/0.5/1.0 at the existing Phase163 walk sample site. This distinguishes an interpolation/
# transform-accounting seam from genuine player displacement. Read-only production-smoke
# telemetry only; no player, train, world, collision, carry vector, or VS2 physics mutation.
marker = 'GATE_E_PHASE183_WALK_TRANSFORM_SEAM'
if marker not in source:
    phase163_marker = 'GATE_E_PHASE163_WALK_WORLD_FRAME'
    marker_pos = source.find(phase163_marker)
    if marker_pos < 0:
        raise SystemExit('Phase 183 could not find Phase163 walk world-frame telemetry')
    logger_pos = source.rfind('                                LOGGER.info(', 0, marker_pos)
    if logger_pos < 0:
        raise SystemExit('Phase 183 could not locate Phase163 logger insertion point')
    line_start = source.rfind('\n', 0, logger_pos) + 1
    indent = source[line_start:logger_pos]
    probe = (
        f'{indent}net.minecraft.world.phys.Vec3 phase183Local0 = (net.minecraft.world.phys.Vec3) phase154ToLocal.invoke(\n'
        f'{indent}    phase154Carriage, player.position(), 0.0f);\n'
        f'{indent}net.minecraft.world.phys.Vec3 phase183LocalHalf = (net.minecraft.world.phys.Vec3) phase154ToLocal.invoke(\n'
        f'{indent}    phase154Carriage, player.position(), 0.5f);\n'
        f'{indent}net.minecraft.world.phys.Vec3 phase183Local1 = (net.minecraft.world.phys.Vec3) phase154ToLocal.invoke(\n'
        f'{indent}    phase154Carriage, player.position(), 1.0f);\n'
        f'{indent}LOGGER.info(\n'
        f'{indent}    "GATE_E_PHASE183_WALK_TRANSFORM_SEAM player_tick={{}} carriage_id={{}} local_sample={{}} local_p0={{}} local_p05={{}} local_p1={{}} p0_to_p1={{}} measured_step={{}} carriage_y_rot={{}} carriage_x_rot={{}} player_world={{}} carriage_world={{}} native_application_tick={{}} native_application_carriage={{}} on_ground={{}} broadphase={{}} fixture_only=true read_only=true",\n'
        f'{indent}    player.tickCount, phase154Carriage.getId(), phase154Local, phase183Local0, phase183LocalHalf, phase183Local1,\n'
        f'{indent}    phase183Local0.distanceTo(phase183Local1), phase154Step, phase154Carriage.getYRot(), phase154Carriage.getXRot(),\n'
        f'{indent}    player.position(), phase154Carriage.position(),\n'
        f'{indent}    System.getProperty("vs2.phase170NativeContactApplicationTick", "missing"),\n'
        f'{indent}    System.getProperty("vs2.phase170NativeContactApplicationCarriageId", "missing"),\n'
        f'{indent}    player.onGround(), phase154Broadphase);\n'
    )
    source = source[:line_start] + probe + source[line_start:]

required = [
    marker,
    'phase154ToLocal.invoke',
    'phase183Local0',
    'phase183LocalHalf',
    'phase183Local1',
    'phase183Local0.distanceTo(phase183Local1)',
    'phase154Carriage.getYRot()',
    'phase154Carriage.getXRot()',
    'vs2.phase170NativeContactApplicationTick',
    'vs2.phase170NativeContactApplicationCarriageId',
    'fixture_only=true read_only=true',
    'GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit('Phase 183 lost transform-seam telemetry anchors: ' + ', '.join(missing))

for forbidden in [
    'player.setPos(', 'player.setDeltaMovement(', 'player.move(', '.teleport', 'setBlock(',
    'setSchedule', 'setTrain', 'setVelocity', 'syncCarriage(', 'cir.setReturnValue(',
]:
    if forbidden in probe if marker not in source else False:
        raise SystemExit('Phase 183 introduced forbidden mutation: ' + forbidden)

client_probe.write_text(source, encoding='utf-8')
print('Phase 183: traces partial-tick Create local-transform seam during bounded walk; read-only only')
