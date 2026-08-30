#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
server = server_probe.read_text(encoding="utf-8")

# Phase 117 runs after Phase 114 and patches the first verified placement-success block.
# In the final generated Gate D source that first block is the retry mutation itself.
# Production-world #111 confirmed the ordering: setBlock succeeded, then
# GATE_D_NATIVE_PLACEMENT_CREATE_SYNC logged, then the retry-mutation summary logged.
# The previous Phase 120 incorrectly assumed that log ordering meant sync happened before
# the mutation and searched for an unsynchronized copy of the success block, aborting the
# prepare step. Validate the already-installed Create-owned sync instead of duplicating it.
retry_marker = 'GATE_D_NATIVE_PLACEMENT_RETRY_MUTATION'
sync_marker = 'GATE_D_NATIVE_PLACEMENT_CREATE_SYNC'
mutation_call = 'setBlock.invoke(carriage, emptyPos.immutable(), candidate)'
sync_call = 'syncCarriage.invoke(carriage)'

retry_index = server.find(retry_marker)
sync_index = server.rfind(sync_marker, 0, retry_index) if retry_index >= 0 else -1
mutation_index = server.rfind(mutation_call, 0, retry_index) if retry_index >= 0 else -1
sync_call_index = server.rfind(sync_call, 0, retry_index) if retry_index >= 0 else -1

if retry_index < 0:
    raise SystemExit("Phase 120 lost retry-mutation marker")
if min(sync_index, mutation_index, sync_call_index) < 0:
    raise SystemExit("Phase 120 could not verify the existing retry placement synchronization")
if not (mutation_index < sync_call_index < sync_index < retry_index):
    raise SystemExit("Phase 120 found unexpected retry placement synchronization ordering")
if retry_index - mutation_index > 5000:
    raise SystemExit("Phase 120 retry placement synchronization is not structurally local to the mutation")

print("Phase 120: verified Phase 117 already synchronizes the exact fixture carriage after retry setBlock; no duplicate sync or gameplay mutation")

# Production-world #114 still observes the authoritative server mutation but no block in
# the exact client carriage. Scan sibling client contraptions read-only before touching
# Create networking, so a wrong-entity observer can be separated from missing replication.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase121.py")), run_name="__main__")
