# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; compatibility stays a thin adapter.

## Current state
- project_state: `RUNTIME_REGRESSION — FINAL_READY REVOKED. Direct user runtime test of the runtime-fixed final JAR shows the player sinking through the Create carriage floor.`
- current_head: `AUTO_RECONCILE_GIT_HEAD`
- implementation_head_under_test: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- candidate_gameplay_commit: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- previous_automated_m1_proof_run: `34799207093` (`production-world-smoke #731`, automated GREEN but now insufficient for real-user acceptance)
- runtime_packaging_fix_commit: `f3d1335c9fc89283d936af039eba34aa9778bd05`
- runtime_final_verify_workflow_commit: `7aeb188099560ad16136df0f335b361b9f519449`
- runtime_final_build_run: `34823149030` (`final-build #4`, success)
- runtime_final_verify_run: `34823564539` (`final-verify #2`, success)
- tested_final_jar_sha256: `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51`
- bootstrap_runtime_fix: `SUCCESS — Kotlin packaging issue fixed; client now reaches Minecraft/world.`
- user_runtime_validation: `FAILED`
- final_ready: `false`
- active_blocker: `G. collision — direct real-user runtime evidence shows carriage floor/support is not solid for the player; player visibly sinks into/below the moving carriage despite automated harness GREEN.`
- active_hypothesis: `The automated production-world fixture/proof does not faithfully reproduce the real user's carriage-floor collision/support boundary, so its floor/carry GREEN was a false positive for final acceptance.`
- next_safe_action: `Reproduce the real-user sinking condition with the exact runtime artifact/environment and add the smallest read-only instrumentation at the native Create/VS2 floor-support/collision boundary. Do not retune unrelated movement inputs or re-finalize from CI alone.`

## Direct user runtime regression — 2026-09-14
The user tested the runtime-fixed final JAR in actual Minecraft 26.2 and supplied a screenshot showing the player sunk into/below the assembled Create carriage floor. This is direct runtime evidence and overrides automated GREEN for the affected M1 criteria.

Consequences:
- previous `FINAL_READY` is invalid and revoked;
- stable standing is REGRESSED/UNPROVEN in real user runtime;
- solid floor is REGRESSED/UNPROVEN in real user runtime;
- no-sink acceptance is REGRESSED/UNPROVEN in real user runtime;
- automated run #731 remains useful harness evidence but is NOT final acceptance evidence;
- bootstrap/Kotlin packaging repair remains valid and should not be reverted;
- do not claim M1_COMPLETE/FINAL_READY again until the exact final candidate passes a fresh real-user runtime test.

## Architecture contract
Forbidden unless direct evidence proves unavoidable:
- fake gravity
- synthetic carry velocity
- inertia compensation
- manual wall clamp
- floor-only collision workaround
- per-tick teleport/setPos carry
- duplicate authority/state
- workaround chains hiding Create+VS2 double ownership

Preferred order: native Create/Minecraft collision -> authoritative VS2/Create transform -> simplify duplicate ownership -> thin adapter.

## Still protected / frozen unless direct regression evidence exists
- bootstrap/no-crash with embedded Kotlin runtime
- Create train + VS2 coexistence
- Steam 'n' Rails and Copycats preservation
- backward/strafe/sprint/jump code paths unless direct runtime evidence shows they are independently broken
- Phase83 sibling-owner arbitration seam unless direct evidence points there
- packaging fix from `f3d1335c9fc89283d936af039eba34aa9778bd05`

## Reopened / not frozen
- stable standing on moving carriage
- carriage floor solidity/support
- no sink / no downward penetration
- carry continuity insofar as it depends on the failed floor/support boundary

## Previous automated proof — retained as non-terminal evidence
`production-world-smoke #731 / run 34799207093` reported:
- stable standing/carry
- forward/sprint
- reverse
- right strafe
- floor/wall/ceiling solidity
- speed-change stability
- jump/airborne/natural landing
- post-land stability

This proof is now classified as `HARNESS_GREEN_BUT_USER_RUNTIME_FALSE_POSITIVE` for final acceptance because direct user runtime contradicts standing/floor/no-sink behavior.

## Bootstrap packaging regression and repair
The first final artifact crashed with `NoClassDefFoundError: kotlin/jvm/internal/Intrinsics` because Kotlin runtime was missing. Repair `f3d1335c9fc89283d936af039eba34aa9778bd05` changed only final packaging and embedded Fabric Language Kotlin plus Kotlin stdlib/jdk7/jdk8/reflect. `final-build #4 / 34823149030` and `final-verify #2 / 34823564539` succeeded. The client now launches; this packaging fix is GREEN and unrelated to the sinking gameplay regression.

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
- Do not tune sprint/reverse/strafe windows merely because floor support fails.
- Do not patch jump admission/acceptance without jump-specific evidence.
- Do not extend native contact leases speculatively.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry/fake gravity/inertia/manual clamps.
- Do not treat CI/harness GREEN as real-user acceptance.
- A verifier/build success never authorizes `FINAL_READY` by itself.

## M1 acceptance — REAL USER RUNTIME is authoritative for terminal completion
- [ ] stable standing — REOPENED, user runtime FAIL
- [ ] forward/backward/strafe — must be rechecked after floor/support fix
- [ ] sprint — must be rechecked after floor/support fix
- [ ] jump + airborne + natural landing — must be rechecked after floor/support fix
- [ ] solid floor/walls/ceiling — FLOOR FAIL; wall/ceiling need recheck on corrected candidate
- [ ] no sink/throw/drift/lag-behind — SINK FAIL
- [ ] stable through movement/turn/speed changes — recheck after support fix

## Final artifact state
- m1_complete: `false`
- final_build_candidate_exists: `true`
- tested_candidate_sha256: `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51`
- artifact_integrity_verification: `SUCCESS`
- bootstrap_runtime_fix: `SUCCESS`
- user_runtime_validation: `FAILED`
- final_ready: `false`

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can advance a candidate through build/integrity verification, but terminal completion requires a real user test of the exact final JAR.

`FINAL_READY` is allowed only when ALL are true:
1. final candidate built successfully;
2. artifact identity/integrity checks pass;
3. no implementation regression is known;
4. the user tests the exact candidate in real Minecraft and confirms all M1 criteria;
5. watchdog local `USER_RUNTIME_GREEN.txt` is bound to the exact `final_jar_sha256` of that candidate.

If ChatGPT/CI says FINAL_READY without condition 4+5, watchdog must reject the terminal decision and HOLD for user runtime validation.

## Fresh-chat protocol
1. Read this file completely.
2. Inspect actual GitHub HEAD.
3. Treat the 2026-09-14 user screenshot as direct regression evidence: player sinks through carriage floor.
4. Do NOT restore FINAL_READY from old run #731 or final-verify #2.
5. Keep Kotlin/bootstrap packaging fix protected.
6. Diagnose the collision/support boundary with smallest read-only proof first.
7. Only re-freeze standing/floor/no-sink after a new exact-candidate real-user runtime pass.
8. Never terminal-finalize from CI alone; require exact-JAR user runtime confirmation gate.
