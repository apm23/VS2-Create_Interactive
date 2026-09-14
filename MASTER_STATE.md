# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `FINAL_READY — M1 remains frozen green; bootstrap packaging regression fixed; runtime-fixed final artifact directly verified.`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (ledger/finalization-only commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- candidate_gameplay_commit: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- last_good_implementation_commit: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- runtime_packaging_fix_commit: `f3d1335c9fc89283d936af039eba34aa9778bd05`
- runtime_final_verify_workflow_commit: `7aeb188099560ad16136df0f335b361b9f519449`
- runtime_final_build_run: `34823149030` (`final-build #4`, success)
- runtime_final_verify_run: `34823564539` (`final-verify #2`, success)
- final_artifact: `VS2-Create-Interactive-M1-final` (artifact id `10339118155`)
- final_artifact_archive_digest: `sha256:88a16cf784710847fc486219de500187cae67ec414fbad6e79ebb2398521678f`
- final_jar: `valkyrienskies-26-2-2.4.205+0bc19eac8f.jar`
- final_jar_sha256: `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51`
- bootstrap_packaging: `Fabric Language Kotlin 1.13.13+kotlin.2.4.10 embedded as nested mod, including kotlin-stdlib, jdk7, jdk8, and kotlin-reflect runtime jars.`
- active_blocker: `NONE.`
- active_hypothesis: `CLOSED. The user-reproduced Bootstrap NoClassDefFoundError kotlin/jvm/internal/Intrinsics was caused by missing Kotlin runtime packaging in the previous final artifact; final-build #4 embeds and verifies the intended Fabric Language Kotlin runtime chain without modifying gameplay implementation.`
- next_safe_action: `USER RUNTIME TEST of the runtime-fixed final JAR. FINAL_READY is terminal unless direct runtime regression evidence is supplied or the user explicitly starts a new milestone.`

## Architecture contract
Forbidden unless a future explicitly reopened milestone has new direct evidence proving unavoidable:
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
Do not modify without direct regression evidence in an explicitly reopened development cycle:
- boot/no-crash gameplay baseline once dependencies are present
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

M1 GREEN is a stop signal. No gameplay tuning after this point without direct runtime regression evidence.

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

## Original finalization evidence
- final-build #1 / run `34816479606`: failed only because verifier searched grounded-Y marker in wrong generated file; CI/verifier-only.
- repair `0d7ac30555d908ead66a972cc671d5e8d441b71a`: corrected grounded-Y marker path only.
- final-build #2 / run `34816587156`: failed only because verifier searched native landing marker in wrong generated file; CI/verifier-only.
- repair `c33eaf48c1083716c5a5a0c4a7e7207286ae4890`: corrected landing-marker path only.
- final-build #3 / run `34816785467`: SUCCESS.
- final-verify #1 / run `34817198302`: SUCCESS for identity/integrity/frozen-green compiled seams.
- previous final JAR SHA-256: `3f4508b7a936467f158cc708217849c930298fa64abca8607849b19a6f10dba4`.

## Runtime bootstrap regression and repair
User runtime crash report on Minecraft 26.2 showed:
- `java.lang.NoClassDefFoundError: kotlin/jvm/internal/Intrinsics`
- first VS2 frame: `org.valkyrienskies.core.util.RateLimiter.<init>(RateLimiter.kt)`
- cause: `ClassNotFoundException: kotlin.jvm.internal.Intrinsics`
- loaded mod list contained VS2 but no Fabric Language Kotlin runtime.

Direct inspection of the previous final JAR confirmed:
- no `META-INF/jars/` runtime payload existed;
- `fabric.mod.json` did not expose a Kotlin runtime dependency;
- therefore this was a packaging/bootstrap regression, not M1 movement/collision evidence.

Repair commit `f3d1335c9fc89283d936af039eba34aa9778bd05` changed only `.github/workflows/final-build.yml` and:
- leaves the exact frozen-green M1 reconstruction unchanged;
- after `:fabric:build`, locates the exact resolved `fabric-language-kotlin` version from Gradle cache;
- verifies that nested mod is actually `fabric-language-kotlin` and itself contains `kotlin-stdlib`;
- embeds it into the final VS2 JAR under `META-INF/jars/`;
- adds the proper outer `fabric.mod.json` `jars` entry;
- verifies the embedded runtime before staging/upload;
- records `bootstrap_packaging=kotlin-runtime-embedded` in `BUILD_INFO.txt`.

Runtime-fixed final-build #4 / run `34823149030`: SUCCESS.
Artifact `10339118155` was downloaded and independently inspected:
- artifact archive digest `sha256:88a16cf784710847fc486219de500187cae67ec414fbad6e79ebb2398521678f`;
- JAR SHA-256 `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51` matches `SHA256SUMS.txt`;
- `BUILD_INFO.txt` pins source commit `f3d1335c...`, M1 proof run `34799207093`, and `bootstrap_packaging=kotlin-runtime-embedded`;
- outer JAR contains `META-INF/jars/fabric-language-kotlin-1.13.13+kotlin.2.4.10.jar`;
- nested mod id/version is `fabric-language-kotlin 1.13.13+kotlin.2.4.10`;
- nested runtime includes `kotlin-stdlib-2.4.10.jar`, `kotlin-stdlib-jdk7-2.4.10.jar`, `kotlin-stdlib-jdk8-2.4.10.jar`, and `kotlin-reflect-2.4.10.jar`.

Runtime final-verify commit `7aeb188099560ad16136df0f335b361b9f519449` changes only `.github/workflows/final-verify.yml` and directly verifies the runtime-fixed artifact.
Runtime final-verify #2 / run `34823564539`: SUCCESS.
It verifies:
- no implementation/gameplay files changed since complete M1 proof;
- exact runtime-fixed BUILD_INFO identity;
- exact JAR SHA-256 and archive integrity;
- frozen-green compiled classes/markers remain present;
- exactly one embedded Fabric Language Kotlin nested mod is present;
- Kotlin stdlib, jdk7, jdk8, and reflect nested runtime jars are present.

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
- Bootstrap/dependency failures do not authorize gameplay changes.
- FINAL_READY is terminal unless user runtime evidence directly reopens it or the user explicitly starts a new milestone.

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
- final_build_commit: `f3d1335c9fc89283d936af039eba34aa9778bd05`
- final_build_run: `34823149030`
- final_verify_commit: `7aeb188099560ad16136df0f335b361b9f519449`
- final_verify_run: `34823564539`
- final_jar: `valkyrienskies-26-2-2.4.205+0bc19eac8f.jar`
- final_jar_sha256: `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51`
- final_verification: `SUCCESS — runtime final-verify #2 / run 34823564539`
- bootstrap_runtime_fix: `SUCCESS`
- final_ready: `true`

## Finalization sequence
1. `M1_COMPLETE` — reached by #731; locked.
2. `FINAL_BUILD` — runtime-fixed artifact completed by final-build #4.
3. `FINAL_VERIFY` — runtime-fixed artifact completed by final-verify #2.
4. `FINAL_READY` — reached again after bootstrap packaging repair; terminal pending user runtime test.

## Fresh-chat protocol
1. Read this file completely.
2. Inspect actual GitHub HEAD.
3. Reconcile AUTO_RECONCILE_GIT_HEAD; ledger/finalization-only commits are not gameplay changes.
4. Respect Frozen Green, Failed Hypotheses, and Anti-loop locks.
5. If user reports Bootstrap `kotlin/jvm/internal/Intrinsics`, ensure they are testing JAR SHA-256 `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51`, not the superseded JAR SHA-256 `3f4508b7a936467f158cc708217849c930298fa64abca8607849b19a6f10dba4`.
6. If `final_ready=true` and no new runtime regression evidence exists, stop. Automation may not reopen gameplay development.
7. Only direct runtime regression evidence or an explicit user request may start a new development cycle or milestone.
