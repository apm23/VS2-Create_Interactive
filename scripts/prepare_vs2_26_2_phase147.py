#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Production-world #236 proved sustained real-train carry and a handled native Create
# held-block dispatch, but Phase145's re-enabled Phase111 placement site had already
# passed before the late client target/dispatch state existed. Phase114 was originally
# added specifically to retry that exact authoritative target on the recurring server
# tick path. Re-enable only that retry and only after genuine native dispatch completion.
# The client synthetic insertion remains disabled; no movement/physics/train behavior
# is changed, and success still requires Create's authoritative carriage setBlock path.
old = '''            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                    && false /* Phase137: native held-block causality probe; suppress retry fixture setBlock */) {'''
new = '''            if (java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")
                    && java.lang.Boolean.getBoolean("vs2.productionNativePlacementTargetReady")
                    && !java.lang.Boolean.getBoolean("vs2.productionNativePlacementMutationProbed")
                    && java.lang.Boolean.getBoolean("vs2.productionHeldBlockNativeDispatchCompleted") /* Phase147: recurring authoritative retry only after genuine native dispatch */) {'''
if old in server:
    server = server.replace(old, new, 1)
elif "Phase147: recurring authoritative retry only after genuine native dispatch" not in server:
    raise SystemExit("Phase 147 could not find suppressed Phase114 retry guard")

required = [
    "Phase147: recurring authoritative retry only after genuine native dispatch",
    "vs2.productionHeldBlockNativeDispatchCompleted",
    "GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION",
    "setBlock.invoke(carriage, emptyPos.immutable(), candidate)",
    "vs2.productionNativePlacementMutationSucceeded",
    "Phase137: native held-block causality probe; suppress client synthetic cell insertion",
]
# The final required token lives in GateE, not GateD; validate the server-side anchors here.
missing = [token for token in required[:-1] if token not in server]
if missing:
    raise SystemExit("Phase 147 lost authoritative retry anchors: " + ", ".join(missing))

server_probe.write_text(server, encoding="utf-8")
print("Phase 147: recurring authoritative placement retry runs only after genuine native Create dispatch; client synthetic insertion remains disabled")
