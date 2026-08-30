#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #126 proved the current workflow can accept one perfect carry frame
# during a large frame discontinuity and then lose physical contact before any settled
# interaction ray exists. Add read-only post-bootstrap telemetry at the normal Gate-E
# state sample so we can distinguish Create client-handler bootstrap state from the
# runtime handler and quantify whether the nearest carriage is already leaving the player.
anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
probe = '''            if (productionSmokeFixture && player.tickCount % 10 == 0) {
                String runtimeHandle = "none";
                String runtimeHandlerOwner = "none";
                try {
                    Class<?> handleClass = Class.forName("com.zurrtum.create.AllClientHandle");
                    Object handleInstance = handleClass.getField("INSTANCE").get(null);
                    if (handleInstance != null) {
                        runtimeHandle = handleInstance.getClass().getName();
                        for (java.lang.reflect.Method method : handleInstance.getClass().getMethods()) {
                            if (method.getName().equals("onContraptionBlockChanged") && method.getParameterCount() == 1) {
                                runtimeHandlerOwner = method.getDeclaringClass().getName();
                                break;
                            }
                        }
                    }
                } catch (ReflectiveOperationException | RuntimeException ignoredRuntimeHandler) {
                    runtimeHandle = "error=" + ignoredRuntimeHandler.getClass().getSimpleName();
                }
                double nearestCarriageDistanceSq = Double.POSITIVE_INFINITY;
                boolean nearestBroadphase = false;
                int nearbyCarriages = 0;
                for (net.minecraft.world.entity.Entity candidate : client.level.getEntitiesOfClass(
                        net.minecraft.world.entity.Entity.class, player.getBoundingBox().inflate(96.0),
                        entity -> "create:carriage_contraption".equals(
                            net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString()))) {
                    nearbyCarriages++;
                    double distanceSq = candidate.distanceToSqr(player);
                    if (distanceSq < nearestCarriageDistanceSq) {
                        nearestCarriageDistanceSq = distanceSq;
                        nearestBroadphase = candidate.getBoundingBox().inflate(2.0).expandTowards(0.0, 32.0, 0.0)
                            .intersects(player.getBoundingBox());
                    }
                }
                LOGGER.info(
                    "GATE_E_POST_CARRY_RUNTIME player_tick={} runtime_handle={} handler_owner={} nearby_carriages={} nearest_distance_sq={} nearest_broadphase={} read_only=true",
                    player.tickCount, runtimeHandle, runtimeHandlerOwner, nearbyCarriages, nearestCarriageDistanceSq, nearestBroadphase);
            }

''' + anchor

if "GATE_E_POST_CARRY_RUNTIME" not in source:
    if anchor not in source:
        raise SystemExit("Phase 126 could not find Gate E state anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_E_POST_CARRY_RUNTIME',
    'runtime_handle={}',
    'handler_owner={}',
    'nearest_distance_sq={}',
    'nearest_broadphase={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 126 lost post-carry runtime telemetry anchors: " + ", ".join(missing))

for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', 'setBlock(', '.put(', '.remove(', '.clear(', '.useItemOn(', '.attack(']:
    if forbidden in probe:
        raise SystemExit("Phase 126 found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 126: traces post-bootstrap Create handler ownership and nearest-carriage separation after carry proof; read-only")
