#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #420 proved the movement blocker is in the test harness, not Create carry:
# while keyUp=true for ticks 16-18, KeyboardInput's authoritative inherited ClientInput state remained
# keyPresses=Input[forward=false,...] and LocalPlayer horizontal delta stayed zero. The Gate E callback
# sets KeyMapping after Minecraft's normal input sampling point, so the disposable key pulse is never
# consumed during the finite real-train window. Sample the already-set fixture KeyMapping through the
# existing KeyboardInput tick method immediately before the Phase192 input snapshot. That snapshot is
# already proven to run inside the bounded walk branch after the fixture key state is updated, and is a
# more stable cumulative anchor than the Phase165 source fragment modified by later composition phases.
# This is strictly production-smoke-fixture input plumbing: it does not set player position/velocity,
# alter collision/carry, or mutate train/world/VS2 state.
anchor = '''                                String phase192InputState = "input_field_missing";
'''
sampler = '''                                boolean phase196InputSampled = false;
                                String phase196Sampler = "missing";
                                try {
                                    java.lang.reflect.Field phase196InputField = null;
                                    Class<?> phase196PlayerClass = player.getClass();
                                    while (phase196PlayerClass != null && phase196InputField == null) {
                                        try {
                                            phase196InputField = phase196PlayerClass.getDeclaredField("input");
                                        } catch (NoSuchFieldException ignored) {
                                            phase196PlayerClass = phase196PlayerClass.getSuperclass();
                                        }
                                    }
                                    if (phase196InputField != null) {
                                        phase196InputField.setAccessible(true);
                                        Object phase196Input = phase196InputField.get(player);
                                        if (phase196Input != null) {
                                            java.lang.reflect.Method phase196Tick = null;
                                            Class<?> phase196InputClass = phase196Input.getClass();
                                            while (phase196InputClass != null && phase196Tick == null) {
                                                for (java.lang.reflect.Method phase196Method : phase196InputClass.getDeclaredMethods()) {
                                                    if (phase196Method.getName().equals("tick")
                                                            && phase196Method.getParameterCount() == 0) {
                                                        phase196Tick = phase196Method;
                                                        break;
                                                    }
                                                }
                                                phase196InputClass = phase196InputClass.getSuperclass();
                                            }
                                            if (phase196Tick != null) {
                                                phase196Tick.setAccessible(true);
                                                phase196Tick.invoke(phase196Input);
                                                phase196InputSampled = true;
                                                phase196Sampler = phase196Tick.getDeclaringClass().getName()
                                                    + "." + phase196Tick.getName();
                                            }
                                        }
                                    }
                                } catch (ReflectiveOperationException | RuntimeException phase196Exception) {
                                    phase196Sampler = "error=" + phase196Exception.getClass().getSimpleName();
                                }
                                LOGGER.info(
                                    "GATE_E_PHASE196_FIXTURE_INPUT_SAMPLE player_tick={} carriage_id={} key_up={} sampled={} sampler={} fixture_only=true",
                                    player.tickCount, phase154Carriage.getId(), client.options.keyUp.isDown(),
                                    phase196InputSampled, phase196Sampler);
                                String phase192InputState = "input_field_missing";
'''
if "GATE_E_PHASE196_FIXTURE_INPUT_SAMPLE" not in source:
    count = source.count(anchor)
    if count != 1:
        raise SystemExit(f"Phase 196 expected one cumulative Phase192 input snapshot anchor, found {count}")
    source = source.replace(anchor, sampler, 1)

required = [
    "GATE_E_PHASE196_FIXTURE_INPUT_SAMPLE",
    "phase196InputSampled",
    "phase196Method.getName().equals(\"tick\")",
    "phase196Method.getParameterCount() == 0",
    "phase196Tick.invoke(phase196Input)",
    "GATE_E_PHASE192_LOCAL_INPUT",
    "client.options.keyUp.isDown()",
    "fixture_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 196 lost fixture input-sampling anchors: " + ", ".join(missing))

for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(", "keyPresses =", "movementVector =",
]:
    if forbidden in sampler:
        raise SystemExit("Phase 196 introduced forbidden gameplay mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 196: samples the fixture key through KeyboardInput at the cumulative Phase192 input probe; harness-only")
