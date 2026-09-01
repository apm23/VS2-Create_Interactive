#!/usr/bin/env python3
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

# Keep all M1 locomotion proof on ordinary Minecraft KeyMappings and the native LocalPlayer aiStep/
# applyInput path. Production-world #482 already proves stable carry, sprint, grounded reverse, and
# jump/fall. Add one bounded right-strafe window between reverse and jump, so the existing jump gate
# cannot pass unless lateral native locomotion succeeds first. This is fixture input/acceptance only;
# no position, velocity, collision/carry, train/world, gravity, or VS2/Create physics is synthesized.
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
    @Unique private static int vs2$walkConfirmedTick = Integer.MIN_VALUE;
    @Unique private static int vs2$backwardStartTick = Integer.MIN_VALUE;
    @Unique private static int vs2$strafeStartTick = Integer.MIN_VALUE;
    @Unique private static int vs2$jumpStartTick = Integer.MIN_VALUE;
    @Unique private static boolean vs2$backwardConfirmed;
    @Unique private static boolean vs2$strafeConfirmed;
    @Unique private static boolean vs2$jumpAirborneSeen;
    @Unique private static boolean vs2$jumpFallingSeen;
    @Unique private static boolean vs2$jumpLandedLogged;
    @Unique private int vs2$nativeAiStepTick = Integer.MIN_VALUE;
    @Unique private boolean vs2$fixtureAiStepFallbackActive;

    @Unique
    private boolean vs2$fixtureWalkSeen(LocalPlayer self) {
        if (!Boolean.getBoolean("vs2.productionFixtureWalkConfirmed")) return false;
        if (vs2$walkConfirmedTick == Integer.MIN_VALUE) vs2$walkConfirmedTick = self.tickCount;
        return true;
    }

    @Unique
    private boolean vs2$backwardWindow(LocalPlayer self) {
        if (!vs2$fixtureWalkSeen(self) || vs2$backwardConfirmed) return false;
        int elapsed = self.tickCount - vs2$walkConfirmedTick;
        return elapsed >= 8 && elapsed <= 11;
    }

    @Unique
    private boolean vs2$strafeWindow(LocalPlayer self) {
        if (!vs2$fixtureWalkSeen(self) || !vs2$backwardConfirmed || vs2$strafeConfirmed) return false;
        int elapsed = self.tickCount - vs2$walkConfirmedTick;
        return elapsed >= 13 && elapsed <= 16;
    }

    @Unique
    private boolean vs2$jumpArmReady(LocalPlayer self) {
        if (!vs2$fixtureWalkSeen(self) || !vs2$backwardConfirmed || !vs2$strafeConfirmed) return false;
        return self.tickCount >= vs2$walkConfirmedTick + 24;
    }

    @Unique
    private void vs2$sampleNativeBackward(LocalPlayer self, Minecraft client, boolean backwardWindow) {
        if (!backwardWindow || vs2$backwardConfirmed) return;
        if (vs2$backwardStartTick == Integer.MIN_VALUE) {
            vs2$backwardStartTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_BACKWARD_REQUESTED player_tick={} walk_confirmed_tick={} settle_ticks={} on_ground={} fixture_only=true vanilla_keymapping=true",
                self.tickCount, vs2$walkConfirmedTick, self.tickCount - vs2$walkConfirmedTick, self.onGround());
        }
        if (self.onGround() && client.options.keyDown.isDown()
                && self.getDeltaMovement().horizontalDistanceSqr() > 0.0004) {
            vs2$backwardConfirmed = true;
            System.setProperty("vs2.productionFixtureBackwardConfirmed", "true");
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_BACKWARD_CONFIRMED player_tick={} start_tick={} duration_ticks={} horizontal_speed_sq={} on_ground=true fixture_only=true vanilla_keymapping=true native_motion=true",
                self.tickCount, vs2$backwardStartTick, self.tickCount - vs2$backwardStartTick,
                self.getDeltaMovement().horizontalDistanceSqr());
        }
    }

    @Unique
    private void vs2$sampleNativeStrafe(LocalPlayer self, Minecraft client, boolean strafeWindow) {
        if (!strafeWindow || vs2$strafeConfirmed) return;
        if (vs2$strafeStartTick == Integer.MIN_VALUE) {
            vs2$strafeStartTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_STRAFE_REQUESTED player_tick={} walk_confirmed_tick={} settle_ticks={} on_ground={} fixture_only=true vanilla_keymapping=true direction=right",
                self.tickCount, vs2$walkConfirmedTick, self.tickCount - vs2$walkConfirmedTick, self.onGround());
        }
        if (self.onGround() && client.options.keyRight.isDown()
                && self.getDeltaMovement().horizontalDistanceSqr() > 0.0004) {
            vs2$strafeConfirmed = true;
            System.setProperty("vs2.productionFixtureStrafeConfirmed", "true");
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_STRAFE_CONFIRMED player_tick={} start_tick={} duration_ticks={} horizontal_speed_sq={} on_ground=true fixture_only=true vanilla_keymapping=true native_motion=true direction=right",
                self.tickCount, vs2$strafeStartTick, self.tickCount - vs2$strafeStartTick,
                self.getDeltaMovement().horizontalDistanceSqr());
        }
    }

    @Unique
    private void vs2$sampleNativeJump(LocalPlayer self, Minecraft client) {
        boolean jumpArmReady = vs2$jumpArmReady(self);
        if (!jumpArmReady || vs2$jumpLandedLogged) {
            client.options.keyJump.setDown(false);
            return;
        }
        if (vs2$jumpStartTick == Integer.MIN_VALUE && self.onGround()) {
            vs2$jumpStartTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_JUMP_REQUESTED player_tick={} walk_confirmed_tick={} settle_ticks={} on_ground=true fixture_only=true vanilla_keymapping=true",
                self.tickCount, vs2$walkConfirmedTick, self.tickCount - vs2$walkConfirmedTick);
        }
        boolean jumpPulse = vs2$jumpStartTick != Integer.MIN_VALUE && self.tickCount == vs2$jumpStartTick;
        client.options.keyJump.setDown(jumpPulse);
        double deltaY = self.getDeltaMovement().y;
        if (vs2$jumpStartTick != Integer.MIN_VALUE && !self.onGround() && deltaY > 0.0 && !vs2$jumpAirborneSeen) {
            vs2$jumpAirborneSeen = true;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_JUMP_AIRBORNE player_tick={} start_tick={} delta_y={} on_ground=false fixture_only=true native_motion=true",
                self.tickCount, vs2$jumpStartTick, deltaY);
        }
        if (vs2$jumpAirborneSeen && !self.onGround() && deltaY < 0.0) vs2$jumpFallingSeen = true;
        if (vs2$jumpFallingSeen && self.onGround() && self.tickCount > vs2$jumpStartTick) {
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
        try { startTick = Integer.parseInt(rawStart); } catch (NumberFormatException ignored) { return; }
        boolean pulse = self.tickCount >= startTick && self.tickCount <= startTick + 3;
        boolean backwardWindow = vs2$backwardWindow(self);
        boolean strafeWindow = vs2$strafeWindow(self);
        client.options.keyUp.setDown(pulse && !backwardWindow && !strafeWindow);
        client.options.keyDown.setDown(backwardWindow);
        client.options.keyLeft.setDown(false);
        client.options.keyRight.setDown(strafeWindow);
        client.options.keySprint.setDown(pulse && !backwardWindow && !strafeWindow);
        if (backwardWindow && vs2$backwardStartTick == Integer.MIN_VALUE) {
            vs2$backwardStartTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_BACKWARD_REQUESTED player_tick={} walk_confirmed_tick={} settle_ticks={} on_ground={} fixture_only=true vanilla_keymapping=true",
                self.tickCount, vs2$walkConfirmedTick, self.tickCount - vs2$walkConfirmedTick, self.onGround());
        }
        if (strafeWindow && vs2$strafeStartTick == Integer.MIN_VALUE) {
            vs2$strafeStartTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_M1_NATIVE_STRAFE_REQUESTED player_tick={} walk_confirmed_tick={} settle_ticks={} on_ground={} fixture_only=true vanilla_keymapping=true direction=right",
                self.tickCount, vs2$walkConfirmedTick, self.tickCount - vs2$walkConfirmedTick, self.onGround());
        }
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
        try { startTick = Integer.parseInt(rawStart); } catch (NumberFormatException ignored) { return; }
        vs2$sampleNativeBackward(self, client, vs2$backwardWindow(self));
        vs2$sampleNativeStrafe(self, client, vs2$strafeWindow(self));
        vs2$sampleNativeJump(self, client);
        if (self.tickCount != vs2$lastReturnTick && self.tickCount <= startTick + 5) {
            vs2$lastReturnTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_LOCALPLAYER_AISTEP_RETURN player_tick={} start_tick={} key_up={} delta={} on_ground={} fixture_only=true read_only=true fallback_active={}",
                self.tickCount, startTick, client.options.keyUp.isDown(), self.getDeltaMovement(), self.onGround(), vs2$fixtureAiStepFallbackActive);
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
        try { startTick = Integer.parseInt(rawStart); } catch (NumberFormatException ignored) { return; }
        boolean walkWindow = self.tickCount >= startTick && self.tickCount <= startTick + 3;
        boolean backwardWindow = vs2$backwardWindow(self);
        boolean strafeWindow = vs2$strafeWindow(self);
        // Once the fixture has actually issued its one vanilla jump, keep the existing
        // headless native-aiStep bridge alive for the whole airborne/falling lifecycle.
        // Phase 202 intentionally makes jumpArmReady() grounded-only to prevent a stale
        // launch, but reusing that arming predicate after takeoff suppresses aiStep on
        // every airborne tick and artificially freezes the jump in the headless smoke.
        boolean jumpWindow = (vs2$jumpStartTick != Integer.MIN_VALUE || vs2$jumpArmReady(self))
            && !vs2$jumpLandedLogged;
        if ((!walkWindow && !backwardWindow && !strafeWindow && !jumpWindow) || vs2$nativeAiStepTick == self.tickCount) return;
        client.options.keyUp.setDown(walkWindow && !backwardWindow && !strafeWindow);
        client.options.keyDown.setDown(backwardWindow);
        client.options.keyLeft.setDown(false);
        client.options.keyRight.setDown(strafeWindow);
        client.options.keySprint.setDown(walkWindow && !backwardWindow && !strafeWindow);
        vs2$fixtureAiStepFallbackActive = true;
        try {
            self.aiStep();
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_HEADLESS_NATIVE_AISTEP_FALLBACK player_tick={} start_tick={} key_up={} key_down={} native_ai_step_seen={} backward_window={} strafe_window={} jump_window={} fixture_only=true native_vanilla_path=true",
                self.tickCount, startTick, client.options.keyUp.isDown(), client.options.keyDown.isDown(),
                vs2$nativeAiStepTick == self.tickCount, backwardWindow, strafeWindow, jumpWindow);
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
    'GATE_E_M1_NATIVE_BACKWARD_REQUESTED', 'GATE_E_M1_NATIVE_BACKWARD_CONFIRMED',
    'GATE_E_M1_NATIVE_STRAFE_REQUESTED', 'GATE_E_M1_NATIVE_STRAFE_CONFIRMED',
    'vs2.productionFixtureBackwardConfirmed', 'vs2.productionFixtureStrafeConfirmed',
    'client.options.keyDown.setDown(backwardWindow)', 'client.options.keyRight.setDown(strafeWindow)',
    'horizontalDistanceSqr() > 0.0004',
    'GATE_E_M1_NATIVE_JUMP_REQUESTED', 'GATE_E_M1_NATIVE_JUMP_AIRBORNE', 'GATE_E_M1_NATIVE_JUMP_LANDED',
    'vs2.productionFixtureJumpLanded', 'vs2.productionFixtureWalkConfirmed',
    'vs2$walkConfirmedTick + 24', '!vs2$backwardConfirmed', '!vs2$strafeConfirmed',
    'jumpWindow', 'vs2$nativeAiStepTick == self.tickCount', 'self.aiStep()',
    'vs2$jumpStartTick != Integer.MIN_VALUE || vs2$jumpArmReady(self)',
    'vs2.productionFixtureWalkStartTick', 'client.options.keyUp.setDown(walkWindow && !backwardWindow && !strafeWindow)',
    'client.options.keyJump.setDown(jumpPulse)', 'deltaY > 0.0', 'deltaY < 0.0', 'vs2$jumpFallingSeen',
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

print("Phase 198: requires native grounded reverse and right-strafe before jump; headless native aiStep now remains active through the started jump lifecycle")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase199.py")), run_name="__main__")
