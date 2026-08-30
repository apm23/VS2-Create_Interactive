#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContraptionInteractionConnectionSendTrace.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #225 still proved handled native dispatch but emitted no Phase141 marker
# even after unwrapping ServerboundCustomPayloadPacket at ClientPacketListener.send(Packet).
# Move the read-only observation one layer lower to Connection.send so we can distinguish an
# alternate ClientPacketListener overload/path from Create never emitting its C2S payload.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.network.protocol.Packet;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(net.minecraft.network.Connection.class)
public abstract class MixinCreateContraptionInteractionConnectionSendTrace {
    @Inject(method = "send(Lnet/minecraft/network/protocol/Packet;)V", at = @At("HEAD"), require = 0)
    private void vs2$traceConnectionSend(Packet<?> packet, CallbackInfo ci) {
        vs2$trace(packet, "send1");
    }

    private static void vs2$trace(Packet<?> packet, String path) {
        if (packet == null) return;
        try {
            Object payload = packet;
            String outer = packet.getClass().getName();
            if (outer.equals("net.minecraft.network.protocol.common.ServerboundCustomPayloadPacket")) {
                payload = packet.getClass().getMethod("payload").invoke(packet);
            }
            String payloadClass = payload == null ? "null" : payload.getClass().getName();
            if (!payloadClass.equals("com.zurrtum.create.infrastructure.packet.c2s.ContraptionInteractionPacket")) return;
            Object hand = payload.getClass().getMethod("hand").invoke(payload);
            Object target = payload.getClass().getMethod("target").invoke(payload);
            Object localPos = payload.getClass().getMethod("localPos").invoke(payload);
            Object face = payload.getClass().getMethod("face").invoke(payload);
            System.out.println("GATE_F_PHASE143_CONNECTION_CONTRAPTION_PACKET_SEND path=" + path
                + " outer=" + outer + " payload=" + payloadClass + " target=" + target
                + " local_pos=" + localPos + " face=" + face + " hand=" + hand
                + " read_only=true");
        } catch (ReflectiveOperationException | RuntimeException exception) {
            System.out.println("GATE_F_PHASE143_CONNECTION_CONTRAPTION_PACKET_SEND error="
                + exception.getClass().getSimpleName() + " read_only=true");
        }
    }
}
''', encoding="utf-8")

config = json.loads(mixin_json.read_text(encoding="utf-8"))
client_mixins = config.setdefault("client", [])
name = "MixinCreateContraptionInteractionConnectionSendTrace"
if name not in client_mixins:
    client_mixins.append(name)
mixin_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

text = java.read_text(encoding="utf-8")
required = [
    "Connection.class",
    'method = "send(Lnet/minecraft/network/protocol/Packet;)V"',
    "ServerboundCustomPayloadPacket",
    "ContraptionInteractionPacket",
    "GATE_F_PHASE143_CONNECTION_CONTRAPTION_PACKET_SEND",
    "read_only=true",
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 143 lost connection-send trace anchors: " + ", ".join(missing))
for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", "cancel()", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in text:
        raise SystemExit("Phase 143 found forbidden mutation/interception: " + forbidden)

print("Phase 143: traces Create ContraptionInteractionPacket at Connection.send read-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase144.py")), run_name="__main__")
