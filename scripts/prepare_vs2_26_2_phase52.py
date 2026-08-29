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
new_decl = "public final class GateEClientProbe implements ClientModInitializer {\n    private static final Logger LOGGER = LogManager.getLogger(\"VS2-GateE-Client\");\n    private static boolean installed;\n    private static long ticks;\n\n    @Override\n    public void onInitializeClient() {\n        install();\n    }\n\n    public static synchronized void install() {\n        boolean enabled = Boolean.getBoolean(\"vs2.gateD\") || \"true\".equals(System.getenv(\"GITHUB_ACTIONS\"));\n        if (!enabled || installed) return;\n        installed = true;\n\n        LOGGER.info(\"GATE_D_CLIENT_OBSERVER_READY transport=main_initializer\");\n        ClientTickEvents.START_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks == 1L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_CALLBACK event=start_client_tick\");\n            }\n            if (ticks <= 5L || ticks % 20L == 0L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_HEARTBEAT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n            }\n            boolean clientReady = client.player != null && client.level != null;\n            if (!clientReady) {\n                if (ticks % 20L == 0L) {\n                    LOGGER.info(\"GATE_D_CLIENT_SAMPLE_WAIT tick={} player_present={} level_present={}\",\n                        ticks, client.player != null, client.level != null);\n                }\n                return;\n            }\n            // Sample every ready tick. The smoke harness can observe train motion and terminate\n            // between 20-tick boundaries, so waiting for ticks % 20 would miss the only useful\n            // local-player/Create collision window. This remains read-only telemetry."
if old_decl in probe_source:
    probe_source = probe_source.replace(old_decl, new_decl, 1)
else:
    previous = "LOGGER.info(\"GATE_D_CLIENT_OBSERVER_READY transport=main_initializer\");\n        ClientTickEvents.START_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks == 1L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_CALLBACK event=start_client_tick\");\n            }\n            if (ticks <= 5L || ticks % 20L == 0L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_HEARTBEAT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n            }\n            if (ticks % 20L != 0L) return;\n            if (client.player == null || client.level == null) {\n                LOGGER.info(\"GATE_D_CLIENT_SAMPLE_WAIT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n                return;\n            }"
    replacement = "LOGGER.info(\"GATE_D_CLIENT_OBSERVER_READY transport=main_initializer\");\n        ClientTickEvents.START_CLIENT_TICK.register(client -> {\n            ticks++;\n            if (ticks == 1L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_CALLBACK event=start_client_tick\");\n            }\n            if (ticks <= 5L || ticks % 20L == 0L) {\n                LOGGER.info(\"GATE_D_CLIENT_TICK_HEARTBEAT tick={} player_present={} level_present={}\",\n                    ticks, client.player != null, client.level != null);\n            }\n            boolean clientReady = client.player != null && client.level != null;\n            if (!clientReady) {\n                if (ticks % 20L == 0L) {\n                    LOGGER.info(\"GATE_D_CLIENT_SAMPLE_WAIT tick={} player_present={} level_present={}\",\n                        ticks, client.player != null, client.level != null);\n                }\n                return;\n            }\n            // Sample every ready tick so Gate E cannot be skipped by smoke termination between boundaries."
    if previous not in probe_source:
        raise SystemExit("Phase 52 could not find GateEClientProbe client tick registration")
    probe_source = probe_source.replace(previous, replacement, 1)

old_reflection = '''                Field field = carriage.getClass().getDeclaredField("collidingEntities");
                field.setAccessible(true);
                Object value = field.get(carriage);'''
new_reflection = '''                Field field = null;
                Class<?> owner = carriage.getClass();
                while (owner != null && field == null) {
                    try {
                        field = owner.getDeclaredField("collidingEntities");
                    } catch (NoSuchFieldException ignored) {
                        owner = owner.getSuperclass();
                    }
                }
                if (field == null) throw new NoSuchFieldException("collidingEntities");
                field.setAccessible(true);
                Object value = field.get(carriage);
                contactFieldState = "owner=" + field.getDeclaringClass().getName();'''
if old_reflection in probe_source:
    probe_source = probe_source.replace(old_reflection, new_reflection, 1)

old_state = '''            LOGGER.info(
                "GATE_E_CLIENT_STATE player_pos={},{},{} on_ground={} velocity={},{},{} carriage_pos={},{},{} carriage_box={},{},{} -> {},{},{} create_registered_contact={} contact_field={}",
                player.getX(), player.getY(), player.getZ(), player.onGround(),
                velocity.x, velocity.y, velocity.z,
                carriage.getX(), carriage.getY(), carriage.getZ(),
                box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ,
                createRegisteredContact, contactFieldState);'''
new_state = '''            var playerBox = player.getBoundingBox();
            boolean collisionEligible = carriage.canCollideWith(player);
            boolean broadphaseOverlap = box.inflate(2.0).expandTowards(0.0, 32.0, 0.0).intersects(playerBox);
            LOGGER.info(
                "GATE_E_CLIENT_STATE player_pos={},{},{} player_box={},{},{} -> {},{},{} on_ground={} velocity={},{},{} carriage_pos={},{},{} carriage_box={},{},{} -> {},{},{} can_collide={} broadphase_overlap={} player_alive={} create_registered_contact={} contact_field={}",
                player.getX(), player.getY(), player.getZ(),
                playerBox.minX, playerBox.minY, playerBox.minZ, playerBox.maxX, playerBox.maxY, playerBox.maxZ,
                player.onGround(), velocity.x, velocity.y, velocity.z,
                carriage.getX(), carriage.getY(), carriage.getZ(),
                box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ,
                collisionEligible, broadphaseOverlap, player.isAlive(), createRegisteredContact, contactFieldState);'''
if old_state not in probe_source:
    raise SystemExit("Phase 52 could not find Gate E state log block")
probe_source = probe_source.replace(old_state, new_state, 1)
client_probe.write_text(probe_source, encoding="utf-8")

print("Phase 52: Gate E validates Create collision eligibility/broadphase plus resolved collidingEntities map on every client-ready tick; telemetry remains read-only and no gameplay or physics behavior is modified")
