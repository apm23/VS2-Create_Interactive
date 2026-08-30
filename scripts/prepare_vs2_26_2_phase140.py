#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContraptionInteractionServerTrace.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #214 proved stable moving-train carry and a handled native Create
# right-click, but no authoritative STONE new-cell replication followed. Trace the exact
# Create C2S ContraptionInteractionPacket at the server handler boundary before changing
# any placement semantics. Read-only diagnostics only.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(targets = "com.zurrtum.create.AllHandle", remap = false)
public abstract class MixinCreateContraptionInteractionServerTrace {
    @Inject(method = "onContraptionInteraction", at = @At("HEAD"), remap = false)
    private static void vs2$traceContraptionInteraction(@Coerce Object listener, @Coerce Object packet, CallbackInfo ci) {
        try {
            Object hand = packet.getClass().getMethod("hand").invoke(packet);
            Object target = packet.getClass().getMethod("target").invoke(packet);
            Object localPos = packet.getClass().getMethod("localPos").invoke(packet);
            Object face = packet.getClass().getMethod("face").invoke(packet);
            Object player = listener.getClass().getField("player").get(listener);
            Object held = player.getClass().getMethod("getMainHandItem").invoke(player);
            System.out.println("GATE_F_PHASE140_SERVER_CONTRAPTION_INTERACTION target=" + target
                + " local_pos=" + localPos + " face=" + face + " hand=" + hand
                + " server_main_hand=" + held + " read_only=true");
        } catch (ReflectiveOperationException | RuntimeException exception) {
            System.out.println("GATE_F_PHASE140_SERVER_CONTRAPTION_INTERACTION error="
                + exception.getClass().getSimpleName() + " read_only=true");
        }
    }
}
''', encoding="utf-8")

config = json.loads(mixin_json.read_text(encoding="utf-8"))
mixins = config.setdefault("mixins", [])
name = "MixinCreateContraptionInteractionServerTrace"
if name not in mixins:
    mixins.append(name)
mixin_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

text = java.read_text(encoding="utf-8")
required = [
    'targets = "com.zurrtum.create.AllHandle"',
    'method = "onContraptionInteraction"',
    'GATE_F_PHASE140_SERVER_CONTRAPTION_INTERACTION',
    'server_main_hand=',
    'read_only=true',
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 140 lost server interaction trace anchors: " + ", ".join(missing))
for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in text:
        raise SystemExit("Phase 140 found forbidden mutation: " + forbidden)

print("Phase 140: traces Create authoritative contraption interaction packet and server held item read-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase141.py")), run_name="__main__")
