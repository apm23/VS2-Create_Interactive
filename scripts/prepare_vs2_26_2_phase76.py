#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerSetPosTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Phase 76: read-only trace of direct LocalPlayer setPos calls.
 * This distinguishes a missing Create carry setPos from a later position reset.
 * No position, motion, collision response, train control, or physics is modified.
 */
@Mixin(Entity.class)
public abstract class MixinEntityLocalPlayerSetPosTrace {
    @Unique private static final Logger VS2_GATE_E_SET_POS_LOGGER = LogManager.getLogger("VS2-GateE-SetPos");
    @Unique private static int vs2$setPosCalls;

    @Inject(method = "setPos(DDD)V", at = @At("HEAD"), require = 0)
    private void vs2$traceLocalPlayerSetPos(double x, double y, double z, CallbackInfo ci) {
        Entity self = (Entity) (Object) this;
        if (!(self instanceof LocalPlayer)) return;
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        int index = ++vs2$setPosCalls;
        if (index > 180) return;

        StackTraceElement[] stack = Thread.currentThread().getStackTrace();
        StringBuilder callers = new StringBuilder();
        for (StackTraceElement frame : stack) {
            String owner = frame.getClassName();
            if (owner.equals(Thread.class.getName()) || owner.equals(MixinEntityLocalPlayerSetPosTrace.class.getName())) continue;
            if (!(owner.contains("zurrtum.create") || owner.contains("valkyrienskies") || owner.startsWith("net.minecraft.client"))) continue;
            if (callers.length() > 0) callers.append('|');
            callers.append(owner).append('#').append(frame.getMethodName()).append(':').append(frame.getLineNumber());
            if (callers.toString().split("\\|").length >= 6) break;
        }

        VS2_GATE_E_SET_POS_LOGGER.info(
            "GATE_E_LOCALPLAYER_SET_POS index={} from={},{},{} to={},{},{} delta={},{},{} on_ground={} thread={} callers={}",
            index,
            self.getX(), self.getY(), self.getZ(),
            x, y, z,
            x - self.getX(), y - self.getY(), z - self.getZ(),
            self.onGround(), thread, callers);
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinEntityLocalPlayerSetPosTrace" not in client:
    client.append("MixinEntityLocalPlayerSetPosTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 76: traced direct LocalPlayer setPos callers to distinguish missing Create carry application from later client position reset; read-only telemetry only")
