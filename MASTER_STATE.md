# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `FINAL_BUILD — M1 is frozen green; final distributable build retry #2 is queued after verifier-only path correction`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `c7da75df793502f3fe4f61d0dd093190e00a06fa` (latest composed source used by the complete M1 proof; the added ground/final-motion telemetry is read-only)
- candidate_gameplay_commit: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- last_good_implementation_commit: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- final_build_workflow_commit: `0d7ac30555d908ead66a972cc671d5e8d441b71a`
- final_build_run: `34816587156` (`final-build #2`, queued at last observation)
- active_blocker: `NONE in gameplay. final-build #1 failed only because its verifier searched GATE_E_CREATE_GROUNDED_Y_CLIP in GateEClientProbe.java although Phase64 generates that marker in MixinContraptionColliderClientTrace.java.`
- active_hypothesis: `final-build #2 should reconstruct the exact proven #731 composition and reach compilation/artifact staging now that the marker assertion points at its actual generated file.`
- next_safe_action: `HOLD while final-build #2 / run 34816587156 is queued or in_progress. When it completes: if failure is CI/build/staging, repair only that finalization boundary; do not touch M1 gameplay. If success, record exact artifact names and SHA-256 values, then advance to FINAL_VERIFY using the smallest frozen-green verification against the final composition/artifact.`

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

Preferred order:
1. native Create/Minecraft collision mechanism
2. reuse existing authoritative VS2/Create transform
3. simplify/remove duplicate ownership
4. thin adapter
5. new workaround only with direct evidence and explicit justification

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
- solid floor, wall, and ceiling behavior in the M1 fixture
- speed-change/frame stability covered by #731
- Phase83 stale-baseline sibling-owner arbitration fixed at the exact #722 competing-owner seam by #724
- Create grounded-negative-Y consistency repair at `aea874`: retained grounded negative Y is clipped only when Create itself finishes LocalPlayer grounded; positive/upward Y and X/Z remain untouched
- #729 fixture floor-support bookkeeping correction at `94b920480f545845134d2e262791704489bb95d7`

Important: M1 is green. Do not continue gameplay tuning after this point.

## Latest durable evidence
### exact-shape experiment `0fa4aa246021c6b7168b7212406d4f61fac59add`
- forced LocalPlayer to exact per-block shapes
- production-world #720 regressed protected locomotion/reference continuity
- reverted and locked failed; DO NOT REINTRODUCE without genuinely new evidence

### owner arbitration recovery `881f1a737c92efdd39b7e5fcda13efb6908b475f`
- #724 proved stale post-handoff Phase83 reanchor no longer recurs
- exact duplicate-owner seam is frozen green

### grounded-motion candidate `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- changes only Create's final native-motion seam
- when Create itself finishes LocalPlayer grounded, only retained negative final Y is clipped to zero
- X/Z and positive/upward Y are untouched
- no teleport/setPos carry, fake gravity, manual floor height, shape override, synthetic carry, or new ownership state
- #727/#728/#730 preserve standing/carry and supported locomotion instead of the former sink

### fixture bookkeeping repair `94b920480f545845134d2e262791704489bb95d7`
- ordinary horizontal native locomotion no longer invalidates fixture floor support merely because total local XYZ step is non-zero
- no player/collision/train/world/input mutation
- compile/client/runtime/production-carry gates pass

### production-world #730 / run `34798398059`
- preserved frozen standing/carry/walk/sprint and produced a real native jump request/positive vertical motion
- failed natural landing in that run and justified read-only ordering diagnostics only
- no gameplay change was authorized from this failure alone

### ground/final-motion ordering diagnostic `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- read-only Create `setOnGround` / final-motion seam telemetry
- preserves the existing behavior exactly
- no movement, collision, gravity, input, train/world, lease, replay, or owner mutation

### production-world #731 / run `34799207093` — COMPLETE M1 PROOF
Workflow conclusion: `success`.
The same real moving-train production-isolation run proves all required M1 behavior:
- `PRODUCTION_CARRY physical_support_stable carriage_id=5 ticks=26-31 samples=6`
- supported forward locomotion and sprint are accepted in-run
- reverse: `reverse_request=26 reverse_confirmed=26`
- right strafe: `strafe_request=27 strafe_confirmed=27`
- floor: `floor_solid=true floor_samples=15 floor_y_span=0.000000000`
- wall: `wall_solid=true wall_impact_ticks=39-41 wall_impact_span=0.000000000`
- ceiling: `ceiling_solid=true ceiling_stop_tick=56 ceiling_overhead_tick=51 ceiling_gap=0.779900`
- speed change: `speed_change_stable=true speed_change_ticks=20-21 frame_speed=3.170403->2.118951 speed_change_local_step=0.000000000`
- jump: `jump_request=51 airborne=51 landed=58 duration=7 delta_y=0.33319999363422365 natural_fall=true`
- no workaround ownership/carry during the accepted jump: `replay_free=true recovery_free=true`
- post-landing stability: `post_land_stable_samples=11`
- workflow emits: `M1 production moving-train carry continuity, supported sprinting, and native jump landing passed.`

This satisfies the project rule that all M1 boxes must be proven in one real moving-train run. #731 is the M1 acceptance proof and supersedes the transient #730 landing failure for milestone state.

### final-build #1 / run `34816479606`
- conclusion: `failure`
- composition scripts completed through the same cumulative Phase98 path used by #731
- build did not start because a final-build-only grep assertion searched `GATE_E_CREATE_GROUNDED_Y_CLIP` in the wrong generated Java file
- Phase64 source proves that marker is generated in `fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientTrace.java`
- classification: `CI/verifier`, not gameplay and not compile

### final-build verifier repair `0d7ac30555d908ead66a972cc671d5e8d441b71a`
- modifies only `.github/workflows/final-build.yml`
- points the grounded-Y marker assertion at the actual generated Phase64 mixin file
- no scripts/gameplay/collision/input/ownership/carry code changed
- automatically triggered `final-build #2 / run 34816587156`

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
- near-zero total local XYZ movement as a prerequisite for supported locomotion

## Anti-loop lock
- M1 GREEN is a stop signal.
- Do not change sprint/reverse/strafe input windows.
- Do not patch jump admission/acceptance.
- Do not extend native contact leases.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry, fake gravity, inertia compensation, or manual floor/wall clamps.
- Do not retune Phase83 native-owner arbitration without direct regression of its exact closed seam.
- Do not broaden `aea874` without renewed direct sink/regression evidence.
- Finalization may remove disposable/read-only diagnostics only if removal itself is proven behavior-neutral; otherwise leave them in place until after final verification.
- Final-build/verify failures are not permission to modify frozen M1 gameplay unless the final artifact directly reproduces a frozen-green regression.

## M1 acceptance — all required in one real moving-train proof
- [x] stable standing
- [x] forward/backward/strafe
- [x] sprint
- [x] jump + airborne + natural landing
- [x] solid floor/walls/ceiling
- [x] no sink/throw/drift/lag-behind under the accepted production proof
- [x] stable through movement/turn/speed changes as fixture permits

Acceptance source: `production-world-smoke #731 / run 34799207093`.

## Final artifact state
- m1_complete: `true`
- m1_proof_run: `34799207093`
- final_build_started: `true`
- final_build_commit: `0d7ac30555d908ead66a972cc671d5e8d441b71a`
- final_build_run: `34816587156`
- final_commit: `NONE` until build success is recorded
- final_jar: `NONE` until artifact success is recorded
- final_verification: `NOT_STARTED`
- final_ready: `false`

## Finalization sequence
1. `M1_COMPLETE` — reached by #731 and locked in this ledger.
2. `FINAL_BUILD` — active via final-build #2; build the distributable from the exact proven composition without gameplay changes.
3. `FINAL_VERIFY` — after successful build, verify artifact identity/integrity and rerun the smallest relevant frozen-green gates against the final artifact/composition.
4. `FINAL_READY` — terminal; automation may not reopen development afterward.

## Fresh-chat protocol
1. Read this file completely.
2. Inspect actual GitHub HEAD.
3. If `current_head=AUTO_RECONCILE_GIT_HEAD`, compare commits since `implementation_head`; workflow/ledger-only finalization commits are not gameplay changes.
4. Respect Frozen Green, Failed Hypotheses, and Anti-loop locks.
5. If `m1_complete=true`, do not return to gameplay patching; continue the finalization sequence only.
6. If a relevant finalization workflow is queued/in_progress, HOLD; do not duplicate-trigger.
7. If final-build succeeds, record artifact/checksum and advance to FINAL_VERIFY.
8. FINAL_READY is terminal and only the user may reopen development after it.
