#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #456 proves all four ordinary walk directions through native Minecraft locomotion.
# Build the existing sustained three-tick acceptance exactly where Phase188 originally owned it,
# but require Minecraft's native sprinting state as part of that acceptance. Production-world #496
# additionally proves the fixture has already produced material native sprint displacement (~0.20
# blocks) while grounded and strictly supported before the longer forward hold walks off the finite
# carriage floor. Accept that material three-tick displacement so reverse/strafe/jump can run before
# the fixture leaves supported geometry. This is fixture-only acceptance logic: no position, velocity,
# collision, train/world, or VS2/Create physics mutation.
old = """                            if (player.tickCount <= phase154WalkStartTick + 12) {\n"""
new = """                            boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 3
                                && phase154WalkSupportHealthy
                                && phase154Carriage.getId() == phase154WalkCarriageId
                                && phase154Broadphase && player.onGround() && player.isSprinting()
                                && phase165WalkPathDistance >= 0.20 && phase165WalkPathDistance <= 4.00
                                && phase154WalkStartLocal != null
                                && Math.hypot(
                                    phase154Local.x - phase154WalkStartLocal.x,
                                    phase154Local.z - phase154WalkStartLocal.z) >= 0.20
                                && Math.hypot(
                                    phase154Local.x - phase154WalkStartLocal.x,
                                    phase154Local.z - phase154WalkStartLocal.z) <= 3.00;
                            if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady) {
"""

if "phase188PreResetWalkReady" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 188 expected exactly one bounded walk completion branch, found {count}")
    source = source.replace(old, new, 1)

# Make the final existing confirmation authoritative for sprint too, rather than merely printing
# sprint state beside a confirmation that could otherwise be true. This is acceptance logic only.
confirm_old = """                                boolean phase154Confirmed = phase154WalkSupportHealthy
                                    && phase154Carriage.getId() == phase154WalkCarriageId
                                    && phase154Broadphase && player.onGround()
"""
confirm_new = """                                boolean phase154Confirmed = player.isSprinting() && phase154WalkSupportHealthy
                                    && phase154Carriage.getId() == phase154WalkCarriageId
                                    && phase154Broadphase && player.onGround()
"""
if "boolean phase154Confirmed = player.isSprinting() && phase154WalkSupportHealthy" not in source:
    confirm_count = source.count(confirm_old)
    if confirm_count != 1:
        raise SystemExit(f"Phase 188 expected exactly one final walk confirmation predicate, found {confirm_count}")
    source = source.replace(confirm_old, confirm_new, 1)

# Keep the native sprint state explicit on the existing walk confirmation marker.
sprint_log_old = '"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED player_tick={} carriage_id={} local_start={} local_end={} local_distance={} duration_ticks={} on_ground={} broadphase={} support_healthy={} confirmed={} fixture_only=true",'
sprint_log_new = '"GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED player_tick={} carriage_id={} local_start={} local_end={} local_distance={} duration_ticks={} on_ground={} broadphase={} support_healthy={} confirmed={} sprinting={} fixture_only=true",'
sprint_args_old = "phase154WalkSupportHealthy, phase154Confirmed);"
sprint_args_new = "phase154WalkSupportHealthy, phase154Confirmed, player.isSprinting());"
if "confirmed={} sprinting={} fixture_only=true" not in source:
    log_count = source.count(sprint_log_old)
    args_count = source.count(sprint_args_old)
    if log_count != 1 or args_count != 1:
        raise SystemExit(
            f"Phase 188 expected one existing walk confirmation logger and argument tail, found log={log_count} args={args_count}"
        )
    source = source.replace(sprint_log_old, sprint_log_new, 1)
    source = source.replace(sprint_args_old, sprint_args_new, 1)

required = [
    "phase188PreResetWalkReady",
    "player.tickCount >= phase154WalkStartTick + 3",
    "phase154WalkSupportHealthy",
    "phase154Broadphase && player.onGround() && player.isSprinting()",
    "phase165WalkPathDistance >= 0.20",
    "Math.hypot(",
    "phase154Local.x - phase154WalkStartLocal.x",
    "phase154Local.z - phase154WalkStartLocal.z",
    "if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady)",
    "boolean phase154Confirmed = player.isSprinting() && phase154WalkSupportHealthy",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "confirmed={} sprinting={} fixture_only=true",
    "phase154Confirmed, player.isSprinting()",
    "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 188 lost native sprint-proof anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in new or forbidden in confirm_new:
        raise SystemExit("Phase 188 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 188: accepts material native sprint before the finite carriage edge; fixture acceptance only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase189.py")), run_name="__main__")
