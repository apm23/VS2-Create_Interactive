#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #239 proved the complete current fixture path green: sustained carry,
# handled native Create right-click, recurring authoritative carriage setBlock, and exact
# client replication. The remaining interaction gap is causality: the STONE cell was added
# by the Phase147 server retry, not by the handled native dispatch itself. Earlier packet
# traces emitted no marker, so inventory the exact runtime network send surface immediately
# after the genuine native dispatch before changing any gameplay semantics.
anchor = '''                                                    LOGGER.info("GATE_F_PHASE146_HELD_BLOCK_NATIVE_DISPATCH carriage_id={} player_tick={} invoked=true handled={} client_mirror_injected={} item_after={} server_held_block_armed=true fixture_only=true",
                                                        carriage.getId(), player.tickCount, handled, phase146ClientMirrorInjected, player.getMainHandItem());'''
probe = anchor + '''
                                                    if (!java.lang.Boolean.getBoolean("vs2.productionPhase148NetworkSurfaceProbed")) {
                                                        java.lang.System.setProperty("vs2.productionPhase148NetworkSurfaceProbed", "true");
                                                        Object packetListener = client.getConnection();
                                                        Object connection = null;
                                                        try {
                                                            connection = packetListener == null ? null : packetListener.getClass().getMethod("getConnection").invoke(packetListener);
                                                        } catch (ReflectiveOperationException ignored) {
                                                        }
                                                        StringBuilder listenerSend = new StringBuilder();
                                                        if (packetListener != null) {
                                                            for (java.lang.reflect.Method method : packetListener.getClass().getMethods()) {
                                                                if (method.getName().toLowerCase(java.util.Locale.ROOT).contains("send")) {
                                                                    if (listenerSend.length() > 0) listenerSend.append('|');
                                                                    listenerSend.append(method.toGenericString());
                                                                }
                                                            }
                                                        }
                                                        StringBuilder connectionSend = new StringBuilder();
                                                        if (connection != null) {
                                                            for (java.lang.reflect.Method method : connection.getClass().getMethods()) {
                                                                if (method.getName().toLowerCase(java.util.Locale.ROOT).contains("send")) {
                                                                    if (connectionSend.length() > 0) connectionSend.append('|');
                                                                    connectionSend.append(method.toGenericString());
                                                                }
                                                            }
                                                        }
                                                        LOGGER.info("GATE_F_PHASE148_NATIVE_DISPATCH_NETWORK_SURFACE carriage_id={} player_tick={} native_method={} native_declaring_class={} packet_listener_class={} connection_class={} listener_send_methods={} connection_send_methods={} read_only=true fixture_only=true",
                                                            carriage.getId(), player.tickCount, settledExactRightClickMethod.toGenericString(), settledExactRightClickMethod.getDeclaringClass().getName(),
                                                            packetListener == null ? "null" : packetListener.getClass().getName(),
                                                            connection == null ? "null" : connection.getClass().getName(),
                                                            listenerSend, connectionSend);
                                                    }'''

if "GATE_F_PHASE148_NATIVE_DISPATCH_NETWORK_SURFACE" not in source:
    if anchor not in source:
        raise SystemExit("Phase 148 could not find Phase146 native-dispatch log anchor")
    source = source.replace(anchor, probe, 1)

required = [
    "GATE_F_PHASE148_NATIVE_DISPATCH_NETWORK_SURFACE",
    "settledExactRightClickMethod.toGenericString()",
    "settledExactRightClickMethod.getDeclaringClass().getName()",
    "packetListener.getClass().getMethods()",
    "connection.getClass().getMethods()",
    "read_only=true",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 148 lost native-dispatch network-surface anchors: " + ", ".join(missing))

for forbidden in ["player.setPos(", "player.setDeltaMovement(", ".teleport", "setBlock(", "setSchedule", "setTrain", "setVelocity", ".send("]:
    if forbidden in probe:
        raise SystemExit("Phase 148 found forbidden gameplay/network mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 148: inventories the exact runtime native-dispatch and network send surface read-only after genuine held-block Create interaction")

# Run the evidence-driven support-reacquire de-dup guard after all cumulative carry
# rewrites are installed so it patches the one final Phase85 replay predicate.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase150.py")), run_name="__main__")
