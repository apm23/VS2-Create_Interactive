# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `FINAL_VERIFY — M1 is frozen green; final distributable build #3 succeeded and artifact identity/integrity verification is next`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (ledger/finalization-only commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- candidate_gameplay_commit: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- last_good_implementation_commit: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- final_build_workflow_commit: `c33eaf48c1083716c5a5a0c4a7e7207286ae4890`
- final_build_run: `34816785467` (`final-build #3`, success)
- final_artifact: `VS2-Create-Interactive-M1-final` (artifact id `10337040684`)
- final_artifact_archive_digest: `sha256:8d882a6d0b78067010cb36d9a0700e57f738ecbee0dec0b61819b3e9c6793f5a`
- final_jar: `valkyrienskies-26-2-2.4.205+0bc19eac8f.jar`
- final_jar_sha256: `3f4508b7a936467f158cc708217849c930298fa64abca8607849b19a6f10dba4`
- active_blocker: `NONE in gameplay; FINAL_BUILD completed successfully.`
- active_hypothesis: `The uploaded final artifact is the exact frozen-green composition because BUILD_INFO pins source_commit c33eaf48... and proven_m1_run 34799207093, while c7da75d..c33eaf48 changes only MASTER_STATE.md and .github/workflows/final-build.yml.`
- next_safe_action: `Run the smallest FINAL_VERIFY proof directly against artifact 10337040684: verify archive/JAR checksums and BUILD_INFO, require JAR integrity plus the frozen-green compiled marker classes/strings, and confirm no implementation files changed since c7da75d. If green, record verification and advance to FINAL_READY. Do not rerun gameplay tuning.`

## Architecture contract
Forbidden unless new direct evidence proves unavoidable:
- fake gravity
- synthetic carry velocity
- inertia compensation
- manual wall clamp
- floor-only collision
- per-tick teleport/setPos carry workaround
- duplicate authority / duplicate world state
- workaround chains hiding Create+VS2 double ownership

Preferred order: native Create/Minecraft collision -> authoritative VS2/Create transform -> simplify duplicate ownership -> thin adapter.

## Frozen / protected green
Do not modify without direct regression evidence:
- boot/no-crash baseline
- Create train + VS2 baseline coexistence
- Steam 'n' Rails and Copycats preservation
- standing carry continuity
- forward/sprint input and supported walking proof
- native backward input/motion proof
- native right-strafe input/motion proof
- native jump request, airborne arc, natural landing, and post-land stability
- solid floor, wall, and ceiling behavior
- speed-change/frame stability
- Phase83 sibling-owner arbitration recovery
- grounded-negative-Y repair at `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- fixture floor-support bookkeeping repair at `94b920480f545845134d2e262791704489bb95d7`

M1 GREEN is a stop signal. No gameplay tuning after this point.

## Complete M1 proof
Acceptance source: `production-world-smoke #731 / run 34799207093` — success.
One real moving-train run proved:
- stable standing/carry (`carriage_id=5 ticks=26-31 samples=6`)
- supported forward locomotion + sprint
- reverse request/confirmation
- right-strafe request/confirmation
- solid floor (`floor_y_span=0`)
- solid wall (`wall_impact_span=0`)
- solid ceiling (`ceiling_gap=0.779900`)
- speed-change stability (`3.170403 -> 2.118951`, local step `0`)
- native jump, airborne arc, natural landing (`51 -> 58`, duration 7)
- replay-free/recovery-free accepted jump
- post-land stability

## Final-build evidence
- #1 / run `34816479606`: failed only because final-build verifier searched grounded-Y marker in wrong generated file; CI/verifier-only.
- repair `0d7ac30555d908ead66a972cc671d5e8d441b71a`: corrected grounded-Y marker path only.
- #2 / run `34816587156`: failed only because final-build verifier searched `GATE_E_M1_NATIVE_JUMP_LANDED` in `GateEClientProbe.java`; CI/verifier-only.
- repair `c33eaf48c1083716c5a5a0c4a7e7207286ae4890`: corrected landing-marker path to `MixinLocalPlayerFixtureInput.java`; workflow-only.
- #3 / run `34816785467`: SUCCESS. Reconstruction, Fabric build, staging/checksum, and artifact upload all completed.
- downloaded artifact contents verified locally: `SHA256SUMS.txt` matches actual JAR SHA-256; `BUILD_INFO.txt` records `source_commit=c33eaf48...` and `proven_m1_run=34799207093`.
- compare `c7da75d...c33eaf48`: only `.github/workflows/final-build.yml` and `MASTER_STATE.md` changed; no implementation/script/gameplay files changed.

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`
- generic accumulation/extension of frame leases, replay, or carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures success
- treating missing jump as a jump-input bug
- treating right-strafe timing as cause of support loss
- broad sibling/global suppression instead of direct native-owner identity
- floor-normal-only correction for #726
- near-zero total local XYZ movement as prerequisite for supported locomotion

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not patch jump admission/acceptance.
- Do not extend native contact leases.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry, fake gravity, inertia compensation, or manual floor/wall clamps.
- Do not retune Phase83 without direct regression evidence.
- Do not broaden `aea874` without renewed direct sink/regression evidence.
- Final-build/final-verify failures are not permission to modify gameplay unless the final artifact directly reproduces a frozen-green regression.

## M1 acceptance
- [x] stable standing
- [x] forward/backward/strafe
- [x] sprint
- [x] jump + airborne + natural landing
- [x] solid floor/walls/ceiling
- [x] no sink/throw/drift/lag-behind under accepted production proof
- [x] stable through movement/turn/speed changes as fixture permits

## Final artifact state
- m1_complete: `true`
- m1_proof_run: `34799207093`
- final_build_started: `true`
- final_build_commit: `c33eaf48c1083716c5a5a0c4a7e7207286ae4890`
- final_build_run: `34816785467`
- final_commit: `c33eaf48c1083716c5a5a0c4a7e7207286ae4890`
- final_jar: `valkyrienskies-26-2-2.4.205+0bc19eac8f.jar`
- final_jar_sha256: `3f4508b7a936467f158cc708217849c930298fa64abca8607849b19a6f10dba4`
- final_verification: `ACTIVE`
- final_ready: `false`

## Finalization sequence
1. `M1_COMPLETE` — reached by #731; locked.
2. `FINAL_BUILD` — completed by final-build #3.
3. `FINAL_VERIFY` — active; verify the uploaded artifact directly and frozen-green composition identity.
4. `FINAL_READY` — terminal; automation may not reopen development afterward.

## Fresh-chat protocol
1. Read this file completely.
2. Inspect actual GitHub HEAD.
3. Reconcile AUTO_RECONCILE_GIT_HEAD; ledger/finalization-only commits are not gameplay changes.
4. Respect Frozen Green, Failed Hypotheses, and Anti-loop locks.
5. If a relevant finalization workflow is queued/in_progress, HOLD; do not duplicate-trigger.
6. If FINAL_VERIFY succeeds, record evidence and advance to FINAL_READY.
7. FINAL_READY is terminal and only the user may reopen development after it.
