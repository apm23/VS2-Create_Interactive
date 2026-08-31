#!/usr/bin/env python3
import json
import runpy
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
 * Give Create Fly's own LocalPlayer contact lease at most two bounded grace ticks only when
 * that lease reaches its native expiry boundary while a grounded player still overlaps
 * the same carriage. Create remains authoritative: healthy age-0/1/2 leases are untouched,
 * a genuine native age-0 refresh rearms the bounded bridge, and an unrefreshed stale lease
 * is then allowed to expire normally instead of being pinned forever by the adapter.
 */
@Mixin(targets = "com.zurrtum.create.content.contraptions.AbstractContraptionEntity", remap = false)
public abstract class MixinCreateContactLeaseTrace {
    @Unique private static final Logger VS2_GATE_E_CONTACT_LEASE_LOGGER = LogManager.getLogger("VS2-GateE-ContactLease");
    @Unique private static int vs2$leaseSamples;
    @Unique private int vs2$leaseGraceTicks;

    @Inject(method = "tick", at = @At("HEAD"), remap = false, require = 0)
    private void vs2$preserveAndTraceContactLeaseHead(CallbackInfo ci) {
        vs2$traceContactLease("head", true);
    }

    @Inject(method = "tick", at = @At("TAIL"), remap = false, require = 0)
    private void vs2$traceContactLeaseTail(CallbackInfo ci) {
        vs2$traceContactLease("tail", false);
    }

    @Unique
    private void vs2$traceContactLease(String stage, boolean allowGrace) {
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

            if (lease == null) {
                vs2$leaseGraceTicks = 0;
            } else if (allowGrace && age == 0) {
                // Only a real Create surfaceCollision can naturally return the lease to age 0;
                // rearm the bounded bridge for a later short native sampling gap.
                vs2$leaseGraceTicks = 0;
            }

            boolean graced = false;
            if (allowGrace
                    && Boolean.getBoolean("vs2.createCarryCompat")
                    && lease != null
                    && age >= 3
                    && vs2$leaseGraceTicks < 2
                    && player.onGround()
                    && self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox())) {
                for (Method method : lease.getClass().getMethods()) {
                    if (!method.getName().equals("setValue") || method.getParameterCount() != 1) continue;
                    Class<?> parameter = method.getParameterTypes()[0];
                    if (parameter == int.class || parameter == Integer.class || Number.class.isAssignableFrom(parameter)) {
                        // Keep the native lease at its expiry edge for at most two ticks. Run 515
                        // proved Create can miss two consecutive native contact publications while
                        // the LocalPlayer remains grounded on the same carriage. Do not reset to 0:
                        // that would impersonate native surface contact and could pin stale leases.
                        method.invoke(lease, Integer.valueOf(2));
                        graced = true;
                        age = 2;
                        vs2$leaseGraceTicks++;
                        break;
                    }
                }
                if (graced) {
                    VS2_GATE_E_CONTACT_LEASE_LOGGER.info(
                        "GATE_E_CREATE_CONTACT_LEASE_GRACE carriage_id={} player_tick={} grace_tick={}/2 native_create_lease=true bounded_bridge=true adapter_only=true",
                        self.getId(), player.tickCount, vs2$leaseGraceTicks);
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
                "GATE_E_CREATE_CONTACT_LEASE stage={} sample={} present={} age={} graced={} grace_ticks={} map_size={} player_pos={},{},{} carriage_pos={},{},{} frame_motion={},{},{} on_ground={}",
                stage, sample, lease != null, age, graced, vs2$leaseGraceTicks, map.size(),
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

text = java.read_text(encoding="utf-8")
required = [
    'Boolean.getBoolean("vs2.createCarryCompat")',
    'map.get(player)',
    'age >= 3',
    'vs2$leaseGraceTicks < 2',
    'player.onGround()',
    'method.getName().equals("setValue")',
    'method.invoke(lease, Integer.valueOf(2))',
    'vs2$leaseGraceTicks++',
    'GATE_E_CREATE_CONTACT_LEASE_GRACE',
    'grace_tick={}/2',
    'bounded_bridge=true',
    'native_create_lease=true',
    'adapter_only=true',
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 78 lost bounded native Create contact-lease anchors: " + ", ".join(missing))
for forbidden in [
    'method.invoke(lease, Integer.valueOf(0))',
    'setPos(', 'setDeltaMovement(', '.move(', '.teleport(', 'setBlock(',
    'getContactPointMotion(', 'cir.setReturnValue(',
]:
    if forbidden in text:
        raise SystemExit("Phase 78 contains forbidden lease pinning/synthetic movement/gameplay mutation: " + forbidden)

print("Phase 78: bridges at most two consecutive native Create contact-sampling gaps after genuine refresh; Create remains authoritative and stale leases still expire")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase79.py")), run_name="__main__")
