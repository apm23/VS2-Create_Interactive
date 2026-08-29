#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
initializer = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/ValkyrienSkiesModFabric.kt"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = initializer.read_text(encoding="utf-8")
anchor = "        GateDProbe.install()\n"
bootstrap = anchor + "        if (net.fabricmc.loader.api.FabricLoader.getInstance().environmentType == net.fabricmc.api.EnvType.CLIENT) {\n            org.valkyrienskies.mod.fabric.client.GateEClientProbe.install()\n        }\n"
if "GateEClientProbe.install()" not in source:
    if anchor not in source:
        raise SystemExit("Phase 52 could not find GateDProbe.install() anchor")
    source = source.replace(anchor, bootstrap, 1)
    initializer.write_text(source, encoding="utf-8")

probe_source = client_probe.read_text(encoding="utf-8")
old_decl = "public final class GateEClientProbe implements ClientModInitializer {\n    private static final Logger LOGGER = LogManager.getLogger(\"VS2-GateE-Client\");\n    private long ticks;\n\n    @Override\n    public void onInitializeClient() {\n        boolean enabled = Boolean.getBoolean(\"vs2.gateD\") || \"true\".equals(System.getenv(\"GITHUB_ACTIONS\"));\n        if (!enabled) return;\n\n        LOGGER.info(\"GATE_E_CLIENT_READY\");\n        ClientTickEvents.END_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks % 20L != 0L || client.player == null || client.level == null) return;"
new_decl = "public final class GateEClientProbe implements ClientModInitializer {\n    private static final Logger LOGGER = LogManager.getLogger(\"VS2-GateE-Client\");\n    private static boolean installed;\n    private static long ticks;\n\n    @Override\n    public void onInitializeClient() {\n        install();\n    }\n\n    public static synchronized void install() {\n        boolean enabled = Boolean.getBoolean(\"vs2.gateD\") || \"true\".equals(System.getenv(\"GITHUB_ACTIONS\"));\n        if (!enabled || installed) return;\n        installed = true;\n\n        LOGGER.info(\"GATE_D_CLIENT_OBSERVER_READY transport=main_initializer\");\n        ClientTickEvents.START_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks == 1L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_CALLBACK event=start_client_tick\");\n            }\n            if (ticks <= 5L || ticks % 20L == 0L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_HEARTBEAT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n            }\n            if (ticks % 20L != 0L) return;\n            if (client.player == null || client.level == null) {\n                LOGGER.info(\"GATE_D_CLIENT_SAMPLE_WAIT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n                return;\n            }"
if old_decl in probe_source:
    probe_source = probe_source.replace(old_decl, new_decl, 1)
else:
    previous = "LOGGER.info(\"GATE_D_CLIENT_OBSERVER_READY transport=main_initializer\");\n        ClientTickEvents.START_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks == 1L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_CALLBACK event=start_client_tick\");\n            }\n            if (ticks % 20L != 0L || client.player == null || client.level == null) return;"
    replacement = "LOGGER.info(\"GATE_D_CLIENT_OBSERVER_READY transport=main_initializer\");\n        ClientTickEvents.START_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks == 1L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_CALLBACK event=start_client_tick\");\n            }\n            if (ticks <= 5L || ticks % 20L == 0L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_HEARTBEAT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n            }\n            if (ticks % 20L != 0L) return;\n            if (client.player == null || client.level == null) {\n                LOGGER.info(\"GATE_D_CLIENT_SAMPLE_WAIT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n                return;\n            }"
    if previous not in probe_source:
        raise SystemExit("Phase 52 could not find GateEClientProbe client tick registration")
    probe_source = probe_source.replace(previous, replacement, 1)
client_probe.write_text(probe_source, encoding="utf-8")

print("Phase 52: bootstrapped read-only Gate E client observer and traced START_CLIENT_TICK sampling preconditions before carriage lookup; no gameplay or physics behavior is modified")
