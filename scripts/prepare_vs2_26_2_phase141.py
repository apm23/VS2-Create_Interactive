#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContraptionInteractionClientSendTrace.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #216 proved sustained moving-train carry and reported the Create
# right-click helper as handled, while Phase140 saw no server ContraptionInteractionPacket.
# Trace the client network send boundary to distinguish "helper consumed the click" from
# "handlePlayerInteraction returned true and actually emitted Create's C2S packet".
# Read-only diagnostics only; the packet is neither replaced nor cancelled.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.network.protocol.Packet;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(net.minecraft.client.multiplayer.ClientPacketListener.class)
public abstract class MixinCreateContraptionInteractionClientSendTrace {
    @Inject(method = "send(Lnet/minecraft/network/protocol/Packet;)V", at = @At("HEAD"), require = 0)
    private void vs2$traceCreateContraptionPacket(Packet<?> packet, CallbackInfo ci) {
        if (packet == null || !packet.getClass().getName().equals(
                "com.zurrtum.create.infrastructure.packet.c2s.ContraptionInteractionPacket")) return;
        try {
            Object hand = packet.getClass().getMethod("hand").invoke(packet);
            Object target = packet.getClass().getMethod("target").invoke(packet);
            Object localPos = packet.getClass().getMethod("localPos").invoke(packet);
            Object face = packet.getClass().getMethod("face").invoke(packet);
            System.out.println("GATE_F_PHASE141_CLIENT_CONTRAPTION_PACKET_SEND target=" + target
                + " local_pos=" + localPos + " face=" + face + " hand=" + hand
                + " read_only=true");
        } catch (ReflectiveOperationException | RuntimeException exception) {
            System.out.println("GATE_F_PHASE141_CLIENT_CONTRAPTION_PACKET_SEND error="
                + exception.getClass().getSimpleName() + " read_only=true");
        }
    }
}
''', encoding="utf-8")

config = json.loads(mixin_json.read_text(encoding="utf-8"))
client_mixins = config.setdefault("client", [])
name = "MixinCreateContraptionInteractionClientSendTrace"
if name not in client_mixins:
    client_mixins.append(name)
mixin_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

text = java.read_text(encoding="utf-8")
required = [
    "ClientPacketListener.class",
    'method = "send(Lnet/minecraft/network/protocol/Packet;)V"',
    "ContraptionInteractionPacket",
    "GATE_F_PHASE141_CLIENT_CONTRAPTION_PACKET_SEND",
    "read_only=true",
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 141 lost client packet-send trace anchors: " + ", ".join(missing))
for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", ".send(", "cancel()", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in text:
        raise SystemExit("Phase 141 found forbidden mutation/interception: " + forbidden)

print("Phase 141: traces Create ContraptionInteractionPacket at the client send boundary read-only")
