#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContinuousOBBColliderTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import com.zurrtum.create.foundation.collision.CollisionList;
import com.zurrtum.create.foundation.collision.ContinuousOBBCollider;
import com.zurrtum.create.foundation.collision.OrientedBB;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** CI-only observation of the actual OBB result Create uses before registering a
 * surface contact. It never changes the returned collision response. */
@Mixin(value = ContinuousOBBCollider.class, remap = false)
public abstract class MixinContinuousOBBColliderTrace {
    private static final Logger LOGGER = LogManager.getLogger("VS2-GateE-OBB");
    private static int renderCalls;

    @Inject(method = "collideMany", at = @At("RETURN"), remap = false, require = 0)
    private static void vs2$traceCollideMany(
        CollisionList collidableBBs,
        CollisionList denseViableColliders,
        OrientedBB obb,
        Vec3 motion,
        float entityMaxStep,
        boolean doHorizontalPass,
        CallbackInfoReturnable<ContinuousOBBCollider.CollisionResponse> cir
    ) {
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        int index = ++renderCalls;
        if (index > 48) return;

        ContinuousOBBCollider.CollisionResponse response = cir.getReturnValue();
        if (response == null) {
            LOGGER.info("GATE_E_CREATE_COLLIDE_MANY_RESULT index={} thread={} response=null motion={},{},{}", index, thread, motion.x, motion.y, motion.z);
            return;
        }

        int collidableSize = -1;
        int denseSize = -1;
        try {
            java.lang.reflect.Field size = CollisionList.class.getDeclaredField("size");
            size.setAccessible(true);
            collidableSize = size.getInt(collidableBBs);
            denseSize = size.getInt(denseViableColliders);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
        }

        LOGGER.info(
            "GATE_E_CREATE_COLLIDE_MANY_RESULT index={} thread={} collidable_size={} dense_size={} surface={} temporal={} response={},{},{} normal={},{},{} location={},{},{} motion={},{},{} max_step={} horizontal_pass={}",
            index, thread, collidableSize, denseSize,
            response.surfaceCollision, response.temporalResponse,
            response.collisionResponse.x, response.collisionResponse.y, response.collisionResponse.z,
            response.normal.x, response.normal.y, response.normal.z,
            response.location.x, response.location.y, response.location.z,
            motion.x, motion.y, motion.z, entityMaxStep, doHorizontalPass);
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinContinuousOBBColliderTrace" not in client:
    client.append("MixinContinuousOBBColliderTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 65: traced ContinuousOBBCollider.collideMany return values on the Render thread, including surfaceCollision/temporalResponse and viable-collider counts; read-only diagnostics only")
