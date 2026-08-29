#!/usr/bin/env python3
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import java.util.Collection;
import java.util.Map;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** CI-only trace of Create's actual narrow-phase path after the smoke player is
 * normalized onto real carriage geometry. No collision result is modified. */
@Mixin(targets = "com.zurrtum.create.content.contraptions.ContraptionCollider", remap = false)
public abstract class MixinContraptionColliderTrace {
    private static final Logger VS2_GATE_E_LOGGER = LogManager.getLogger("VS2-GateE-Narrowphase");
    private static int vs2$collideCalls;
    private static int vs2$shapeCalls;

    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)
    private static void vs2$traceCollideEntities(CallbackInfo ci) {
        if (vs2$collideCalls++ < 12) {
            VS2_GATE_E_LOGGER.info("GATE_E_CREATE_COLLIDE_ENTITIES_CALL index={}", vs2$collideCalls);
        }
    }

    @Inject(method = "getPotentiallyCollidedShapes", at = @At("RETURN"), remap = false, require = 0)
    private static void vs2$tracePotentialShapes(CallbackInfoReturnable<Object> cir) {
        if (vs2$shapeCalls++ >= 24) return;
        Object value = cir.getReturnValue();
        String type = value == null ? "null" : value.getClass().getName();
        int size = -1;
        if (value instanceof Collection<?> collection) size = collection.size();
        else if (value instanceof Map<?, ?> map) size = map.size();
        VS2_GATE_E_LOGGER.info(
            "GATE_E_CREATE_POTENTIAL_SHAPES index={} return_type={} size={}",
            vs2$shapeCalls, type, size);
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinContraptionColliderTrace" not in client:
    client.append("MixinContraptionColliderTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 62: traced Create collideEntities entry and getPotentiallyCollidedShapes results after valid fixture contact; read-only diagnostics only")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase63.py")), run_name="__main__")
