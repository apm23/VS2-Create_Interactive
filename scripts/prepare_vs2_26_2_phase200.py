#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

source = java.read_text(encoding="utf-8")

# Production-world #429 proved every KeyboardInput.tick invocation in the bounded walk window is the
# reflective Phase196 call from START_CLIENT_TICK; no vanilla caller reaches KeyboardInput.tick before
# LocalPlayer locomotion. Phase198 already places the ordinary fixture KeyMapping at LocalPlayer.tick
# HEAD. Sample that KeyMapping through the player's existing KeyboardInput immediately there.
#
# Production-world #440 then proved sampling itself is correct: ClientInput.keyPresses.forward=true
# for ticks 27-30, yet LocalPlayer.tick RETURN keeps zero horizontal delta and Entity.move is never
# reached by locomotion. Minecraft 26.x exposes LocalPlayer.applyInput() as the vanilla bridge from the
# sampled ClientInput object into LivingEntity movement inputs. Invoke that existing vanilla bridge
# immediately after the fixture-only KeyboardInput sample, still before LocalPlayer.tick proceeds.
# This does not synthesize a movement vector or touch position/velocity/collision/carry/train/world
# state; it only completes the disposable headless fixture's ordinary input pipeline.
anchor = '''        client.options.keyUp.setDown(pulse);\n        client.options.keyDown.setDown(false);\n'''
insert = anchor + '''        boolean phase200Sampled = false;\n        boolean phase200AppliedInput = false;\n        String phase200Sampler = "missing";\n        String phase200ApplyBridge = "missing";\n        try {\n            java.lang.reflect.Field inputField = null;\n            Class<?> playerClass = self.getClass();\n            while (playerClass != null && inputField == null) {\n                try {\n                    inputField = playerClass.getDeclaredField("input");\n                } catch (NoSuchFieldException ignored) {\n                    playerClass = playerClass.getSuperclass();\n                }\n            }\n            if (inputField != null) {\n                inputField.setAccessible(true);\n                Object input = inputField.get(self);\n                if (input != null) {\n                    java.lang.reflect.Method inputTick = null;\n                    Class<?> inputClass = input.getClass();\n                    while (inputClass != null && inputTick == null) {\n                        for (java.lang.reflect.Method method : inputClass.getDeclaredMethods()) {\n                            if (method.getName().equals("tick") && method.getParameterCount() == 0) {\n                                inputTick = method;\n                                break;\n                            }\n                        }\n                        inputClass = inputClass.getSuperclass();\n                    }\n                    if (inputTick != null) {\n                        inputTick.setAccessible(true);\n                        inputTick.invoke(input);\n                        phase200Sampled = true;\n                        phase200Sampler = inputTick.getDeclaringClass().getName() + "." + inputTick.getName();\n                    }\n                }\n            }\n            if (phase200Sampled) {\n                java.lang.reflect.Method applyInput = null;\n                Class<?> applyClass = self.getClass();\n                while (applyClass != null && applyInput == null) {\n                    for (java.lang.reflect.Method method : applyClass.getDeclaredMethods()) {\n                        if (method.getName().equals("applyInput") && method.getParameterCount() == 0) {\n                            applyInput = method;\n                            break;\n                        }\n                    }\n                    applyClass = applyClass.getSuperclass();\n                }\n                if (applyInput != null) {\n                    applyInput.setAccessible(true);\n                    applyInput.invoke(self);\n                    phase200AppliedInput = true;\n                    phase200ApplyBridge = applyInput.getDeclaringClass().getName() + "." + applyInput.getName();\n                }\n            }\n        } catch (ReflectiveOperationException | RuntimeException exception) {\n            if (!phase200Sampled) {\n                phase200Sampler = "error=" + exception.getClass().getSimpleName();\n            } else {\n                phase200ApplyBridge = "error=" + exception.getClass().getSimpleName();\n            }\n        }\n        if (self.tickCount <= startTick + 5) {\n            VS2_FIXTURE_INPUT_LOGGER.info(\n                "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE player_tick={} start_tick={} pulse={} key_up={} sampled={} sampler={} applied_input={} apply_bridge={} fixture_only=true input_only=true",\n                self.tickCount, startTick, pulse, client.options.keyUp.isDown(), phase200Sampled, phase200Sampler,\n                phase200AppliedInput, phase200ApplyBridge);\n        }\n'''

if "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE" not in source:
    count = source.count(anchor)
    if count != 1:
        raise SystemExit(f"Phase 200 expected one Phase198 KeyMapping anchor, found {count}")
    source = source.replace(anchor, insert, 1)
else:
    old_begin = '''        boolean phase200Sampled = false;\n        String phase200Sampler = "missing";'''
    old_end = '''        if (self.tickCount <= startTick + 5) {\n            VS2_FIXTURE_INPUT_LOGGER.info(\n                "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE player_tick={} start_tick={} pulse={} key_up={} sampled={} sampler={} fixture_only=true input_only=true",\n                self.tickCount, startTick, pulse, client.options.keyUp.isDown(), phase200Sampled, phase200Sampler);\n        }\n'''
    start = source.find(old_begin)
    end = source.find(old_end)
    if start < 0 or end < 0:
        raise SystemExit("Phase 200 could not upgrade existing input sample bridge")
    end += len(old_end)
    replacement = insert[len(anchor):]
    source = source[:start] + replacement + source[end:]

required = [
    "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE",
    "inputTick.invoke(input)",
    "applyInput.invoke(self)",
    "phase200AppliedInput",
    "applied_input={}",
    "apply_bridge={}",
    "client.options.keyUp.setDown(pulse)",
    '@Inject(method = "tick", at = @At("HEAD"), require = 1)',
    "fixture_only=true input_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 200 lost pre-LocalPlayer input bridge anchors: " + ", ".join(missing))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
    "keyPresses =", "moveVector =",
]:
    if forbidden in source:
        raise SystemExit("Phase 200 introduced forbidden gameplay mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
print("Phase 200: samples fixture KeyboardInput and applies the vanilla LocalPlayer input bridge before tick; harness-only input plumbing")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase201.py")), run_name="__main__")
