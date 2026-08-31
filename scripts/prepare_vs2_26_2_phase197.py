#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerFixtureInput.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

source = client_probe.read_text(encoding="utf-8")

# Production-world #469 proves sustained grounded native sprinting on the moving train.
# Keep that subsystem frozen, then use the same disposable vanilla KeyMapping input boundary to
# request one jump only after the walk proof has already confirmed. Observe airborne -> landed
# transitions without writing position, velocity, collision/carry, train/world, or VS2/Create physics.
start_anchor = '''                            phase154WalkStartTick = player.tickCount;\n'''
start_insert = start_anchor + '''                            System.setProperty("vs2.productionFixtureWalkStartTick", Integer.toString(player.tickCount));\n'''
if 'vs2.productionFixtureWalkStartTick' not in source:
    count = source.count(start_anchor)
    if count != 1:
        raise SystemExit(f"Phase 197 expected one walk-start tick anchor, found {count}")
    source = source.replace(start_anchor, start_insert, 1)

required_probe = [
    "GATE_E_PHASE154_FIXTURE_WALK_START",
    "GATE_E_PHASE196_FIXTURE_INPUT_SAMPLE",
    "vs2.productionFixtureWalkStartTick",
    "vs2.productionFixtureWalkConfirmed",
]
missing_probe = [token for token in required_probe if token not in source]
if missing_probe:
    raise SystemExit("Phase 197 lost fixture walk/input anchors: " + ", ".join(missing_probe))

java.parent.mkdir(parents=True, exist_ok=True)
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

/**
 * Disposable production-world smoke input timing bridge. The Gate E observer discovers a strictly
 * supported moving-carriage walk window, then publishes only its start tick. At LocalPlayer.aiStep
 * HEAD we hold vanilla forward+sprint KeyMappings for three ticks so LocalPlayer's own KeyboardInput
 * sampling consumes them in the normal locomotion path. Once that existing walk/sprint proof has
 * confirmed, this same harness requests exactly one vanilla jump and only observes the resulting
 * airborne/landed states. No position, velocity, collision, carry, or world state is written here.
 */
@Mixin(LocalPlayer.class)
public abstract class MixinLocalPlayerFixtureInput {
    @Unique private static final Logger VS2_FIXTURE_INPUT_LOGGER = LogManager.getLogger("VS2-GateE-FixtureInput");
    @Unique private static int vs2$lastLoggedTick = Integer.MIN_VALUE;
    @Unique private static int vs2$jumpStartTick = Integer.MIN_VALUE;
    @Unique private static boolean vs2$jumpAirborneSeen;
    @Unique private static boolean vs2$jumpLandedLogged;

    @Inject(method = "aiStep", at = @At("HEAD"), require = 0)
    private void vs2$sampleFixtureMovementBeforeLocalPlayer(CallbackInfo ci) {
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
        client.options.keyLeft.setDown(false);
        client.options.keyRight.setDown(false);
        client.options.keySprint.setDown(pulse);

        boolean walkConfirmed = Boolean.getBoolean("vs2.productionFixtureWalkConfirmed");
        if (walkConfirmed && !vs2$jumpLandedLogged) {
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
        } else {
            client.options.keyJump.setDown(false);
        }

        if (self.tickCount != vs2$lastLoggedTick && self.tickCount <= startTick + 5) {
            vs2$lastLoggedTick = self.tickCount;
            VS2_FIXTURE_INPUT_LOGGER.info(
                "GATE_E_PHASE197_PRE_AISTEP_FIXTURE_INPUT player_tick={} start_tick={} pulse={} key_up={} key_sprint={} sprinting={} fixture_only=true vanilla_input_path=true",
                self.tickCount, startTick, pulse, client.options.keyUp.isDown(), client.options.keySprint.isDown(), self.isSprinting());
        }
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client_mixins = metadata.setdefault("client", [])
if "MixinLocalPlayerFixtureInput" not in client_mixins:
    client_mixins.append("MixinLocalPlayerFixtureInput")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

inserted = start_insert + java.read_text(encoding="utf-8")
for forbidden in [
    "self.setPos(", "self.setDeltaMovement(", "self.move(", "player.setPos(",
    "player.setDeltaMovement(", "player.move(", ".teleport(", "setBlock(",
    "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 197 introduced forbidden gameplay mutation token: " + forbidden)

for required in [
    "client.options.keyJump.setDown(jumpPulse)",
    "GATE_E_M1_NATIVE_JUMP_REQUESTED",
    "GATE_E_M1_NATIVE_JUMP_AIRBORNE",
    "GATE_E_M1_NATIVE_JUMP_LANDED",
    "vs2.productionFixtureJumpLanded",
]:
    if required not in inserted:
        raise SystemExit("Phase 197 lost native jump proof anchor: " + required)

client_probe.write_text(source, encoding="utf-8")
print("Phase 197: preserves native sprint proof then requests one vanilla jump and observes airborne/landed states; harness-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase198.py")), run_name="__main__")
