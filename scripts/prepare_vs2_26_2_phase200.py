#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

source = java.read_text(encoding="utf-8")

# Production-world #429 proves every KeyboardInput.tick invocation in the bounded walk window is the
# reflective Phase196 call from START_CLIENT_TICK; no vanilla caller reaches KeyboardInput.tick before
# LocalPlayer locomotion. Phase198 already places the ordinary fixture KeyMapping at LocalPlayer.tick
# HEAD. Sample that KeyMapping through the player's existing KeyboardInput immediately there, before
# vanilla LocalPlayer.tick proceeds. This is fixture-only input plumbing: it mutates input state only,
# never player position/velocity, carry/collision, train/world, inventory, or VS2/Create physics.
anchor = '''        client.options.keyUp.setDown(pulse);\n        client.options.keyDown.setDown(false);\n'''
insert = anchor + '''        boolean phase200Sampled = false;\n        String phase200Sampler = "missing";\n        try {\n            java.lang.reflect.Field inputField = null;\n            Class<?> playerClass = self.getClass();\n            while (playerClass != null && inputField == null) {\n                try {\n                    inputField = playerClass.getDeclaredField("input");\n                } catch (NoSuchFieldException ignored) {\n                    playerClass = playerClass.getSuperclass();\n                }\n            }\n            if (inputField != null) {\n                inputField.setAccessible(true);\n                Object input = inputField.get(self);\n                if (input != null) {\n                    java.lang.reflect.Method inputTick = null;\n                    Class<?> inputClass = input.getClass();\n                    while (inputClass != null && inputTick == null) {\n                        for (java.lang.reflect.Method method : inputClass.getDeclaredMethods()) {\n                            if (method.getName().equals("tick") && method.getParameterCount() == 0) {\n                                inputTick = method;\n                                break;\n                            }\n                        }\n                        inputClass = inputClass.getSuperclass();\n                    }\n                    if (inputTick != null) {\n                        inputTick.setAccessible(true);\n                        inputTick.invoke(input);\n                        phase200Sampled = true;\n                        phase200Sampler = inputTick.getDeclaringClass().getName() + "." + inputTick.getName();\n                    }\n                }\n            }\n        } catch (ReflectiveOperationException | RuntimeException exception) {\n            phase200Sampler = "error=" + exception.getClass().getSimpleName();\n        }\n        if (self.tickCount <= startTick + 5) {\n            VS2_FIXTURE_INPUT_LOGGER.info(\n                "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE player_tick={} start_tick={} pulse={} key_up={} sampled={} sampler={} fixture_only=true input_only=true",\n                self.tickCount, startTick, pulse, client.options.keyUp.isDown(), phase200Sampled, phase200Sampler);\n        }\n'''

if "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE" not in source:
    count = source.count(anchor)
    if count != 1:
        raise SystemExit(f"Phase 200 expected one Phase198 KeyMapping anchor, found {count}")
    source = source.replace(anchor, insert, 1)

required = [
    "GATE_E_PHASE200_PRE_LOCALPLAYER_INPUT_SAMPLE",
    "inputTick.invoke(input)",
    "client.options.keyUp.setDown(pulse)",
    '@Inject(method = "tick", at = @At("HEAD"), require = 1)',
    "fixture_only=true input_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 200 lost pre-LocalPlayer input sampling anchors: " + ", ".join(missing))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
    "keyPresses =", "moveVector =",
]:
    if forbidden in source:
        raise SystemExit("Phase 200 introduced forbidden gameplay mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
print("Phase 200: samples existing fixture KeyMapping through KeyboardInput at LocalPlayer.tick HEAD; harness-only input plumbing")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase201.py")), run_name="__main__")
