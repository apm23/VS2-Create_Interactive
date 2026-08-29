#!/usr/bin/env python3
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** CI-only trace of the actual Create Fly client collision class. */
@Mixin(targets = "com.zurrtum.create.client.content.contraptions.ContraptionColliderClient", remap = false)
public abstract class MixinContraptionColliderClientTrace {
    private static final Logger LOGGER = LogManager.getLogger("VS2-GateE-ClientCollider");
    private static int calls;

    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)
    private static void vs2$traceClientCollideEntities(CallbackInfo ci) {
        if (++calls <= 32) {
            LOGGER.info("GATE_E_CREATE_CLIENT_COLLIDE_ENTITIES_CALL index={} thread={}", calls, Thread.currentThread().getName());
        }
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinContraptionColliderClientTrace" not in client:
    client.append("MixinContraptionColliderClientTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

# Fix the common shape trace to the runtime signature discovered in Run 66:
# getPotentiallyCollidedShapes(...)->void, not a return value.
trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderTrace.java"
source = trace.read_text(encoding="utf-8")
old = '''    @Inject(method = "getPotentiallyCollidedShapes", at = @At("RETURN"), remap = false, require = 0)
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
    }'''
new = '''    @Inject(method = "getPotentiallyCollidedShapes", at = @At("HEAD"), remap = false, require = 0)
    private static void vs2$tracePotentialShapes(CallbackInfo ci) {
        if (++vs2$shapeCalls <= 32) {
            VS2_GATE_E_LOGGER.info(
                "GATE_E_CREATE_POTENTIAL_SHAPES_CALL index={} thread={}",
                vs2$shapeCalls, Thread.currentThread().getName());
        }
    }'''
if old not in source:
    raise SystemExit("Phase 64 could not find stale getPotentiallyCollidedShapes trace")
source = source.replace(old, new, 1)
trace.write_text(source, encoding="utf-8")

print("Phase 64: traced the actual client-only ContraptionColliderClient path and corrected the common shape hook to its runtime void signature; read-only diagnostics only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase65.py")), run_name="__main__")
