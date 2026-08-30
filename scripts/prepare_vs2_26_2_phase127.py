#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #128 passed, but its Phase85 replay moved the player by ~15 blocks per
# render tick and the subsequent world-frame delta still showed large relative drift.
# Before changing any compatibility behavior, measure the player's carriage-local position
# every tick across the fixture window. Stable local coordinates are the direct proof we
# need that the player remains attached to one moving train frame despite uneven CI frame time.
anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
probe = '''            if (productionSmokeFixture && player.tickCount >= 14 && player.tickCount <= 32) {
                net.minecraft.world.entity.Entity localFrameCarriage = client.level.getEntitiesOfClass(
                        net.minecraft.world.entity.Entity.class,
                        player.getBoundingBox().inflate(96.0),
                        entity -> "create:carriage_contraption".equals(
                            net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString()))
                    .stream()
                    .min(java.util.Comparator.comparingDouble(entity -> entity.distanceToSqr(player)))
                    .orElse(null);
                if (localFrameCarriage != null) {
                    String localFeet = "unresolved";
                    try {
                        java.lang.reflect.Method toLocal = localFrameCarriage.getClass().getMethod(
                            "toLocalVector", net.minecraft.world.phys.Vec3.class, float.class);
                        Object localValue = toLocal.invoke(localFrameCarriage, player.position(), 0.0f);
                        localFeet = String.valueOf(localValue);
                    } catch (ReflectiveOperationException | RuntimeException localFrameException) {
                        localFeet = "error=" + localFrameException.getClass().getSimpleName();
                    }
                    boolean broadphase = localFrameCarriage.getBoundingBox().inflate(2.0)
                        .expandTowards(0.0, 32.0, 0.0).intersects(player.getBoundingBox());
                    LOGGER.info(
                        "GATE_E_CARRIAGE_LOCAL_CONTINUITY player_tick={} carriage_id={} local_feet={} world_distance_sq={} broadphase={} on_ground={} read_only=true",
                        player.tickCount, localFrameCarriage.getId(), localFeet,
                        localFrameCarriage.distanceToSqr(player), broadphase, player.onGround());
                }
            }

''' + anchor

if "GATE_E_CARRIAGE_LOCAL_CONTINUITY" not in source:
    if anchor not in source:
        raise SystemExit("Phase 127 could not find Gate E state anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_E_CARRIAGE_LOCAL_CONTINUITY',
    'player.tickCount >= 14 && player.tickCount <= 32',
    'toLocalVector',
    'local_feet={}',
    'broadphase={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 127 lost carriage-local continuity anchors: " + ", ".join(missing))

for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', 'setBlock(', '.put(', '.remove(', '.clear(', '.useItemOn(', '.attack(']:
    if forbidden in probe:
        raise SystemExit("Phase 127 found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 127: traces per-tick carriage-local player continuity across the production fixture window; read-only")
