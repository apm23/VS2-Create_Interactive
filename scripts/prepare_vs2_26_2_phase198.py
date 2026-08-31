#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

# Production-world #473 proves the supported sprint/walk path is healthy, but Phase198 overwrote
# Phase197's jump request bridge and limited the headless native-aiStep fallback to the short walk
# pulse. Preserve the same vanilla KeyMapping + LocalPlayer.aiStep harness across the post-walk jump
# proof. No position/velocity/collision/carry/train/world state is synthesized or written here.
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
    @Unique private static int vs2$jumpStartTick = Integer.MIN_VALUE;
    @Unique private static boolean vs2$jumpAirborneSeen;
    @Unique private static boolean vs2$jumpLandedLogged;
    @Unique private int vs2$nativeAiStepTick = Integer.MIN_VALUE;
    @Unique private boolean vs2$fixtureAiStepFallbackActive;

    @Unique
    private void vs2$sampleNativeJump(LocalPlayer self, Minecraft client) {
        boolean walkConfirmed = Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");
        if (!walkConfirmed || vs2$jumpLandedLogged) {
            if (!walkConfirmed) client.options.keyJump.setDown(false);
            return;
        }
        if (vs2$jumpStartTick == Integer.MIN_VALUE && self.onGround()) {
            vs2$jumpStartTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_JUMP_REQUESTED player_tick={} on_ground=true fixture_only=true vanilla_keymapping=true",
                self.tickCount);
        }
        boolean jumpPulse = vs2$jumpStartTick != Integer.MIN_VALUE && self.tickCount == vs2$jumpStartTick;
        client.options.keyJump.setDown(jumpPulse);
        if (vs2$jumpStartTick != Integer.MIN_VALUE && !self.onGround() && !vs2$jumpAirborneSeen) {
            vs2$jumpAirborneSeen = true;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_JUMP_AIRBORNE player_tick={} start_tick={} delta_y={} on_ground=false fixture_only=true native_motion=true",
                self.tickCount, vs2$jumpStartTick, self.getDeltaMovement().y);
        }
        if (vs2$jumpAirborneSeen && self.onGround() && self.tickCount > vs2$jumpStartTick) {
            vs2$jumpLandedLogged = true;
            client.options.keyJump.setDown(false);
            System.setProperty("vs2.productionFixtureJumpLanded", "true");
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_JUMP_LANDED player_tick={} start_tick={} duration_ticks={} on_ground=true fixture_only=true natural_fall=true",
                self.tickCount, vs2$jumpStartTick, self.tickCount - vs2$jumpStartTick);
        }
    }

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
        client.options.keyLeft.setDown(false);
        client.options.keyRight.setDown(false);
        client.options.keySprint.setDown(pulse);
        vs2$sampleNativeJump(self, client);
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
        Minecraft client = Minecraft.getInstance();
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try {
            startTick = Integer.parseInt(rawStart);
        } catch (NumberFormatException ignored) {
            return;
        }
        vs2$sampleNativeJump(self, client);
        if (self.tickCount != vs2$lastReturnTick && self.tickCount <= startTick + 5) {
            vs2$lastReturnTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_LOCALPLAYER_AISTEP_RETURN player_tick={} start_tick={} key_up={} delta={} on_ground={} fixture_only=true read_only=true fallback_active={}",
                self.tickCount, startTick, client.options.keyUp.isDown(),
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
        boolean jumpWindow = Boolean.getBoolean("vs2.productionFixtureWalkConfirmed") && !vs2$jumpLandedLogged;
        if ((!walkWindow && !jumpWindow) || vs2$nativeAiStepTick == self.tickCount) return;
        client.options.keyUp.setDown(walkWindow);
        client.options.keyDown.setDown(false);
        client.options.keyLeft.setDown(false);
        client.options.keyRight.setDown(false);
        client.options.keySprint.setDown(walkWindow);
        vs2$fixtureAiStepFallbackActive = true;
        try {
            self.aiStep();
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_HEADLESS_NATIVE_AISTEP_FALLBACK player_tick={} start_tick={} key_up={} native_ai_step_seen={} jump_window={} fixture_only=true native_vanilla_path=true",
                self.tickCount, startTick, client.options.keyUp.isDown(), vs2$nativeAiStepTick == self.tickCount, jumpWindow);
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
    'GATE_E_M1_NATIVE_JUMP_REQUESTED',
    'GATE_E_M1_NATIVE_JUMP_AIRBORNE',
    'GATE_E_M1_NATIVE_JUMP_LANDED',
    'vs2.productionFixtureJumpLanded',
    'vs2.productionFixtureWalkConfirmed',
    'jumpWindow',
    'vs2$nativeAiStepTick == self.tickCount',
    'self.aiStep()',
    'vs2.productionFixtureWalkStartTick',
    'client.options.keyUp.setDown(walkWindow)',
    'client.options.keyJump.setDown(jumpPulse)',
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

print("Phase 198: preserves native jump request/landing through the headless aiStep bridge after supported walk confirmation; harness-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase199.py")), run_name="__main__")
