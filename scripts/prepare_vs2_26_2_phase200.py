#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

source = java.read_text(encoding="utf-8")

# Production-world #453 proves the native fixture path can sustain grounded forward locomotion.
# Keep the same native LocalPlayer.applyInput boundary but sample the ordinary backward KeyMapping
# for the next M1 directional proof. Vanilla applyInput still proceeds exactly once in its normal
# call chain. This is fixture-only input plumbing: no position, velocity, Entity.move, collision/carry,
# train/world, inventory, or VS2/Create physics state is written.
method = r'''

    @Inject(method = "applyInput", at = @At("HEAD"), require = 1)
    private void vs2$sampleFixtureInputAtNativeApplyInput(CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.productionSmokeFixture")) return;
        LocalPlayer self = (LocalPlayer) (Object) this;
        Minecraft client = Minecraft.getInstance();
        if (client.player != self) return;
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try {
            startTick = Integer.parseInt(rawStart);
        } catch (NumberFormatException ignored) {
            return;
        }
        boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3;
        client.options.keyUp.setDown(false);
        client.options.keyDown.setDown(pulse);

        boolean sampled = false;
        String sampler = "missing";
        try {
            java.lang.reflect.Field inputField = null;
            Class<?> playerClass = self.getClass();
            while (playerClass != null && inputField == null) {
                try {
                    inputField = playerClass.getDeclaredField("input");
                } catch (NoSuchFieldException ignored) {
                    playerClass = playerClass.getSuperclass();
                }
            }
            if (inputField != null) {
                inputField.setAccessible(true);
                Object input = inputField.get(self);
                if (input != null) {
                    java.lang.reflect.Method inputTick = null;
                    Class<?> inputClass = input.getClass();
                    while (inputClass != null && inputTick == null) {
                        for (java.lang.reflect.Method candidate : inputClass.getDeclaredMethods()) {
                            if (candidate.getName().equals("tick") && candidate.getParameterCount() == 0) {
                                inputTick = candidate;
                                break;
                            }
                        }
                        inputClass = inputClass.getSuperclass();
                    }
                    if (inputTick != null) {
                        inputTick.setAccessible(true);
                        inputTick.invoke(input);
                        sampled = true;
                        sampler = inputTick.getDeclaringClass().getName() + "." + inputTick.getName();
                    }
                }
            }
        } catch (ReflectiveOperationException | RuntimeException exception) {
            sampler = "error=" + exception.getClass().getSimpleName();
        }

        if (self.tickCount <= startTick + 5) {
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE200_NATIVE_APPLY_INPUT_HEAD player_tick={} start_tick={} pulse={} key_down={} sampled={} sampler={} fixture_only=true input_only=true native_boundary=true",
                self.tickCount, startTick, pulse, client.options.keyDown.isDown(), sampled, sampler);
        }
    }
'''

marker = "GATE_E_PHASE200_NATIVE_APPLY_INPUT_HEAD"
if marker not in source:
    end = source.rfind("\n}")
    if end < 0:
        raise SystemExit("Phase 200 could not find MixinLocalPlayerFixtureInput class end")
    source = source[:end] + method + source[end:]

required = [
    marker,
    '@Inject(method = "applyInput", at = @At("HEAD"), require = 1)',
    "inputTick.invoke(input)",
    "client.options.keyDown.setDown(pulse)",
    "native_boundary=true",
    "fixture_only=true input_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 200 lost native applyInput fixture anchors: " + ", ".join(missing))

# The fixture may manipulate only ordinary input state. Keep direct movement/physics mutation out.
for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
    "applyInput.invoke(", "keyPresses =", "moveVector =",
]:
    if forbidden in source:
        raise SystemExit("Phase 200 introduced forbidden gameplay mutation token: " + forbidden)

java.write_text(source, encoding="utf-8")
print("Phase 200: samples backward fixture KeyboardInput at native LocalPlayer.applyInput HEAD and lets vanilla proceed once; input-only harness")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase201.py")), run_name="__main__")
