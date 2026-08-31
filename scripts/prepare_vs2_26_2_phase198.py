#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"

# Production-world #425 proves the aiStep injection from Phase197 never executes: the cumulative
# walk begins and Phase196 sees sampled forward=true, but there is no Phase197 marker at all. That is
# a silent require=0 target miss on this MC 26.2 LocalPlayer shape, not a physics failure. Retarget the
# disposable fixture bridge to LocalPlayer.tick HEAD, a method already proven active by player_tick
# telemetry, so vanilla input processing later in the same tick can consume the ordinary KeyMapping.
# Harness-only input timing; no player position/velocity, collision/carry, train/world, inventory, or
# VS2/Create physics state is modified.
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

    @Inject(method = "tick", at = @At("HEAD"), require = 1)
    private void vs2$fixtureForwardBeforeLocalPlayerTick(CallbackInfo ci) {
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
        client.options.keyUp.setDown(pulse);
        client.options.keyDown.setDown(false);
        if (self.tickCount != vs2$lastHeadTick && self.tickCount <= startTick + 5) {
            vs2$lastHeadTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE198_LOCALPLAYER_TICK_HEAD player_tick={} start_tick={} pulse={} key_up={} delta={} fixture_only=true vanilla_input_path=true",
                self.tickCount, startTick, pulse, client.options.keyUp.isDown(), self.getDeltaMovement());
        }
    }

    @Inject(method = "tick", at = @At("RETURN"), require = 1)
    private void vs2$observeFixtureForwardAfterLocalPlayerTick(CallbackInfo ci) {
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
                "GATE_E_PHASE198_LOCALPLAYER_TICK_RETURN player_tick={} start_tick={} key_up={} delta={} on_ground={} fixture_only=true read_only=true",
                self.tickCount, startTick, Minecraft.getInstance().options.keyUp.isDown(),
                self.getDeltaMovement(), self.onGround());
        }
    }
}
''', encoding="utf-8")

text = java.read_text(encoding="utf-8")
required = [
    '@Inject(method = "tick", at = @At("HEAD"), require = 1)',
    '@Inject(method = "tick", at = @At("RETURN"), require = 1)',
    'GATE_E_PHASE198_LOCALPLAYER_TICK_HEAD',
    'GATE_E_PHASE198_LOCALPLAYER_TICK_RETURN',
    'vs2.productionFixtureWalkStartTick',
    'client.options.keyUp.setDown(pulse)',
    'fixture_only=true',
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 198 lost LocalPlayer tick fixture anchors: " + ", ".join(missing))

for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in text:
        raise SystemExit("Phase 198 introduced forbidden gameplay mutation token: " + forbidden)

print("Phase 198: retargets disposable forward KeyMapping bridge to required LocalPlayer.tick HEAD and traces RETURN; harness-only")
