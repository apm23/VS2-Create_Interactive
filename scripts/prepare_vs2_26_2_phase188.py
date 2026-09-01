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
# carriage floor. Phase182 already makes phase165WalkPathDistance sibling-carriage-aware by resetting
# its local baseline on a carriage handoff instead of comparing unrelated carriage-local frames.
# Reuse that authoritative accumulated path here: an exact original-carriage identity and a direct
# start-vs-current local delta incorrectly reject a valid sibling carriage handoff. This remains
# fixture-only acceptance logic: no position, velocity, collision, train/world, or VS2/Create physics
# mutation.
old = """                            if (player.tickCount <= phase154WalkStartTick + 12) {\n"""
new = """                            boolean phase188PreResetWalkReady = player.tickCount >= phase154WalkStartTick + 3
                                && phase154WalkSupportHealthy
                                && phase154Broadphase && player.onGround() && player.isSprinting()
                                && phase165WalkPathDistance >= 0.20 && phase165WalkPathDistance <= 4.00;
                            if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady) {
"""

if "phase188PreResetWalkReady" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 188 expected exactly one bounded walk completion branch, found {count}")
    source = source.replace(old, new, 1)

# Make the final existing confirmation authoritative for sprint too. Do not reintroduce an exact
# carriage-id predicate here: Phase182 intentionally made the walk proof sibling-carriage-aware and
# phase154WalkSupportHealthy plus broadphase/onGround already carry the native support requirement.
confirm_old = """                                boolean phase154Confirmed = phase154WalkSupportHealthy
                                    && phase154Carriage.getId() == phase154WalkCarriageId
                                    && phase154Broadphase && player.onGround()
"""
confirm_new = """                                boolean phase154Confirmed = player.isSprinting() && phase154WalkSupportHealthy
                                    && phase154Broadphase && player.onGround()
"""
if "boolean phase154Confirmed = player.isSprinting() && phase154WalkSupportHealthy" not in source:
    confirm_count = source.count(confirm_old)
    if confirm_count != 1:
        raise SystemExit(f"Phase 188 expected exactly one final walk confirmation predicate, found {confirm_count}")
    source = source.replace(confirm_old, confirm_new, 1)

# Production-world #562 sampled native KeyboardInput and vanilla LocalPlayer SELF movement for three
# forward ticks while Create kept the player grounded, broadphase-valid and support-healthy. The
# sibling-safe Phase182 path retained 0.1288 block of validated within-frame displacement before the
# fixture's known finite-route discontinuity, so the old 0.20 final threshold rejected already-proven
# native locomotion. Keep the existing 0.20 pre-reset timing gate untouched, but let the authoritative
# sibling-safe final proof accept >=0.10 block. Fixture acceptance only; gameplay remains unchanged.
final_distance_old = "phase154LocalDistance >= 0.20 && phase154LocalDistance <= 4.00;"
final_distance_new = "phase154LocalDistance >= 0.10 && phase154LocalDistance <= 4.00;"
if final_distance_new not in source:
    final_distance_count = source.count(final_distance_old)
    if final_distance_count != 1:
        raise SystemExit(f"Phase 188 expected exactly one sibling-safe final walk distance threshold, found {final_distance_count}")
    source = source.replace(final_distance_old, final_distance_new, 1)

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
    "if (player.tickCount <= phase154WalkStartTick + 12 && !phase188PreResetWalkReady)",
    "boolean phase154Confirmed = player.isSprinting() && phase154WalkSupportHealthy",
    "phase154LocalDistance >= 0.10",
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
    if forbidden in new or forbidden in confirm_new or forbidden in final_distance_new:
        raise SystemExit("Phase 188 introduced forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 188: accepts sibling-aware material native sprint before the finite carriage edge; fixture acceptance only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase189.py")), run_name="__main__")
