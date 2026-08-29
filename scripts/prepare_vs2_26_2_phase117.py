#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #105 proved the authoritative fixture-only setBlock mutation succeeds
# and runtime reflection exposed Create's public syncCarriage():void on that exact carriage.
# Use that Create-owned synchronization surface only after the disposable smoke mutation
# has been verified. Normal gameplay never enables productionSmokeFixture.
anchor = '''                        if (success) {
                            System.setProperty("vs2.productionNativePlacementMutationProbed", "true")
                            System.setProperty("vs2.productionNativePlacementMutationSucceeded", "true")
                        }'''
replacement = '''                        if (success) {
                            System.setProperty("vs2.productionNativePlacementMutationProbed", "true")
                            System.setProperty("vs2.productionNativePlacementMutationSucceeded", "true")
                            val syncCarriage = carriage?.javaClass?.methods?.firstOrNull { method ->
                                method.name == "syncCarriage" && method.parameterCount == 0
                                    && method.returnType == java.lang.Void.TYPE
                            }
                            var syncInvoked = false
                            if (syncCarriage != null && carriage != null) {
                                syncCarriage.invoke(carriage)
                                syncInvoked = true
                            }
                            System.setProperty("vs2.productionNativePlacementSyncInvoked", java.lang.Boolean.toString(syncInvoked))
                            logger.info("GATE_D_NATIVE_PLACEMENT_CREATE_SYNC carriage_id={} method_found={} invoked={} fixture_only=true",
                                carriageId, syncCarriage != null, syncInvoked)
                        }'''

if "GATE_D_NATIVE_PLACEMENT_CREATE_SYNC" not in server:
    if anchor not in server:
        raise SystemExit("Phase 117 could not find verified Phase 114 mutation success anchor")
    server = server.replace(anchor, replacement, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_CREATE_SYNC',
    'method.name == "syncCarriage"',
    'syncCarriage.invoke(carriage)',
    'vs2.productionNativePlacementSyncInvoked',
    'fixture_only=true',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 117 lost Create sync anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
print("Phase 117: invokes Create public syncCarriage only after verified fixture-only moving-carriage placement; no player, inventory, train control, collision, or physics mutation")

# Production-world #107 proved syncCarriage() is invoked, but the prior observer could be
# skipped when the surrounding support loop was on a sibling carriage. Resolve the exact
# published client entity by id instead of depending on loop-carriage identity.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase118.py")), run_name="__main__")
