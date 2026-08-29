#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #109 reached the delayed client fixture, but the first block-top
# normalization landed on a Copycats/partial-shape location with no simplified Create
# collider beneath the same local X/Z. Phase 67 therefore left best == -1, never ran
# its exact-surface normalization, and the moving carriage immediately outran the
# LocalPlayer. In the disposable productionSmokeFixture only, recover that failed
# under-feet lookup by choosing the globally nearest Create simplified collider and
# moving the fixture's local X/Z to that collider center. The existing Phase 68 code
# then places the fixture exactly on that collider's top. Production gameplay/carry,
# train controls, collision response, and VS2 physics remain untouched.
old = '''                            }
                            if (best >= 0) {
                                Vec3 localTarget = new Vec3(localFeetFixture.x, bestTop, localFeetFixture.z);'''
new = '''                            }
                            if (best < 0 && productionSmokeFixture && colliderCount > 0) {
                                int fallback = -1;
                                double fallbackDistanceSq = Double.POSITIVE_INFINITY;
                                for (int i = 0; i < colliderCount; i++) {
                                    double top = cy[i] + ey[i];
                                    double dx = cx[i] - localFeetFixture.x;
                                    double dy = top - localFeetFixture.y;
                                    double dz = cz[i] - localFeetFixture.z;
                                    double distanceSq = dx * dx + dy * dy + dz * dz;
                                    if (distanceSq < fallbackDistanceSq) {
                                        fallbackDistanceSq = distanceSq;
                                        fallback = i;
                                    }
                                }
                                if (fallback >= 0) {
                                    best = fallback;
                                    bestTop = cy[best] + ey[best];
                                    localFeetFixture = new Vec3(cx[best], localFeetFixture.y, cz[best]);
                                    LOGGER.info(
                                        "GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK carriage_id={} player_tick={} collider_index={} distance_sq={} local_xz={},{} local_top={} fixture_only=true",
                                        carriage.getId(), player.tickCount, best, fallbackDistanceSq,
                                        localFeetFixture.x, localFeetFixture.z, bestTop);
                                }
                            }
                            if (best >= 0) {
                                Vec3 localTarget = new Vec3(localFeetFixture.x, bestTop, localFeetFixture.z);'''

if "GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK" not in source:
    if old not in source:
        raise SystemExit("Phase 119 could not find Phase 68 simplified-collider fixture block")
    source = source.replace(old, new, 1)

required = [
    'best < 0 && productionSmokeFixture && colliderCount > 0',
    'GATE_E_FIXTURE_COLLIDER_NEAREST_FALLBACK',
    'localFeetFixture = new Vec3(cx[best], localFeetFixture.y, cz[best])',
    'Vec3 localTarget = new Vec3(localFeetFixture.x, bestTop, localFeetFixture.z)',
    'fixture_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 119 lost nearest-collider recovery anchors: " + ", ".join(missing))

# The new logic only chooses a fixture-local collider target. The actual setPos already
# belongs to the pre-existing productionSmokeFixture normalization path from Phase 67/68.
for forbidden in [
    'setDeltaMovement(', '.move(', '.teleport', 'setBlock(', '.put(', '.remove(',
    '.clear(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in new:
        raise SystemExit("Phase 119 found unexpected gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 119: production smoke fixture recovers failed under-feet lookup onto the nearest real Create simplified collider; harness-only")
