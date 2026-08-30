#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Phase 154 proved a short five-tick normal-key walk can displace the LocalPlayer while
# remaining grounded and inside one moving Create carriage frame. Strengthen only the
# disposable production-smoke fixture: hold the same vanilla forward key for twenty ticks
# and require support continuity for the whole interval. No player position/velocity,
# collision, train, world, inventory, VS2 physics, or Create carry state is mutated here.
old_window = "if (player.tickCount <= phase154WalkStartTick + 5) {"
new_window = "if (player.tickCount <= phase154WalkStartTick + 20) {"
old_limit = "&& phase154LocalDistance >= 0.05 && phase154LocalDistance <= 1.50;"
new_limit = "&& phase154LocalDistance >= 0.20 && phase154LocalDistance <= 6.00;"
old_log = '"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED player_tick={} carriage_id={} local_start={} local_end={} local_distance={} on_ground={} broadphase={} support_healthy={} confirmed={} fixture_only=true",'
new_log = '"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED player_tick={} carriage_id={} local_start={} local_end={} local_distance={} duration_ticks={} on_ground={} broadphase={} support_healthy={} confirmed={} fixture_only=true",'
old_args = "phase154LocalDistance, player.onGround(), phase154Broadphase,\n                                    phase154WalkSupportHealthy, phase154Confirmed);"
new_args = "phase154LocalDistance, player.tickCount - phase154WalkStartTick, player.onGround(), phase154Broadphase,\n                                    phase154WalkSupportHealthy, phase154Confirmed);"

for old, new, label in [
    (old_window, new_window, "walk window"),
    (old_limit, new_limit, "walk distance bound"),
    (old_log, new_log, "confirmation telemetry"),
    (old_args, new_args, "confirmation arguments"),
]:
    if new not in source:
        if old not in source:
            raise SystemExit(f"Phase 155 could not find {label} anchor")
        source = source.replace(old, new, 1)

required = [
    "phase154WalkStartTick + 20",
    "phase154LocalDistance >= 0.20",
    "phase154LocalDistance <= 6.00",
    "duration_ticks={}",
    "player.tickCount - phase154WalkStartTick",
    "phase154WalkSupportHealthy",
    "client.options.keyUp.setDown(true)",
    "client.options.keyUp.setDown(false)",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 155 lost extended walk anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport", "setBlock(",
    "setSchedule", "setTrain", "setVelocity", "syncCarriage(",
]:
    if forbidden in source[source.find(new_window):source.find(new_window) + 6000]:
        raise SystemExit("Phase 155 found forbidden movement/world/train mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 155: extends fixture-only normal forward-key walking proof to twenty ticks with continuous same-carriage support; no production movement or physics mutation")
