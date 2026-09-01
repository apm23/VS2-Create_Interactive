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

import net.minecraft.world.entity.Entity;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Adapter around the actual Create Fly client collision path. Create remains authoritative for
 * carriage contact and horizontal carry. When vanilla LocalPlayer has a real upward jump velocity,
 * however, a same-tick moving-contraption contact must not rewrite that airborne state back to
 * grounded or snap the player's Y to Create's grounded contact correction. Preserve vanilla's
 * rising Y only at that first Create setPos call while still forwarding Create's X/Z and leaving
 * every grounded/non-rising collision unchanged. No synthetic velocity, gravity, carry vector,
 * train state, or world state is introduced here.
 */
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

    @Redirect(
        method = "collideEntities",
        at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/Entity;setOnGround(Z)V"),
        remap = false,
        require = 0
    )
    private static void vs2$preserveVanillaAirborneDuringCreateCarry(Entity entity, boolean onGround) {
        boolean risingLocalPlayer = Boolean.getBoolean("vs2.createCarryCompat")
            && "net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName())
            && entity.getDeltaMovement().y > 0.05;
        entity.setOnGround(onGround && !risingLocalPlayer);
    }

    @Redirect(
        method = "collideEntities",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/world/entity/Entity;setPos(DDD)V",
            ordinal = 0
        ),
        remap = false,
        require = 0
    )
    private static void vs2$preserveVanillaRisingYDuringCreateContact(Entity entity, double x, double y, double z) {
        boolean risingLocalPlayer = Boolean.getBoolean("vs2.createCarryCompat")
            && "net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName())
            && entity.getDeltaMovement().y > 0.05
            && y > entity.getY() + 0.05;
        entity.setPos(x, risingLocalPlayer ? entity.getY() : y, z);
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

inserted = java.read_text(encoding="utf-8")
if inserted.count("entity.setPos(") != 1:
    raise SystemExit("Phase 64 airborne adapter expected exactly one native Create setPos forwarding boundary")
for forbidden in [
    "setDeltaMovement(", ".move(", ".teleport(", "setVelocity(",
    "setBlock(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 64 airborne adapter introduced forbidden gameplay mutation: " + forbidden)

print("Phase 64: keeps Create horizontal carry authoritative while preserving vanilla rising Y across the first grounded contact correction")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase65.py")), run_name="__main__")
