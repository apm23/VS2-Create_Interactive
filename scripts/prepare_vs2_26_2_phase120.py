#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #111 proved movement/carry and native interaction targeting, and its
# fixture-only placement mutation succeeded on the authoritative moving carriage. The
# artifact also proved the client never observed that STONE entry. Log ordering exposed
# the concrete harness bug: Phase 117's syncCarriage() call patched an earlier mutation
# success block, so GATE_D_NATIVE_PLACEMENT_CREATE_SYNC happened before the later
# GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION that actually added the empty-cell block.
# Synchronize the exact carriage immediately after *that* verified retry mutation.
# This remains disposable productionSmokeFixture-only and does not alter normal gameplay.
old = '''                        if (success) {
                            System.setProperty("vs2.productionNativePlacementMutationProbed", "true")
                            System.setProperty("vs2.productionNativePlacementMutationSucceeded", "true")
                        }
                        logger.info("GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION carriage_id={} hit_local={} empty_local={} invoked={} before_size={} after_size={} state_match={} source_identity_stable={} success={} fixture_only=true",'''
new = '''                        if (success) {
                            System.setProperty("vs2.productionNativePlacementMutationProbed", "true")
                            System.setProperty("vs2.productionNativePlacementMutationSucceeded", "true")
                            val postRetrySync = carriage?.javaClass?.methods?.firstOrNull { method ->
                                method.name == "syncCarriage" && method.parameterCount == 0
                                    && method.returnType == java.lang.Void.TYPE
                            }
                            var postRetrySyncInvoked = false
                            if (postRetrySync != null && carriage != null) {
                                postRetrySync.invoke(carriage)
                                postRetrySyncInvoked = true
                            }
                            System.setProperty("vs2.productionNativePlacementPostRetrySyncInvoked", java.lang.Boolean.toString(postRetrySyncInvoked))
                            logger.info("GATE_D_NATIVE_PLACEMENT_POST_RETRY_SYNC carriage_id={} method_found={} invoked={} after_verified_mutation=true fixture_only=true",
                                carriageId, postRetrySync != null, postRetrySyncInvoked)
                        }
                        logger.info("GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION carriage_id={} hit_local={} empty_local={} invoked={} before_size={} after_size={} state_match={} source_identity_stable={} success={} fixture_only=true",'''

if "GATE_D_NATIVE_PLACEMENT_POST_RETRY_SYNC" not in server:
    if old not in server:
        raise SystemExit("Phase 120 could not find the unsynchronized retry-mutation success block")
    server = server.replace(old, new, 1)

required = [
    'GATE_D_NATIVE_PLACEMENT_POST_RETRY_SYNC',
    'vs2.productionNativePlacementPostRetrySyncInvoked',
    'postRetrySync.invoke(carriage)',
    'after_verified_mutation=true',
    'GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION',
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 120 lost post-retry synchronization anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
print("Phase 120: synchronizes the exact fixture carriage only after the verified retry placement mutation; harness-only")
