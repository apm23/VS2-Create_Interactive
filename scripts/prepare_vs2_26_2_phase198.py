#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

# Production-world #450 proves the internal KeyboardInput sampler can report forward=true while
# the real bounded walk window still never enters LocalPlayer.aiStep/applyInput or Entity.move.
# The blocker is therefore the headless fixture locomotion harness, not Create/VS2 carry physics.
# Keep the ordinary KeyMapping pulse, but if MC's headless LocalPlayer.tick did not enter aiStep
# for that player tick, invoke LocalPlayer.aiStep once as a fixture-only native fallback. aiStep
# remains Minecraft's own locomotion/input path; this does not set position/velocity, call move
# directly, synthesize carry, or mutate collision/train/world state. If native aiStep runs normally,
# the fallback is skipped so there is no duplicate locomotion.
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Disposable production-world smoke input timing bridge. */
@Mixin(LocalPlayer.class)
public abstract class MixinLocalPlayerFixtureInput {
    @Unique private static final Logger VS2_FIXTURE_INPUT_LOGGER = LogManager.getLogger("VS2-GateE-FixtureInput");
    @Unique private static int vs2$lastHeadTick = Integer.MIN_VALUE;
    @Unique private static int vs2$lastReturnTick = Integer.MIN_VALUE;
    @Unique private int vs2$nativeAiStepTick = Integer.MIN_VALUE;
    @Unique private boolean vs2$fixtureAiStepFallbackActive;

    @Inject(method = "aiStep", at = @At("HEAD"), require = 1)
    private void vs2$fixtureForwardBeforeLocalPlayerAiStep(CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.productionSmokeFixture")) return;
        LocalPlayer self = (LocalPlayer) (Object) this;
        Minecraft client = Minecraft.getInstance();
        if (client.player != self) return;
        vs2$nativeAiStepTick = self.tickCount;
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try {
            startTick = Integer.parseInt(rawStart);
        } catch (NumberFormatException ignored) {
            return;
        }
        boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3;
        client.options.keyUp.setDown(pulse);
        client.options.keyDown.setDown(false);
        if (self.tickCount != vs2$lastHeadTick && self.tickCount <= startTick + 5) {
            vs2$lastHeadTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_LOCALPLAYER_AISTEP_HEAD player_tick={} start_tick={} pulse={} key_up={} delta={} fixture_only=true vanilla_input_path=true fallback_active={}",
                self.tickCount, startTick, pulse, client.options.keyUp.isDown(), self.getDeltaMovement(), vs2$fixtureAiStepFallbackActive);
        }
    }

    @Inject(method = "aiStep", at = @At("RETURN"), require = 1)
    private void vs2$observeFixtureForwardAfterLocalPlayerAiStep(CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.productionSmokeFixture")) return;
        LocalPlayer self = (LocalPlayer) (Object) this;
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try {
            startTick = Integer.parseInt(rawStart);
        } catch (NumberFormatException ignored) {
            return;
        }
        if (self.tickCount != vs2$lastReturnTick && self.tickCount <= startTick + 5) {
            vs2$lastReturnTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_LOCALPLAYER_AISTEP_RETURN player_tick={} start_tick={} key_up={} delta={} on_ground={} fixture_only=true read_only=true fallback_active={}",
                self.tickCount, startTick, Minecraft.getInstance().options.keyUp.isDown(),
                self.getDeltaMovement(), self.onGround(), vs2$fixtureAiStepFallbackActive);
        }
    }

    @Inject(method = "tick", at = @At("RETURN"), require = 1)
    private void vs2$runNativeAiStepWhenHeadlessTickSkippedIt(CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.productionSmokeFixture")) return;
        LocalPlayer self = (LocalPlayer) (Object) this;
        Minecraft client = Minecraft.getInstance();
        if (client.player != self || vs2$fixtureAiStepFallbackActive) return;
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try {
            startTick = Integer.parseInt(rawStart);
        } catch (NumberFormatException ignored) {
            return;
        }
        boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3;
        if (!walkWindow || vs2$nativeAiStepTick == self.tickCount) return;
        client.options.keyUp.setDown(true);
        client.options.keyDown.setDown(false);
        vs2$fixtureAiStepFallbackActive = true;
        try {
            self.aiStep();
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_HEADLESS_NATIVE_AISTEP_FALLBACK player_tick={} start_tick={} key_up={} native_ai_step_seen={} fixture_only=true native_vanilla_path=true",
                self.tickCount, startTick, client.options.keyUp.isDown(), vs2$nativeAiStepTick == self.tickCount);
        } finally {
            vs2$fixtureAiStepFallbackActive = false;
        }
    }
}
''', encoding="utf-8")

text = java.read_text(encoding="utf-8")
required = [
    '@Inject(method = "aiStep", at = @At("HEAD"), require = 1)',
    '@Inject(method = "aiStep", at = @At("RETURN"), require = 1)',
    '@Inject(method = "tick", at = @At("RETURN"), require = 1)',
    'GATE_E_PHASE198_LOCALPLAYER_AISTEP_HEAD',
    'GATE_E_PHASE198_LOCALPLAYER_AISTEP_RETURN',
    'GATE_E_PHASE198_HEADLESS_NATIVE_AISTEP_FALLBACK',
    'vs2$nativeAiStepTick == self.tickCount',
    'self.aiStep()',
    'vs2.productionFixtureWalkStartTick',
    'client.options.keyUp.setDown(true)',
    'fixture_only=true',
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 198 lost LocalPlayer native fixture anchors: " + ", ".join(missing))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in text:
        raise SystemExit("Phase 198 introduced forbidden gameplay mutation token: " + forbidden)

print("Phase 198: uses one fixture-only native aiStep fallback only when headless LocalPlayer.tick skipped vanilla locomotion; no direct movement mutation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase199.py")), run_name="__main__")
