#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world run 33348083330 started the bounded walk on carriage 2 at tick 17 after the
# existing three-tick settled predicate, then the end-tick local frame jumped 6.998 blocks at tick
# 18 and support became unhealthy. The following carriage 4 interval lasted only ticks 19-22 before
# another handoff. These are short-lived fixture frame windows, not evidence for a new physics
# correction. Keep the conservative five-tick readiness path for health-only readiness.
#
# Production-world #411 then proved that the conservative five-tick gate can starve the walk proof:
# carriage 4 had strict support plus exact same-carriage native Create applications on ticks 60-61,
# but native application ended at tick 62, so the five-tick counter could never complete. Treat two
# consecutive ready ticks as sufficient only when the current tick itself has the exact Phase170
# same-carriage native application evidence. Health-only readiness still requires five ticks.
#
# Production-world #412 finally started the walk, remained grounded/broadphase-supported with zero
# carriage-local displacement through tick 33, then hit the known finite-route reset at tick 34.
# Before changing any movement behavior, trace whether the ordinary key pulse actually reaches the
# LocalPlayer input object. Reflection keeps this diagnostic independent of 26.2 input field names and
# is read-only: it logs the runtime input class plus its primitive field values beside KeyMapping state.
#
# Production-world #413 proved the runtime input object is KeyboardInput, but getDeclaredFields() on
# that concrete class exposed no primitive movement state at all. That leaves the important inherited
# Input fields invisible. Walk the input class hierarchy and log primitive fields from every level so
# the next real-world run can distinguish a KeyMapping-only pulse from an actually sampled movement
# impulse. This remains read-only telemetry; no player movement, carry vector, collision, train/world
# state, inventory, Create behavior, or VS2 physics is changed.
#
# Production-world #489 proves the four-tick post-rebase delay now defeats the later Phase194 hardening:
# carriage 7 had strict support, exact native Create application, and zero carriage-local drift on
# ticks 25-28, but readiness stayed false solely because rebase age was 0-3. At tick 29 a sibling
# carriage native application arrived before the Phase185/172 sibling guard could be prearmed and the
# stable interval was lost. Phase194 now independently requires three fresh ready ticks plus a strict
# next-tick confirmation before starting the walk, so the old four-tick delay is redundant. Restore the
# historical two-tick rebase settle boundary: this lets the existing Phase172 guard prearm inside the
# proven stable carry window while Phase194 still prevents a two-tick startup transient from starting
# locomotion. Fixture accounting only; no movement/carry vector/physics mutation is introduced.
#
# Production-world #490 exposed a harness contamination boundary, not a new gameplay-physics failure:
# Phase185 accumulated ready ticks 34-36 while the bounded fixture-contact acquisition was still active
# (attempts continued through player tick 50). Phase194 then deliberately withheld that assistance on
# tick 37 for its strict confirmation, where the apparent stable local frame immediately disappeared.
# Do not arm locomotion from fixture-assisted samples. Require the existing 48-attempt acquisition to
# be complete before Phase185 can accumulate walk readiness. This is fixture-only acceptance gating;
# production carry, player motion, collision response, train state, and VS2/Create physics are unchanged.
#
# The cumulative client also contains another unrelated rebase-age >=2 expression, so scope this
# patch to Phase185's complete walk-readiness clause instead of counting the token globally.
old_readiness = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
old_phase192_readiness = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 4);'''
new_readiness = '''                        boolean phase185WalkReadyNow = phase154SupportNow
                            && phase81PhysicalSupport
                            && phase185FreshNativeEvidence
                            && (!productionSmokeFixture || fixtureContactAcquireTicks >= 48)
                            && (carryBaselineRebaseTick == Integer.MIN_VALUE
                                || player.tickCount - carryBaselineRebaseTick >= 2);'''
if new_readiness not in source:
    if source.count(old_readiness) == 1:
        source = source.replace(old_readiness, new_readiness, 1)
    elif source.count(old_phase192_readiness) == 1:
        source = source.replace(old_phase192_readiness, new_readiness, 1)
    else:
        raise SystemExit("Phase 192 expected one scoped Phase185 readiness clause")

old_ready = '''                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && phase185WalkReadyTicks >= 3) {'''
old_phase192_ready = '''                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && phase185WalkReadyTicks >= 5) {'''
new_ready = '''                        if (!phase154WalkStarted && phase185WalkReadyNow
                                && phase185WalkReadyCarriageId == phase154Carriage.getId()
                                && (phase185WalkReadyTicks >= 5
                                    || (phase185NativeApplicationFresh && phase185WalkReadyTicks >= 2))) {'''
if new_ready not in source:
    if source.count(old_phase192_ready) == 1:
        source = source.replace(old_phase192_ready, new_ready, 1)
    elif source.count(old_ready) == 1:
        source = source.replace(old_ready, new_ready, 1)
    else:
        raise SystemExit("Phase 192 expected one scoped Phase185 ready-tick branch")

input_anchor = '''                                LOGGER.info(
                                    "GATE_E_PHASE167_WALK_NATIVE_MOTION'''
input_probe = '''                                String phase192InputState = "input_field_missing";
                                try {
                                    java.lang.reflect.Field phase192InputField = null;
                                    Class<?> phase192PlayerClass = player.getClass();
                                    while (phase192PlayerClass != null && phase192InputField == null) {
                                        try {
                                            phase192InputField = phase192PlayerClass.getDeclaredField("input");
                                        } catch (NoSuchFieldException ignored) {
                                            phase192PlayerClass = phase192PlayerClass.getSuperclass();
                                        }
                                    }
                                    if (phase192InputField != null) {
                                        phase192InputField.setAccessible(true);
                                        Object phase192Input = phase192InputField.get(player);
                                        if (phase192Input == null) {
                                            phase192InputState = "null";
                                        } else {
                                            StringBuilder phase192InputBuilder = new StringBuilder(
                                                phase192Input.getClass().getName());
                                            Class<?> phase192InputClass = phase192Input.getClass();
                                            while (phase192InputClass != null) {
                                                for (java.lang.reflect.Field phase192Field : phase192InputClass.getDeclaredFields()) {
                                                    Class<?> phase192Type = phase192Field.getType();
                                                    if (phase192Type == boolean.class || phase192Type == float.class
                                                            || phase192Type == double.class || phase192Type == int.class) {
                                                        phase192Field.setAccessible(true);
                                                        phase192InputBuilder.append(';')
                                                            .append(phase192InputClass.getSimpleName()).append('.')
                                                            .append(phase192Field.getName()).append('=')
                                                            .append(String.valueOf(phase192Field.get(phase192Input)));
                                                    }
                                                }
                                                phase192InputClass = phase192InputClass.getSuperclass();
                                            }
                                            phase192InputState = phase192InputBuilder.toString();
                                        }
                                    }
                                } catch (ReflectiveOperationException | RuntimeException phase192InputException) {
                                    phase192InputState = "error=" + phase192InputException.getClass().getSimpleName();
                                }
                                LOGGER.info(
                                    "GATE_E_PHASE192_LOCAL_INPUT player_tick={} carriage_id={} key_up={} key_down={} input_state={} delta={} on_ground={} broadphase={} read_only=true",
                                    player.tickCount, phase154Carriage.getId(), client.options.keyUp.isDown(),
                                    client.options.keyDown.isDown(), phase192InputState, player.getDeltaMovement(),
                                    player.onGround(), phase154Broadphase);
                                LOGGER.info(
                                    "GATE_E_PHASE167_WALK_NATIVE_MOTION'''
if "GATE_E_PHASE192_LOCAL_INPUT" not in source:
    count = source.count(input_anchor)
    if count != 1:
        raise SystemExit(f"Phase 192 expected one Phase167 sampled-input telemetry anchor, found {count}")
    source = source.replace(input_anchor, input_probe, 1)
elif "phase192InputClass.getSuperclass()" not in source:
    old_concrete_loop = '''                                            for (java.lang.reflect.Field phase192Field : phase192Input.getClass().getDeclaredFields()) {
                                                Class<?> phase192Type = phase192Field.getType();
                                                if (phase192Type == boolean.class || phase192Type == float.class
                                                        || phase192Type == double.class || phase192Type == int.class) {
                                                    phase192Field.setAccessible(true);
                                                    phase192InputBuilder.append(';').append(phase192Field.getName())
                                                        .append('=').append(String.valueOf(phase192Field.get(phase192Input)));
                                                }
                                            }'''
    new_hierarchy_loop = '''                                            Class<?> phase192InputClass = phase192Input.getClass();
                                            while (phase192InputClass != null) {
                                                for (java.lang.reflect.Field phase192Field : phase192InputClass.getDeclaredFields()) {
                                                    Class<?> phase192Type = phase192Field.getType();
                                                    if (phase192Type == boolean.class || phase192Type == float.class
                                                            || phase192Type == double.class || phase192Type == int.class) {
                                                        phase192Field.setAccessible(true);
                                                        phase192InputBuilder.append(';')
                                                            .append(phase192InputClass.getSimpleName()).append('.')
                                                            .append(phase192Field.getName()).append('=')
                                                            .append(String.valueOf(phase192Field.get(phase192Input)));
                                                    }
                                                }
                                                phase192InputClass = phase192InputClass.getSuperclass();
                                            }'''
    count = source.count(old_concrete_loop)
    if count != 1:
        raise SystemExit(f"Phase 192 expected one concrete-only input reflection loop, found {count}")
    source = source.replace(old_concrete_loop, new_hierarchy_loop, 1)

required = [
    "GATE_E_PHASE185_SETTLED_WALK_READY",
    "phase185WalkReadyCarriageId == phase154Carriage.getId()",
    "phase185WalkReadyTicks >= 5",
    "phase185NativeApplicationFresh && phase185WalkReadyTicks >= 2",
    "fixtureContactAcquireTicks >= 48",
    "!productionSmokeFixture",
    "player.tickCount - carryBaselineRebaseTick >= 2",
    "phase81PhysicalSupport",
    "phase185FreshNativeEvidence",
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED",
    "GATE_E_PHASE192_LOCAL_INPUT",
    "getDeclaredField(\"input\")",
    "phase192InputClass.getSuperclass()",
    "input_state={}",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 192 lost settled-frame/input telemetry anchors: " + ", ".join(missing))

inserted = new_readiness + new_ready + input_probe
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 192 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 192: waits for bounded fixture acquisition before accumulating walk readiness")
