#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #347 removed the previous duplicate-sibling carry failure but exposed a
# different discontinuity: at walk tick 24 the tracked carriage 7 frame stepped -22.3696 blocks
# while Create's actual native contact application came from sibling carriage 5 (-1.5394). The
# player stayed grounded and broadphase-visible, but carriage-7 local X jumped by 20.3218 blocks.
# Before changing any carry or handoff behavior, correlate a failed walk frame with the exact
# same-tick native-contact carriage and its current local coordinate/broadphase. Read-only only.
# Later cumulative phases can insert accounting between phase154WalkPreviousLocal and the sample
# branch, so anchor on the durable bounded sample-window branch itself rather than historical adjacency.
anchor = '''                            if (player.tickCount <= phase154WalkStartTick + 12) {'''
insert = '''                            if (!phase154WalkSupportHealthy
                                    && Integer.toString(player.tickCount).equals(System.getProperty(
                                        "vs2.phase170NativeContactApplicationTick"))) {
                                int phase177NativeCarriageId = Integer.getInteger(
                                    "vs2.phase170NativeContactApplicationCarriageId", Integer.MIN_VALUE);
                                net.minecraft.world.entity.Entity phase177NativeCarriage = phase177NativeCarriageId == Integer.MIN_VALUE
                                    ? null : client.level.getEntity(phase177NativeCarriageId);
                                if (phase177NativeCarriage != null
                                        && "create:carriage_contraption".equals(
                                            net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(
                                                phase177NativeCarriage.getType()).toString())) {
                                    try {
                                        java.lang.reflect.Method phase177ToLocal = phase177NativeCarriage.getClass().getMethod(
                                            "toLocalVector", net.minecraft.world.phys.Vec3.class, float.class);
                                        net.minecraft.world.phys.Vec3 phase177NativeLocal =
                                            (net.minecraft.world.phys.Vec3) phase177ToLocal.invoke(
                                                phase177NativeCarriage, player.position(), 0.0f);
                                        boolean phase177NativeBroadphase = phase177NativeCarriage.getBoundingBox().inflate(2.0)
                                            .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                                        LOGGER.info(
                                            "GATE_E_PHASE177_FAILED_WALK_NATIVE_FRAME player_tick={} tracked_carriage_id={} tracked_local={} tracked_support_now={} native_carriage_id={} native_local={} native_broadphase={} on_ground={} same_carriage={} tracked_world={} native_world={} read_only=true diagnostic_state_only=true",
                                            player.tickCount, phase154Carriage.getId(), phase154Local, phase154SupportNow,
                                            phase177NativeCarriageId, phase177NativeLocal, phase177NativeBroadphase,
                                            player.onGround(), phase177NativeCarriageId == phase154Carriage.getId(),
                                            phase154Carriage.position(), phase177NativeCarriage.position());
                                    } catch (ReflectiveOperationException | RuntimeException phase177Exception) {
                                        LOGGER.info(
                                            "GATE_E_PHASE177_FAILED_WALK_NATIVE_FRAME player_tick={} tracked_carriage_id={} native_carriage_id={} error={} read_only=true diagnostic_state_only=true",
                                            player.tickCount, phase154Carriage.getId(), phase177NativeCarriageId,
                                            phase177Exception.getClass().getSimpleName());
                                    }
                                } else {
                                    LOGGER.info(
                                        "GATE_E_PHASE177_FAILED_WALK_NATIVE_FRAME player_tick={} tracked_carriage_id={} native_carriage_id={} native_entity_resolved=false read_only=true diagnostic_state_only=true",
                                        player.tickCount, phase154Carriage.getId(), phase177NativeCarriageId);
                                }
                            }
''' + anchor

inserted = ""
if "GATE_E_PHASE177_FAILED_WALK_NATIVE_FRAME" not in source:
    count = source.count(anchor)
    if count != 1:
        raise SystemExit(f"Phase 177 expected exactly one durable walk sample-window anchor, found {count}")
    source = source.replace(anchor, insert, 1)
    inserted = insert

# Production-world #350 isolated an accounting oscillator: a compatibility replay from the
# previous sample can resemble the next carriage frame closely enough that Phase137's adaptive
# raw-vs-discounted selector chooses raw and publishes native_carry_healthy=true. Do not rewrite
# that historical selector here (later cumulative phases may legitimately reshape it). Instead,
# at the final cumulative Phase166 health-publication predicate, reject only the narrow case where
# a known previous replay is still inside the bounded disposable walk sample and the selector did
# not discount it. Genuine native carry remains eligible; this adds no movement or physics path.
phase178_old = '''boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && player.onGround()
            && (phase134DriftSq <= 0.01 || phase158LocomotionHealthHold);'''
phase178_new = '''boolean phase178FixtureReplayMasquerade = productionSmokeFixture
            && phase154WalkStarted && !phase154WalkFinished
            && phase137PreviousReplayInSample && !phase137UseReplayDiscount;
        boolean phase134NativeCarryHealthy = phase134TickGap >= 1 && phase134TickGap <= 2
            && player.onGround()
            && !phase178FixtureReplayMasquerade
            && (phase134DriftSq <= 0.01 || phase158LocomotionHealthHold);
        if (phase178FixtureReplayMasquerade) {
            LOGGER.info(
                "GATE_E_PHASE178_FIXTURE_WALK_REPLAY_ACCOUNTING player_tick={} carriage_id={} previous_replay_tick={} raw_drift_sq={} discounted_drift_sq={} selected_raw=true native_health_rejected=true prevents_replay_as_native_health=true fixture_only=true accounting_only=true",
                player.tickCount, carriage.getId(), phase137PreviousReplayTick,
                phase137RawDriftSq, phase137DiscountedDriftSq);
        }'''
phase178_inserted = ""
if "GATE_E_PHASE178_FIXTURE_WALK_REPLAY_ACCOUNTING" not in source:
    count = source.count(phase178_old)
    if count != 1:
        raise SystemExit(f"Phase 178 expected exactly one cumulative Phase166 native-health predicate, found {count}")
    source = source.replace(phase178_old, phase178_new, 1)
    phase178_inserted = phase178_new

required = [
    "GATE_E_PHASE177_FAILED_WALK_NATIVE_FRAME",
    "vs2.phase170NativeContactApplicationTick",
    "vs2.phase170NativeContactApplicationCarriageId",
    "phase154WalkSupportHealthy",
    "phase154SupportNow",
    "toLocalVector",
    "native_broadphase={}",
    "diagnostic_state_only=true",
    "GATE_E_PHASE154_FIXTURE_WALK_SAMPLE",
    "phase154WalkStartTick + 12",
    "GATE_E_PHASE178_FIXTURE_WALK_REPLAY_ACCOUNTING",
    "phase178FixtureReplayMasquerade",
    "phase137PreviousReplayInSample",
    "phase137UseReplayDiscount",
    "phase137DiscountedDriftSq",
    "native_health_rejected=true",
    "prevents_replay_as_native_health=true",
    "accounting_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 177/178 lost walk/native accounting anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted or forbidden in phase178_inserted:
        raise SystemExit("Phase 177/178 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 177: correlates failed walk frames with the exact same-tick native-contact carriage; read-only only")
print("Phase 178: rejects replay-only native-health masquerade at cumulative walk health publication")
