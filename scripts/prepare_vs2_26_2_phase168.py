#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
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

/** Read-only production-smoke trace of the exact Create carriage owning each contact-motion vector. */
@Mixin(targets = "com.zurrtum.create.content.contraptions.AbstractContraptionEntity", remap = false)
public abstract class MixinAbstractContraptionEntityContactTrace {
    private static final Logger LOGGER = LogManager.getLogger("VS2-GateE-ContactOwner");
    private static int calls;

    @Inject(method = "getContactPointMotion", at = @At("RETURN"), remap = false, require = 0)
    private void vs2$traceContactOwner(
        net.minecraft.world.phys.Vec3 contactPoint,
        CallbackInfoReturnable<net.minecraft.world.phys.Vec3> cir
    ) {
        if (!java.lang.Boolean.getBoolean("vs2.productionSmoke")) return;
        if (!(Thread.currentThread().getName().contains("Render") || Thread.currentThread().getName().contains("Client"))) return;
        if (++calls > 160) return;
        net.minecraft.world.entity.Entity self = (net.minecraft.world.entity.Entity) (Object) this;
        net.minecraft.world.phys.Vec3 motion = cir.getReturnValue();
        LOGGER.info(
            "GATE_E_PHASE168_CONTACT_OWNER index={} carriage_id={} contact_point={} motion={} carriage_pos={} carriage_delta={} thread={} read_only=true",
            calls, self.getId(), contactPoint, motion, self.position(), self.getDeltaMovement(), Thread.currentThread().getName());
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinAbstractContraptionEntityContactTrace" not in client:
    client.append("MixinAbstractContraptionEntityContactTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

required = [
    "GATE_E_PHASE168_CONTACT_OWNER",
    "getContactPointMotion",
    "self.getId()",
    "self.position()",
    "self.getDeltaMovement()",
    "read_only=true",
]
text = java.read_text(encoding="utf-8")
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 168 lost per-carriage contact trace anchors: " + ", ".join(missing))
for forbidden in ["setPos(", "setDeltaMovement(", ".move(", ".teleport", "setBlock(", "syncCarriage("]:
    if forbidden in text:
        raise SystemExit("Phase 168 introduced forbidden gameplay mutation: " + forbidden)

print("Phase 168: traces the exact Create carriage owning each native contact-motion vector; read-only only")
