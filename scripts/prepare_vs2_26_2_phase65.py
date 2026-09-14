#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContinuousOBBColliderTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** CI-only observation of Create Fly's OBB collision result. The integration
 * source set intentionally does not compile against Create classes, so this
 * diagnostic targets the runtime class by name and reflects only the returned
 * response fields. No collision value is modified. */
@Mixin(targets = "com.zurrtum.create.foundation.collision.ContinuousOBBCollider", remap = false)
public abstract class MixinContinuousOBBColliderTrace {
    private static final Logger LOGGER = LogManager.getLogger("VS2-GateE-OBB");
    private static int renderCalls;

    @Inject(method = "collideMany", at = @At("RETURN"), remap = false, require = 0)
    private static void vs2$traceCollideMany(CallbackInfoReturnable<Object> cir) {
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        int index = ++renderCalls;
        // #725 reached the LocalPlayer zero-response consumption seam just after
        // the old 64-call trace cap. Extend the read-only window only far enough
        // to correlate the OBB return with the same LocalPlayer tick/position.
        if (index > 128) return;

        net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;
        int playerTick = player == null ? -1 : player.tickCount;
        String playerPos = player == null ? "none" : String.valueOf(player.position());
        String playerMotion = player == null ? "none" : String.valueOf(player.getDeltaMovement());
        boolean playerOnGround = player != null && player.onGround();

        Object response = cir.getReturnValue();
        if (response == null) {
            LOGGER.info(
                "GATE_E_CREATE_COLLIDE_MANY_RESULT index={} thread={} response=null player_tick={} player_pos={} player_motion={} player_on_ground={}",
                index, thread, playerTick, playerPos, playerMotion, playerOnGround);
            return;
        }

        try {
            Class<?> type = response.getClass();
            java.lang.reflect.Field surfaceField = type.getField("surfaceCollision");
            java.lang.reflect.Field temporalField = type.getField("temporalResponse");
            java.lang.reflect.Field responseField = type.getField("collisionResponse");
            java.lang.reflect.Field normalField = type.getField("normal");
            java.lang.reflect.Field locationField = type.getField("location");
            Object collisionResponse = responseField.get(response);
            Object normal = normalField.get(response);
            Object location = locationField.get(response);
            LOGGER.info(
                "GATE_E_CREATE_COLLIDE_MANY_RESULT index={} thread={} surface={} temporal={} response={} normal={} location={} player_tick={} player_pos={} player_motion={} player_on_ground={}",
                index, thread,
                surfaceField.getBoolean(response), temporalField.getDouble(response),
                String.valueOf(collisionResponse), String.valueOf(normal), String.valueOf(location),
                playerTick, playerPos, playerMotion, playerOnGround);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            LOGGER.info(
                "GATE_E_CREATE_COLLIDE_MANY_RESULT index={} thread={} reflection_error={} response_type={} player_tick={} player_pos={} player_motion={} player_on_ground={}",
                index, thread, exception.getClass().getSimpleName(), response.getClass().getName(),
                playerTick, playerPos, playerMotion, playerOnGround);
        }
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinContinuousOBBColliderTrace" not in client:
    client.append("MixinContinuousOBBColliderTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 65: correlated ContinuousOBBCollider.collideMany returns with LocalPlayer tick/position across the #725 zero-response seam; read-only telemetry only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase66.py")), run_name="__main__")
