#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #155 exposed a telemetry-only sibling-carriage race: Phase85/Phase130
# were carrying against carryBaselineCarriageId=8 while Phase127 independently chose the
# nearest carriage and reported ids 7/10. That made the workflow compare local positions
# in different moving frames even while the actual carry delta reached zero. Prefer the
# already-active carry baseline carriage for continuity telemetry, falling back to nearest
# only before that baseline exists. No gameplay, collision, train, or physics state changes.
anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
probe = '''            if (productionSmokeFixture && player.tickCount >= 14 && player.tickCount <= 40) {
                net.minecraft.world.entity.Entity localFrameCarriage = null;
                if (carryBaselineCarriageId != Integer.MIN_VALUE) {
                    net.minecraft.world.entity.Entity baselineEntity = client.level.getEntity(carryBaselineCarriageId);
                    if (baselineEntity != null && "create:carriage_contraption".equals(
                            net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(baselineEntity.getType()).toString())) {
                        localFrameCarriage = baselineEntity;
                    }
                }
                if (localFrameCarriage == null) {
                    localFrameCarriage = client.level.getEntitiesOfClass(
                            net.minecraft.world.entity.Entity.class,
                            player.getBoundingBox().inflate(96.0),
                            entity -> "create:carriage_contraption".equals(
                                net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString()))
                        .stream()
                        .min(java.util.Comparator.comparingDouble(entity -> entity.distanceToSqr(player)))
                        .orElse(null);
                }
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
                    boolean baselineFrame = localFrameCarriage.getId() == carryBaselineCarriageId;
                    LOGGER.info(
                        "GATE_E_CARRIAGE_LOCAL_CONTINUITY player_tick={} carriage_id={} local_feet={} world_distance_sq={} broadphase={} on_ground={} baseline_frame={} read_only=true",
                        player.tickCount, localFrameCarriage.getId(), localFeet,
                        localFrameCarriage.distanceToSqr(player), broadphase, player.onGround(), baselineFrame);
                }
            }

''' + anchor

if "baseline_frame={}" not in source:
    if "GATE_E_CARRIAGE_LOCAL_CONTINUITY" in source:
        start = source.find('            if (productionSmokeFixture && player.tickCount >= 14')
        end = source.find(anchor, start)
        if start < 0 or end < 0:
            raise SystemExit("Phase 127 could not replace existing continuity telemetry block")
        source = source[:start] + probe[:-len(anchor)] + source[end:]
    else:
        if anchor not in source:
            raise SystemExit("Phase 127 could not find Gate E state anchor")
        source = source.replace(anchor, probe, 1)

required = [
    'GATE_E_CARRIAGE_LOCAL_CONTINUITY',
    'player.tickCount >= 14 && player.tickCount <= 40',
    'client.level.getEntity(carryBaselineCarriageId)',
    'localFrameCarriage.getId() == carryBaselineCarriageId',
    'toLocalVector',
    'local_feet={}',
    'baseline_frame={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 127 lost carriage-local continuity anchors: " + ", ".join(missing))

for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', 'setBlock(', '.put(', '.remove(', '.clear(', '.useItemOn(', '.attack(']:
    if forbidden in probe:
        raise SystemExit("Phase 127 found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 127: traces carriage-local continuity in the active carry baseline frame; read-only sibling-carriage telemetry fix")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase128.py")), run_name="__main__")
