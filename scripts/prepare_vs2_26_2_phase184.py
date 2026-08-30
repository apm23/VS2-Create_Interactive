#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #370 proved the existing Create-filtered recovery keeps the player carriage-local
# stable through tick 33 after native contact disappears at tick 22. The failure starts only after
# Phase81's simplified-collider shape probe drops physical_support=false even though the bounded walk
# is still on the same active carriage, grounded, broadphase-overlapping, Phase154 support_now remains
# true, and the immediately previous tick replay preserved the local frame. Preserve that already-
# validated support continuity only for the disposable bounded production-smoke walk and only while
# replay continuity is consecutive and no same-tick native Create application exists. No carry vector
# is synthesized or clamped; the existing Create-computed/collision-filtered replay remains authoritative.
# Keep phase81PhysicalSupport text visible in the final Phase85 guard so cumulative Phase132 can still
# add its independently bounded one-tick grace without mistaking this later continuity patch for a
# missing support predicate.

marker = "GATE_E_PHASE184_BOUNDED_SUPPORT_CONTINUITY"
inserted = ""
if marker not in source:
    decl_token = "boolean phase161SupportedLocomotionNativeLoss ="
    decl_pos = source.find(decl_token)
    if decl_pos < 0:
        raise SystemExit("Phase 184 could not locate Phase161 supported-loss declaration")
    line_start = source.rfind("\n", 0, decl_pos) + 1
    indent = source[line_start:decl_pos]
    support_decl = (
        f'{indent}boolean phase184BoundedSupportContinuity = productionSmokeFixture\n'
        f'{indent}    && phase154WalkStarted && !phase154WalkFinished && phase154WalkSupportHealthy\n'
        f'{indent}    && carriage.getId() == phase154WalkCarriageId\n'
        f'{indent}    && collisionEligible && broadphaseOverlap && player.onGround()\n'
        f'{indent}    && carryReplayPlayerTick == player.tickCount - 1\n'
        f'{indent}    && !Integer.toString(player.tickCount).equals(System.getProperty(\n'
        f'{indent}        "vs2.phase170NativeContactApplicationTick"));\n'
        f'{indent}boolean phase184ReplaySupport = phase81PhysicalSupport || phase184BoundedSupportContinuity;\n'
        f'{indent}if (phase184BoundedSupportContinuity) {{\n'
        f'{indent}    LOGGER.info(\n'
        f'{indent}        "GATE_E_PHASE184_BOUNDED_SUPPORT_CONTINUITY carriage_id={{}} player_tick={{}} strict_support={{}} walk_support_healthy={{}} collision_eligible={{}} broadphase={{}} grounded={{}} previous_replay_tick={{}} same_tick_native_application=false fixture_only=true bounded_continuity=true",\n'
        f'{indent}        carriage.getId(), player.tickCount, phase81PhysicalSupport, phase154WalkSupportHealthy,\n'
        f'{indent}        collisionEligible, broadphaseOverlap, player.onGround(), carryReplayPlayerTick);\n'
        f'{indent}}}\n'
    )
    source = source[:line_start] + support_decl + source[line_start:]
    inserted += support_decl

    # Extend only the Phase161 bounded recovery predicate, not unrelated support checks.
    decl_pos = source.find(decl_token, line_start + len(support_decl))
    decl_end = source.find(";", decl_pos)
    if decl_end < 0:
        raise SystemExit("Phase 184 could not bound Phase161 supported-loss declaration")
    predicate = source[decl_pos:decl_end + 1]
    strict = "phase81PhysicalSupport && collisionEligible && broadphaseOverlap && player.onGround()"
    relaxed = "phase184ReplaySupport && collisionEligible && broadphaseOverlap && player.onGround()"
    if strict in predicate:
        predicate = predicate.replace(strict, relaxed, 1)
    elif relaxed not in predicate:
        raise SystemExit("Phase 184 could not find strict support clause inside Phase161 predicate")
    source = source[:decl_pos] + predicate + source[decl_end + 1:]

    # Widen final Phase85 replay support while retaining the literal Phase81 predicate. Phase132 runs
    # again in the cumulative Phase98 path and searches this exact final guard before adding grace.
    replay_token = "carryReplayPlayerTick != player.tickCount"
    replay_pos = source.find(replay_token)
    if replay_pos < 0:
        raise SystemExit("Phase 184 could not locate final Phase85 replay guard")
    if_pos = source.rfind("if (", 0, replay_pos)
    if_end = source.find(") {", replay_pos)
    if if_pos < 0 or if_end < 0:
        raise SystemExit("Phase 184 could not bound final Phase85 replay guard")
    final_guard = source[if_pos:if_end + 3]
    expanded_support = "(phase81PhysicalSupport || phase184BoundedSupportContinuity)"
    if "phase81PhysicalSupport" in final_guard and "phase184BoundedSupportContinuity" not in final_guard:
        final_guard = final_guard.replace("phase81PhysicalSupport", expanded_support, 1)
    elif expanded_support not in final_guard:
        raise SystemExit("Phase 184 could not find Phase81 support in final replay guard")
    source = source[:if_pos] + final_guard + source[if_end + 3:]

# Production-world #373 isolated the remaining walk failure to Create's interpolation frame rather
# than real carriage-local drift. At tick 39 on carriage 4, Phase183 measured local_p0=(6.402...,1.5)
# but local_p1=(-5.402...,-0.5), exactly matching the previous stable local frame; p0_to_p1 equaled
# the entire 11.973-block rejected walk step. The player remained grounded and broadphase-supported.
# Use the end-of-tick Create transform (partial tick 1.0) for the bounded walk verifier so it compares
# player samples in the same completed carriage frame. This changes fixture accounting only: it does
# not alter player position, velocity, collision, Create carry, train state, world blocks, or VS2 physics.
walk_local_old = '''                        net.minecraft.world.phys.Vec3 phase154Local = (net.minecraft.world.phys.Vec3) phase154ToLocal.invoke(
                            phase154Carriage, player.position(), 0.0f);'''
walk_local_new = '''                        net.minecraft.world.phys.Vec3 phase154Local = (net.minecraft.world.phys.Vec3) phase154ToLocal.invoke(
                            phase154Carriage, player.position(), 1.0f);'''
if walk_local_old in source:
    if source.count(walk_local_old) != 1:
        raise SystemExit("Phase 184 found ambiguous Phase154 walk-local transform site")
    source = source.replace(walk_local_old, walk_local_new, 1)
elif walk_local_new not in source:
    raise SystemExit("Phase 184 could not align Phase154 walk accounting to end-tick carriage frame")

required = [
    marker,
    "phase184BoundedSupportContinuity",
    "phase184ReplaySupport",
    "phase154WalkStarted && !phase154WalkFinished && phase154WalkSupportHealthy",
    "carriage.getId() == phase154WalkCarriageId",
    "carryReplayPlayerTick == player.tickCount - 1",
    "vs2.phase170NativeContactApplicationTick",
    "phase184ReplaySupport && collisionEligible && broadphaseOverlap && player.onGround()",
    "(phase81PhysicalSupport || phase184BoundedSupportContinuity)",
    "carryReplayPlayerTick != player.tickCount",
    "GATE_E_PHASE85_CARRY_REPLAY",
    "fixture_only=true bounded_continuity=true",
    "phase154Carriage, player.position(), 1.0f",
    "GATE_E_PHASE183_WALK_TRANSFORM_SEAM",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 184 lost bounded support/end-tick accounting anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 184 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 184: preserves bounded support continuity and aligns walk accounting to Create end-tick carriage frame; no gameplay mutation")
