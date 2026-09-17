# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger; chat is temporary.

## Hard contract
- Repository: `apm23/VS2-Create_Interactive`; milestone: `M1 — movement/collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 must be the continuous moving reference-space/transform foundation for player body/render/camera through grounded, airborne, turns and speed changes; mouse/look stays free.
- Create floor/walls/ceiling remain authoritative solid geometry in that moving frame.
- Forbidden: fake gravity; synthetic carry velocity/inertia; manual floor/wall clamps; floor-only fixes; per-tick teleport/setPos chase/reanchor architecture; duplicate authority/state; direct camera forcing/counter-rotation; fake/proxy VS2 ships; workaround chains hiding double ownership.

## Current reconciliation — 2026-09-17
- Actual HEAD immediately before this ledger-only reconciliation: `61122b80e8e07416af01232e6ac290109f5bf9b2` (`Instrument ceiling contact correlation`).
- Previous workflow/media HEAD: `3f85a7871431e5725d30dcf7877ca9747ece5ded` (`Fix framebuffer video luminance validation`).
- Latest gameplay implementation remains `9aea12a6114198c33c70d52897eb9d3c29342425` (`Refresh jump owner from exact Create grounded carry contact`); commits after it are proof/workflow/ledger infrastructure, not gameplay patches.
- Active blocker: `CEILING`.
- Project state: `CAMERA_DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT; CEILING_READ_ONLY_RUNTIME_PROOF_IN_PROGRESS`.
- final_ready: `false`.
- Exact historical failed real-user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; grounded floor/walking passed, but walls soft, jump dragged player backward 2–4 carriages, turns swept player/camera, wall penetration/throw occurred, and it did not feel VS2-relative. Never ask user to retest this SHA.

## Camera — data proof is authoritative; visual audit remains non-blocking
- Exact source proof HEAD: `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`.
- Workflow/run: `m1-camera-external-reference-active-turn-retry-proof` / `35135734132` — SUCCESS.
- Artifact: id `10461944899`, `camera-external-reference-active-turn-retry-proof`, digest `sha256:69494207606455f0f6ee2f50927d397bbf49300f482ba37d4d28e85d10282fbf`.
- Classifier: `CAMERA_EXTERNAL_REFERENCE_POSITIONAL_ALIGNED_WITHIN_0_05`; owner `7`; ticks `32,42`; heading span `3.141592654 rad / 180 deg`; max/p95/median horizontal error `0`; acquisitions `18`; native contacts `25`.
- Basis: `previous_owner_to_current_owner`; `look_mutated=false`, `player_mutated=false`, `collision_mutated=false`, `gameplay_mutated=false`, `harness_semantics_unchanged=true`.
- Visual history is preserved for later user audit:
  - run `35138243767`: MP4 technically produced but black; rejected visually.
  - run `35163349899`: direct OpenGL framebuffer MP4 is visible and telemetry interval contained active owner `2`, ~54.26 deg turn, ~358 samples, max camera error ~`1.4e-14`; however assistant and user observed camera framing aimed mostly at floor/lower wall, so it is not accepted as closure visual PASS.
  - run `35166011444`: direct framebuffer/nonblack validation worked, but capture interval contained no proven active-owner turn; classification is media/observation inconclusive, not gameplay failure. Artifact id `10474552888`, `camera-visual-close`, digest `sha256:04cb6bb574625f1836ef341d3ddc1a53498fae79dbefb64efca7ed6df6355e12`.
- Current camera engineering status: `DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`. Do not reopen gameplay from media timing/framing failures. User explicitly prioritizes mod progress and permits framing cleanup later.
- Never use an older/different-build visual as proof for newer code.

## Video policy — autonomous and non-blocking
- Video is blocker-closure validation only, never a debugging/instrumentation/correction tool.
- Assistant reviews actual MP4 frames/behavior; user presence is not required. Preserve every video/review for later user audit.
- PASS => `AUTO_FROZEN_GREEN_PENDING_USER_AUDIT` and continue.
- Visible FAIL => reopen only that subsystem and continue diagnosis automatically.
- Black/unreadable/observation-missed after the narrow media repair budget => `VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`; preserve data proof and continue independent engineering. Never mutate gameplay to satisfy media.
- Later user rejection reopens the affected subsystem and requires downstream dependency reconciliation.
- Autonomous video review never substitutes for exact-final-JAR real-user runtime acceptance; `FINAL_READY` remains forbidden until that gate passes.

## Active ceiling proof
- Instrumentation commit/proof source HEAD: `61122b80e8e07416af01232e6ac290109f5bf9b2`.
- New read-only files:
  - `scripts/prepare_vs2_26_2_ceiling_contact_trace.py`
  - `.github/workflows/m1-ceiling-contact-runtime-proof.yml`
- Relevant workflow run: `35167469407`, `m1-ceiling-contact-runtime-proof`; in progress at this reconciliation.
- This proof reuses the pristine verified r0v3 carriage save (ZIP SHA256 `e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`) and the existing natural-landing native-input harness. It does not modify carriage geometry, train route/timing, player motion, collision, camera, input semantics, or gameplay state.
- Existing telemetry reused:
  - Phase65: `ContinuousOBBCollider.collideMany` tick + `surfaceCollision` + `temporalResponse` + `collisionResponse` + OBB normal/location + player pos/motion.
  - Phase66: simplified floor/overhead geometry in exact Create `worldToLocalPos` frame, including `local_feet`, `lowest_bottom_over_head`, `ceiling_head_gap`.
  - Phase75: LocalPlayer requested-vs-allowed Create `collide` response.
  - Phase76: LocalPlayer `setPos` caller chain.
- New trace only adds tick correlation to GateE local-frame state, Phase75 nonzero collide rows and Phase76 setPos rows.
- Required ceiling timeline: tick; Create local position/overhead geometry; downward OBB normal; collisionResponse; surfaceCollision; temporalResponse; requested/allowed collide; tick-bearing final Create setPos writer.
- If classifier says `CEILING_NOT_EXERCISED`, this authorizes no gameplay patch. Improve observation/selection only; do not alter collision physics or manufacture geometry.
- If ceiling contact is measured but writer correlation is incomplete, improve read-only correlation only.
- Only direct measured runtime failure at the complete ceiling timeline may authorize one gameplay hypothesis.
- No ceiling video until the ceiling blocker is data/runtime closure-ready.

## Preserved collision evidence
- Current Create collision-frame continuity through rotations: run `35100081357`; candidate-vs-Phase131 residual exactly zero; current-frame max step `0.048467738`; external owner continuous; existing EntityDragger writer runs.
- Wall/ceiling source map: run `35101691613`, artifact `10448192299`; proves current Create `worldToLocalPos` OBB path, horizontal X/Z clipping, vertical Y clipping, response setPos, surface contact-motion writer, and duplicate authority removed.
- Pinned contacts: run `35104224078`, artifact `10450080515`; seven horizontal wall rows, no ceiling row.
- Pinned wall semantics: run `35104523803`, artifact `10449412710`; all seven wall rows are valid temporal-only responses; `unresolved_zero=0`; no exact tick-bearing final Create setPos correlation was available there.
- Valid OBB rule: `surface=true + collisionResponse=ZERO + 0<temporal<1` can be solved Create behavior and is not failure by itself.
- Historical native jump: run `35089177675`, HEAD `012d92dabb86cac5571d5d320eea9fa77ea539d6`, artifact `10444135201`; native airborne tick46, rise `+0.33319999363422365`, owner7 continuous ticks46..83. Its later post-arc lifecycle failure was subsequently addressed; do not reuse it as current ceiling failure.

## FROZEN / protected evidence
Preserve unless directly regressed:
- bootstrap/Kotlin packaging `f3d1335...`
- Create train + VS2 coexistence
- Steam 'n' Rails + Copycats
- V1 infra `34984299770`
- external-owner lifecycle requirement `35008163064`
- same-point transform `35023234306`
- free-look structural boundary `35034983734`
- OBB temporal-only support-loss `35041914462`
- native drag gate `35045444238`
- existing VS2 body writer `35048234680`
- ordinary descent support-miss lifecycle `35051781646`
- owner-cap lag `35071088843`
- fixture arbitration `35084762923`, `35085286003`
- current Create collision-frame continuity `35100081357`
- pinned wall temporal-only semantics `35104523803`
- camera external-owner gate reachability after alignWithEntity `35113644070`
- historical user floor solidity + grounded walking
- camera active-turn data proof `35135734132` (data-proven; visual audit still pending/inconclusive, not user-final).

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`
- generic frame lease/replay/carry extension
- lifecycle extension beyond proven jump/landing seam
- synthetic carry velocity/inertia; fake gravity
- manual floor/wall clamp or floor-only workaround
- per-tick teleport/setPos chase/reanchor
- direct camera forcing/counter-rotation
- jump/input timing tuning as production fix
- sprint/reverse/strafe tuning as reference-frame fix
- unscoped/global collider suppression
- suppressing Create collision-response writer
- duplicate Create/VS2 authority
- fake/proxy VS2 ship
- harness mutation to manufacture green
- blind resolver prev/current/yaw/point changes after proof
- interpreting old `toLocalVector(...,0)` mismatch as current failure
- interpreting temporal-only zero response as failure
- patching `isDraggable` / `vs$shouldDrag`
- adding/replacing body-position writer
- Phase64 grounding/Y clip merely from location knowledge
- hardcoded carriage id/block count/span/geometry
- changing server `firstOrNull` initial fixture selector
- counting post-release hypothetical camera rows as active camera mismatch
- adding camera counter-rotation after exact active-turn alignment proof.

## next_safe_action
1. Inspect only run `35167469407` first. While queued/in_progress, HOLD; do not stack a gameplay patch.
2. If SUCCESS, read `m1-ceiling-contact-proof.txt` / job log and classify:
   - `CEILING_NOT_EXERCISED` => no gameplay patch; smallest observation/selection follow-up using existing real carriage geometry only.
   - `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE` => narrow read-only correlation follow-up only.
   - `CEILING_CONTACT_CORRELATED` => inspect exact tick timeline before deciding whether Create clips correctly or a direct measured failure exists.
3. If workflow fails in compose/compile/harness/verifier, treat as proof-infra failure only; repair proof infra, not gameplay physics.
4. Never patch walls from the already-proven temporal-only rows.
5. No video for ceiling until data/runtime closure-ready.
6. Regression of protected/FROZEN evidence => REVERT before workaround.
7. CI alone never permits `FINAL_READY`; exact final JAR must pass real-user Minecraft acceptance: no sinking, stable standing, forward/back/strafe/sprint, jump+natural landing, floor/wall/ceiling solidity, and train movement/speed-change stability.
