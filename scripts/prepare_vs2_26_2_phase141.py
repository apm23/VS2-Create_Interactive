#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContraptionInteractionClientSendTrace.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #224 proved the authoritative server-arm handshake and held-block native
# helper invocation both complete with handled=true, yet the previous Phase141 telemetry saw
# no ContraptionInteractionPacket. On MC 26.2/Fabric, custom payloads travel through a vanilla
# ServerboundCustomPayloadPacket wrapper, so comparing the outer Packet class directly to
# Create's payload class can silently miss a real send. Unwrap payload() read-only before
# filtering. This changes telemetry only; no packet is replaced, cancelled, duplicated, or sent.
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
        if (packet == null) return;
        Object candidate = packet;
        String wrapperClass = packet.getClass().getName();
        try {
            if (wrapperClass.endsWith("ServerboundCustomPayloadPacket")) {
                candidate = packet.getClass().getMethod("payload").invoke(packet);
            }
            if (candidate == null || !candidate.getClass().getName().equals(
                    "com.zurrtum.create.infrastructure.packet.c2s.ContraptionInteractionPacket")) return;
            Object hand = candidate.getClass().getMethod("hand").invoke(candidate);
            Object target = candidate.getClass().getMethod("target").invoke(candidate);
            Object localPos = candidate.getClass().getMethod("localPos").invoke(candidate);
            Object face = candidate.getClass().getMethod("face").invoke(candidate);
            System.out.println("GATE_F_PHASE141_CLIENT_CONTRAPTION_PACKET_SEND wrapper=" + wrapperClass
                + " payload=" + candidate.getClass().getName() + " target=" + target
                + " local_pos=" + localPos + " face=" + face + " hand=" + hand
                + " unwrapped_custom_payload=true read_only=true");
        } catch (ReflectiveOperationException | RuntimeException exception) {
            if (wrapperClass.contains("CustomPayload")) {
                System.out.println("GATE_F_PHASE141_CLIENT_CONTRAPTION_PACKET_SEND wrapper=" + wrapperClass
                    + " error=" + exception.getClass().getSimpleName()
                    + " unwrap_attempted=true read_only=true");
            }
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
    "ServerboundCustomPayloadPacket",
    'getMethod("payload")',
    "ContraptionInteractionPacket",
    "GATE_F_PHASE141_CLIENT_CONTRAPTION_PACKET_SEND",
    "unwrapped_custom_payload=true",
    "read_only=true",
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 141 lost client packet-send unwrap anchors: " + ", ".join(missing))
for forbidden in ["setPos(", "setDeltaMovement(", ".teleport", "setBlock(", "setItemSlot(", ".send(", "cancel()", "setSchedule", "setTrain", "setVelocity"]:
    if forbidden in text:
        raise SystemExit("Phase 141 found forbidden mutation/interception: " + forbidden)

print("Phase 141: unwraps vanilla custom-payload packet and traces Create ContraptionInteractionPacket read-only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase142.py")), run_name="__main__")
