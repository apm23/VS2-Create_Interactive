#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = client_probe.read_text(encoding="utf-8")

old_decl = '''    private static boolean installed;
    private static long ticks;'''
new_decl = '''    private static boolean installed;
    private static boolean createPlayerTypeLogged;
    private static long ticks;'''
if old_decl not in source:
    raise SystemExit("Phase 57 could not find Gate E static-state declaration anchor")
source = source.replace(old_decl, new_decl, 1)

old_ready = '''            var player = client.player;
            var carriageCandidates = client.level.getEntitiesOfClass('''
new_ready = '''            var player = client.player;
            if (!createPlayerTypeLogged) {
                createPlayerTypeLogged = true;
                String createPlayerTypeState;
                try {
                    Class<?> colliderClass = Class.forName("com.zurrtum.create.content.contraptions.ContraptionCollider");
                    java.lang.reflect.Method playerTypeMethod = colliderClass.getDeclaredMethod("getPlayerType", Entity.class);
                    playerTypeMethod.setAccessible(true);
                    Object playerType = playerTypeMethod.invoke(null, player);
                    createPlayerTypeState = String.valueOf(playerType);
                } catch (ReflectiveOperationException | RuntimeException exception) {
                    createPlayerTypeState = "error=" + exception.getClass().getSimpleName();
                }
                LOGGER.info("GATE_E_CREATE_PLAYER_TYPE runtime_type={} player_class={}",
                    createPlayerTypeState, player.getClass().getName());
            }
            var carriageCandidates = client.level.getEntitiesOfClass('''
if old_ready not in source:
    raise SystemExit("Phase 57 could not find ready-player/carriage anchor")
source = source.replace(old_ready, new_ready, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 57: reflected Create ContraptionCollider.getPlayerType for the actual local client player; read-only telemetry only")
