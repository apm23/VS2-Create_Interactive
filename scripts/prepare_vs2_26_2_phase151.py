#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
connection_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContraptionInteractionConnectionSendTrace.java"

source = client_probe.read_text(encoding="utf-8")
trace = connection_trace.read_text(encoding="utf-8")

# Production-world #247 is green for sustained moving-train carry, handled native Create
# right-click and authoritative fixture placement replication, but the all-overload Phase143
# Connection trace still emitted no ContraptionInteractionPacket marker. Phase145 already
# documents why that matters: generic held-block placement is not Create's
# handlePlayerInteraction packet path, so the current successful STONE mutation is a
# fixture-after-native-dispatch proof, not proof that ordinary user placement travels through
# Create's native C2S interaction packet. Record that distinction at runtime and inventory the
# exact Fabric networking + Create carriage mutation surfaces read-only before introducing any
# production placement bridge.
trace_anchor = '''            System.out.println("GATE_F_PHASE143_CONNECTION_CONTRAPTION_PACKET_SEND path=" + path
                + " outer=" + outer + " payload=" + payloadClass + " target=" + target
                + " local_pos=" + localPos + " face=" + face + " hand=" + hand
                + " read_only=true");'''
trace_replacement = '''            System.setProperty("vs2.phase151NativeContraptionInteractionPacketObserved", "true");
            System.out.println("GATE_F_PHASE143_CONNECTION_CONTRAPTION_PACKET_SEND path=" + path
                + " outer=" + outer + " payload=" + payloadClass + " target=" + target
                + " local_pos=" + localPos + " face=" + face + " hand=" + hand
                + " read_only=true");'''
if "vs2.phase151NativeContraptionInteractionPacketObserved" not in trace:
    if trace_anchor not in trace:
        raise SystemExit("Phase 151 could not find Phase143 packet trace anchor")
    trace = trace.replace(trace_anchor, trace_replacement, 1)
connection_trace.write_text(trace, encoding="utf-8")

anchor = '''                                                        LOGGER.info("GATE_F_PHASE148_NATIVE_DISPATCH_NETWORK_SURFACE carriage_id={} player_tick={} native_method={} native_declaring_class={} packet_listener_class={} connection_class={} listener_send_methods={} connection_send_methods={} read_only=true fixture_only=true",
                                                            carriage.getId(), player.tickCount, settledExactRightClickMethod.toGenericString(), settledExactRightClickMethod.getDeclaringClass().getName(),
                                                            packetListener == null ? "null" : packetListener.getClass().getName(),
                                                            connection == null ? "null" : connection.getClass().getName(),
                                                            listenerSend, connectionSend);'''
probe = anchor + '''
                                                        if (!java.lang.Boolean.getBoolean("vs2.productionPhase151PlacementSurfaceProbed")) {
                                                            java.lang.System.setProperty("vs2.productionPhase151PlacementSurfaceProbed", "true");
                                                            boolean nativeContraptionPacketObserved = java.lang.Boolean.getBoolean("vs2.phase151NativeContraptionInteractionPacketObserved");
                                                            StringBuilder clientNetworkingMethods = new StringBuilder();
                                                            StringBuilder serverNetworkingMethods = new StringBuilder();
                                                            try {
                                                                Class<?> clientNetworking = Class.forName("net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking");
                                                                for (java.lang.reflect.Method method : clientNetworking.getMethods()) {
                                                                    String methodName = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                    if (methodName.contains("send") || methodName.contains("register")) {
                                                                        if (clientNetworkingMethods.length() > 0) clientNetworkingMethods.append('|');
                                                                        clientNetworkingMethods.append(method.toGenericString());
                                                                    }
                                                                }
                                                            } catch (ReflectiveOperationException | LinkageError exception) {
                                                                clientNetworkingMethods.append("unavailable:").append(exception.getClass().getSimpleName());
                                                            }
                                                            try {
                                                                Class<?> serverNetworking = Class.forName("net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking");
                                                                for (java.lang.reflect.Method method : serverNetworking.getMethods()) {
                                                                    String methodName = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                    if (methodName.contains("send") || methodName.contains("register")) {
                                                                        if (serverNetworkingMethods.length() > 0) serverNetworkingMethods.append('|');
                                                                        serverNetworkingMethods.append(method.toGenericString());
                                                                    }
                                                                }
                                                            } catch (ReflectiveOperationException | LinkageError exception) {
                                                                serverNetworkingMethods.append("unavailable:").append(exception.getClass().getSimpleName());
                                                            }
                                                            StringBuilder carriageMutationMethods = new StringBuilder();
                                                            for (java.lang.reflect.Method method : carriage.getClass().getMethods()) {
                                                                String methodName = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                if (methodName.equals("setblock") || methodName.equals("synccarriage") || methodName.contains("playerinteraction")) {
                                                                    if (carriageMutationMethods.length() > 0) carriageMutationMethods.append('|');
                                                                    carriageMutationMethods.append(method.toGenericString());
                                                                }
                                                            }
                                                            LOGGER.info("GATE_F_PHASE151_GENERIC_HELD_BLOCK_NATIVE_GAP carriage_id={} player_tick={} native_dispatch_handled={} native_contraption_packet_observed={} placement_origin=fixture_after_native_dispatch client_networking_methods={} server_networking_methods={} carriage_mutation_methods={} read_only=true fixture_only=true",
                                                                carriage.getId(), player.tickCount, handled, nativeContraptionPacketObserved,
                                                                clientNetworkingMethods, serverNetworkingMethods, carriageMutationMethods);
                                                        }'''
if "GATE_F_PHASE151_GENERIC_HELD_BLOCK_NATIVE_GAP" not in source:
    if anchor not in source:
        raise SystemExit("Phase 151 could not find Phase148 network-surface anchor")
    source = source.replace(anchor, probe, 1)

required = [
    "GATE_F_PHASE151_GENERIC_HELD_BLOCK_NATIVE_GAP",
    "native_contraption_packet_observed={}",
    "placement_origin=fixture_after_native_dispatch",
    "ClientPlayNetworking",
    "ServerPlayNetworking",
    "carriageMutationMethods",
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 151 lost held-block gap/network inventory anchors: " + ", ".join(missing))

for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity", "ClientPlayNetworking.send(", "ServerPlayNetworking.send("]:
    if forbidden in probe:
        raise SystemExit("Phase 151 introduced forbidden gameplay/network mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 151: proves generic held-block native packet gap and inventories a production placement-bridge surface read-only")
