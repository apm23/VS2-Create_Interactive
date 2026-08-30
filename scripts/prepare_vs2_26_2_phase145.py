#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #232 proved the actual Create helper consumes a valid contraption ray
# with authoritative STONE, but Create's own source only sends ContraptionInteractionPacket
# when AbstractContraptionEntity.handlePlayerInteraction(...) returns true. Generic held-block
# placement is not part of that interaction path, so no C2S packet is emitted for this target.
# Re-enable only the already-validated disposable-fixture authoritative setBlock proof, and
# only after the genuine native helper dispatch has completed. This preserves causality and
# tests the server-authoritative moving-cell + replication path without changing movement,
# collision, train state, or normal gameplay. The retry and client synthetic insertion remain
# disabled, so a success still requires the authoritative server carriage mutation path.
old = '''                                if (candidateReady
                                        && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                                        && false /* Phase137: native held-block causality probe; suppress direct fixture setBlock */) {'''
new = '''                                if (candidateReady
                                        && java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                                        && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                                        && java.lang.Boolean.getBoolean("vs2.productionHeldBlockNativeDispatchCompleted") /* Phase145: authoritative placement proof only after genuine native dispatch */) {'''
if old in server:
    server = server.replace(old, new, 1)
elif "Phase145: authoritative placement proof only after genuine native dispatch" not in server:
    raise SystemExit("Phase 145 could not find suppressed Phase111 placement guard")

required = [
    "Phase145: authoritative placement proof only after genuine native dispatch",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "setBlockMethod.invoke(nativeCarriage, emptyPos.immutable(), placementCandidate)",
    "Phase137: native held-block causality probe; suppress retry fixture setBlock",
]
missing = [token for token in required if token not in server]
if missing:
    raise SystemExit("Phase 145 lost authoritative placement anchors: " + ", ".join(missing))

# Keep this strictly fixture-side: do not add player/train/physics mutation or bypass the
# existing native-dispatch prerequisite.
server_probe.write_text(server, encoding="utf-8")
print("Phase 145: authoritative fixture placement proof runs only after genuine native Create dispatch; retry/client shortcuts stay disabled")
