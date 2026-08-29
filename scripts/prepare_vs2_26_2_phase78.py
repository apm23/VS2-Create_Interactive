#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContactLeaseTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Phase 78: read-only trace of Create's collidingEntities lease for LocalPlayer.
 * Create refreshes this lease only on surfaceCollision and removes entries once
 * their MutableInt age exceeds three ticks. This mixin proves the exact runtime
 * lease lifetime before any contact-persistence or movement behavior is changed.
 */
@Mixin(targets = "com.zurrtum.create.content.contraptions.AbstractContraptionEntity", remap = false)
public abstract class MixinCreateContactLeaseTrace {
    @Unique private static final Logger VS2_GATE_E_CONTACT_LEASE_LOGGER = LogManager.getLogger("VS2-GateE-ContactLease");
    @Unique private static int vs2$leaseSamples;

    @Inject(method = "tick", at = @At("HEAD"), remap = false, require = 0)
    private void vs2$traceContactLeaseHead(CallbackInfo ci) {
        vs2$traceContactLease("head");
    }

    @Inject(method = "tick", at = @At("TAIL"), remap = false, require = 0)
    private void vs2$traceContactLeaseTail(CallbackInfo ci) {
        vs2$traceContactLease("tail");
    }

    @Unique
    private void vs2$traceContactLease(String stage) {
        LocalPlayer player = Minecraft.getInstance().player;
        if (player == null) return;
        Entity self = (Entity) (Object) this;
        if (!self.level().isClientSide()) return;
        if (!self.getBoundingBox().inflate(4.0).intersects(player.getBoundingBox())) return;
        int sample = ++vs2$leaseSamples;
        if (sample > 160) return;

        try {
            Field field = null;
            Class<?> owner = self.getClass();
            while (owner != null && field == null) {
                try {
                    field = owner.getDeclaredField("collidingEntities");
                } catch (NoSuchFieldException ignored) {
                    owner = owner.getSuperclass();
                }
            }
            if (field == null) return;
            field.setAccessible(true);
            Object raw = field.get(self);
            if (!(raw instanceof Map<?, ?> map)) return;

            Object lease = map.get(player);
            int age = -1;
            if (lease != null) {
                try {
                    Method intValue = lease.getClass().getMethod("intValue");
                    age = ((Number) intValue.invoke(lease)).intValue();
                } catch (ReflectiveOperationException ignored) {
                    try {
                        Method getValue = lease.getClass().getMethod("getValue");
                        age = ((Number) getValue.invoke(lease)).intValue();
                    } catch (ReflectiveOperationException ignoredAgain) {
                        age = -2;
                    }
                }
            }

            Vec3 now = self.position();
            Vec3 frameMotion = Vec3.ZERO;
            try {
                Method prev = self.getClass().getMethod("getPrevPositionVec");
                Object value = prev.invoke(self);
                if (value instanceof Vec3 prevVec) frameMotion = now.subtract(prevVec);
            } catch (ReflectiveOperationException ignored) {
            }

            VS2_GATE_E_CONTACT_LEASE_LOGGER.info(
                "GATE_E_CREATE_CONTACT_LEASE stage={} sample={} present={} age={} map_size={} player_pos={},{},{} carriage_pos={},{},{} frame_motion={},{},{} on_ground={}",
                stage, sample, lease != null, age, map.size(),
                player.getX(), player.getY(), player.getZ(),
                now.x, now.y, now.z,
                frameMotion.x, frameMotion.y, frameMotion.z,
                player.onGround());
        } catch (ReflectiveOperationException | RuntimeException exception) {
            VS2_GATE_E_CONTACT_LEASE_LOGGER.info(
                "GATE_E_CREATE_CONTACT_LEASE_ERROR stage={} type={}", stage, exception.getClass().getSimpleName());
        }
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinCreateContactLeaseTrace" not in client:
    client.append("MixinCreateContactLeaseTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 78: traced Create LocalPlayer collidingEntities lease age and expiry around AbstractContraptionEntity.tick; read-only telemetry only")
