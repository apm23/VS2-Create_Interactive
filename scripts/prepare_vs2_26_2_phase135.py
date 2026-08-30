#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server = server_probe.read_text(encoding="utf-8")
client = client_probe.read_text(encoding="utf-8")

# Production-world + held-block gate now independently prove all three prerequisites:
# sustained moving-train carry, handled native Create right-click with a held STONE block,
# and authoritative new-cell replication. The remaining gap is causality: previous smoke
# still had direct server-fixture setBlock fallbacks (Phase111/114) and a client-map insertion
# hypothesis (Phase125), so replication could pass without the held-block dispatch creating it.
# Disable only those disposable-fixture shortcuts in the final prepared smoke source.
# Normal gameplay, Create/VS2 physics, train controls, world saves, and production compat
# packet handling are untouched. If the native dispatch cannot place, the existing production
# placement gate will fail with the real next blocker instead of being masked by a fixture.

phase111_old = '''                                if (candidateReady
                                        && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")) {'''
phase111_new = '''                                if (candidateReady
                                        && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                                        && false /* Phase137: native held-block causality probe; suppress direct fixture setBlock */) {'''
if phase111_old not in server and "Phase137: native held-block causality probe; suppress direct fixture setBlock" not in server:
    raise SystemExit("Phase 135 could not locate Phase111 direct placement guard")
server = server.replace(phase111_old, phase111_new, 1)

phase114_old = '''            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")) {'''
phase114_new = '''            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                    && false /* Phase137: native held-block causality probe; suppress retry fixture setBlock */) {'''
if phase114_old not in server and "Phase137: native held-block causality probe; suppress retry fixture setBlock" not in server:
    raise SystemExit("Phase 135 could not locate Phase114 retry placement guard")
server = server.replace(phase114_old, phase114_new, 1)

phase125_old = '''                                if (exactEntry == null
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementClientInsertHypothesisApplied")) {'''
phase125_new = '''                                if (exactEntry == null
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementClientInsertHypothesisApplied")
                                        && false /* Phase137: native held-block causality probe; suppress client synthetic cell insertion */) {'''
if phase125_old not in client and "Phase137: native held-block causality probe; suppress client synthetic cell insertion" not in client:
    raise SystemExit("Phase 135 could not locate Phase125 client insertion guard")
client = client.replace(phase125_old, phase125_new, 1)

required_server = [
    "Phase137: native held-block causality probe; suppress direct fixture setBlock",
    "Phase137: native held-block causality probe; suppress retry fixture setBlock",
    "setBlockMethod.invoke(nativeCarriage, emptyPos.immutable(), placementCandidate)",
    "setBlock.invoke(carriage, emptyPos.immutable(), candidate)",
]
required_client = [
    "Phase137: native held-block causality probe; suppress client synthetic cell insertion",
    "GATE_F_PHASE136_HELD_BLOCK_NATIVE_MULTI_ANCHOR",
    "writableExactMap.put(exactPos, inserted)",
]
missing = [token for token in required_server if token not in server] + [token for token in required_client if token not in client]
if missing:
    raise SystemExit("Phase 135 lost native-placement causality anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
client_probe.write_text(client, encoding="utf-8")
print("Phase 135: disabled direct server placement and client synthetic-cell fixture shortcuts so moving-cell sync must originate from held-block native Create dispatch")
