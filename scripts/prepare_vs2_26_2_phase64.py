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
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Adapter around the actual Create Fly client collision path. Create remains authoritative for
 * carriage contact and collision geometry.
 *
 * Two narrow LocalPlayer semantics are repaired while the explicit VS2/Create carry mode is on:
 * 1) a real upward jump must not be rewritten to grounded by same-tick Create contact; and
 * 2) when Create itself finishes the collision pass with LocalPlayer grounded, its final native
 *    motion write must not retain a downward Y component. #726 proved that the retained negative
 *    Y is consumed by vanilla on the next tick and progressively sinks the player through the
 *    moving floor even while Create keeps onGround=true.
 *
 * The second rule does not synthesize carry velocity or a floor height. It only makes Create's
 * own final motion state consistent with Create's own grounded decision; X/Z and upward motion are
 * untouched, and no position, gravity, collision shape/vector, train state, or world state is
 * manufactured here.
 */
@Mixin(targets = "com.zurrtum.create.client.content.contraptions.ContraptionColliderClient", remap = false)
public abstract class MixinContraptionColliderClientTrace {
    private static final Logger LOGGER = LogManager.getLogger("VS2-GateE-ClientCollider");
    private static int calls;
    private static int groundedVerticalClips;

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
            target = "Lnet/minecraft/world/entity/Entity;setDeltaMovement(Lnet/minecraft/world/phys/Vec3;)V",
            ordinal = 2
        ),
        remap = false,
        require = 0
    )
    private static void vs2$clipGroundedLocalPlayerDownwardMotion(Entity entity, Vec3 motion) {
        boolean groundedLocalPlayer = Boolean.getBoolean("vs2.createCarryCompat")
            && "net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName())
            && entity.onGround();
        Vec3 appliedMotion = motion;
        if (groundedLocalPlayer && motion.y < 0.0) {
            appliedMotion = new Vec3(motion.x, 0.0, motion.z);
            int index = ++groundedVerticalClips;
            if (index <= 64) {
                LOGGER.info(
                    "GATE_E_CREATE_GROUNDED_Y_CLIP index={} player_tick={} before_y={} after_y={} pos={},{},{} thread={}",
                    index, entity.tickCount, motion.y, appliedMotion.y,
                    entity.getX(), entity.getY(), entity.getZ(), Thread.currentThread().getName());
            }
        }
        entity.setDeltaMovement(appliedMotion);
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
for forbidden in [
    "setPos(", ".move(", ".teleport(", "setVelocity(",
    "setBlock(", "syncCarriage(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 64 collision adapter introduced forbidden gameplay mutation: " + forbidden)
if inserted.count("entity.setDeltaMovement(appliedMotion)") != 1:
    raise SystemExit("Phase 64 must contain exactly one final native-motion redirect write")

print("Phase 64: preserves upward LocalPlayer airborne semantics and clips only retained downward Y after Create itself marks the LocalPlayer grounded")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase65.py")), run_name="__main__")
