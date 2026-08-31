#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinKeyboardInputTrace.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #427 proves the Phase198 LocalPlayer.tick bridge really runs and holds keyUp
# during ticks 17-19, but LocalPlayer.tick RETURN still has zero horizontal delta. Phase196 later
# calls KeyboardInput.tick() manually and observes sampled=true, so the remaining harness question is
# where/when vanilla MC 26.2 itself invokes KeyboardInput.tick relative to LocalPlayer locomotion.
# Trace that method and its immediate caller stack read-only; do not synthesize movement or mutate
# player/carry/collision/train/world state.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.KeyboardInput;
import net.minecraft.client.player.LocalPlayer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Read-only production-smoke trace of the real MC 26.2 KeyboardInput sampling boundary. */
@Mixin(KeyboardInput.class)
public abstract class MixinKeyboardInputTrace {
    @Unique private static final Logger VS2_INPUT_TRACE_LOGGER = LogManager.getLogger("VS2-GateE-InputTrace");

    @Unique
    private static String vs2$callerSummary() {
        StackTraceElement[] stack = Thread.currentThread().getStackTrace();
        StringBuilder out = new StringBuilder();
        int emitted = 0;
        for (StackTraceElement frame : stack) {
            String owner = frame.getClassName();
            if (owner.equals(Thread.class.getName()) || owner.contains("MixinKeyboardInputTrace") || owner.equals(KeyboardInput.class.getName())) continue;
            if (emitted++ > 0) out.append(" <- ");
            out.append(owner).append('#').append(frame.getMethodName());
            if (emitted >= 5) break;
        }
        return out.toString();
    }

    @Inject(method = "tick", at = @At("HEAD"), require = 1)
    private void vs2$traceKeyboardInputTickHead(CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.productionSmokeFixture")) return;
        Minecraft client = Minecraft.getInstance();
        LocalPlayer player = client.player;
        if (player == null) return;
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try { startTick = Integer.parseInt(rawStart); } catch (NumberFormatException ignored) { return; }
        if (player.tickCount > startTick + 7) return;
        VS2_INPUT_TRACE_LOGGER.info(
            "GATE_E_PHASE199_KEYBOARD_INPUT_TICK_HEAD player_tick={} start_tick={} key_up={} input_before={} callers={} fixture_only=true read_only=true",
            player.tickCount, startTick, client.options.keyUp.isDown(), (Object) this, vs2$callerSummary());
    }

    @Inject(method = "tick", at = @At("RETURN"), require = 1)
    private void vs2$traceKeyboardInputTickReturn(CallbackInfo ci) {
        if (!Boolean.getBoolean("vs2.productionSmokeFixture")) return;
        Minecraft client = Minecraft.getInstance();
        LocalPlayer player = client.player;
        if (player == null) return;
        String rawStart = System.getProperty("vs2.productionFixtureWalkStartTick");
        if (rawStart == null) return;
        int startTick;
        try { startTick = Integer.parseInt(rawStart); } catch (NumberFormatException ignored) { return; }
        if (player.tickCount > startTick + 7) return;
        VS2_INPUT_TRACE_LOGGER.info(
            "GATE_E_PHASE199_KEYBOARD_INPUT_TICK_RETURN player_tick={} start_tick={} key_up={} input_after={} fixture_only=true read_only=true",
            player.tickCount, startTick, client.options.keyUp.isDown(), (Object) this);
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client_mixins = metadata.setdefault("client", [])
if "MixinKeyboardInputTrace" not in client_mixins:
    client_mixins.append("MixinKeyboardInputTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

text = java.read_text(encoding="utf-8")
required = [
    '@Mixin(KeyboardInput.class)',
    '@Inject(method = "tick", at = @At("HEAD"), require = 1)',
    '@Inject(method = "tick", at = @At("RETURN"), require = 1)',
    'GATE_E_PHASE199_KEYBOARD_INPUT_TICK_HEAD',
    'GATE_E_PHASE199_KEYBOARD_INPUT_TICK_RETURN',
    'vs2$callerSummary()',
    'fixture_only=true read_only=true',
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 199 lost KeyboardInput trace anchors: " + ", ".join(missing))

for forbidden in [
    ".setDown(", "setPos(", "setDeltaMovement(", ".move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in text:
        raise SystemExit("Phase 199 introduced forbidden mutation token: " + forbidden)

print("Phase 199: traces required KeyboardInput.tick caller/timing boundary read-only; no gameplay or physics mutation")
