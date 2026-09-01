#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
server_probe = ROOT / "fabric/src/main/kotlin/org/valkyrienskies/mod/fabric/common/GateDProbe.kt"
source = client_probe.read_text(encoding="utf-8")

# Phase 86 separated fixture behavior from the carry compatibility path, but its
# ciHarness switch still implicitly treated every GitHub Actions JVM as a fixture
# run. Preserve existing CI behavior for regression stability while adding an
# explicit production-smoke escape hatch. A runner launched with
# -Dvs2.productionSmoke=true can now exercise ci_harness=false even inside Actions.
old = '''        boolean ciHarness = Boolean.getBoolean("vs2.gateD") || "true".equals(System.getenv("GITHUB_ACTIONS"));'''
new = '''        boolean productionSmoke = Boolean.getBoolean("vs2.productionSmoke");
        boolean productionSmokeFixture = Boolean.getBoolean("vs2.productionSmokeFixture");
        boolean ciHarness = Boolean.getBoolean("vs2.gateD") || ("true".equals(System.getenv("GITHUB_ACTIONS")) && !productionSmoke);'''
if new not in source:
    if old not in source:
        raise SystemExit("Phase 87 could not find Phase 86 ciHarness switch")
    source = source.replace(old, new, 1)

required = [
    'boolean explicitCarryCompat = Boolean.getBoolean("vs2.createCarryCompat")',
    'VS2_CREATE_CARRY_COMPAT_MODE ci_harness={} explicit_opt_in={}',
    'if (ciHarness && !fixtureClientNormalized',
    'if (ciHarness && !fixtureColliderNormalized',
    'GATE_E_PHASE85_CARRY_REPLAY',
    'vs2.productionSmoke',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 87 lost production/harness isolation anchors: " + ", ".join(missing))

# Production-world runs 5-9 showed that trying to pre-seed the dev player's save
# profile from outside Minecraft is brittle: the archived world has no playerdata,
# the development username is ephemeral, and CI cannot reliably force a normal
# client shutdown. Keep production compatibility itself at ci_harness=false, but
# allow an independently named test-only fixture switch to reuse the already-proven
# carriage normalization path. This only establishes initial test contact; it does
# not enable the carry compatibility path by itself.
source = source.replace(
    'if (ciHarness && !fixtureClientNormalized',
    'if ((ciHarness || productionSmokeFixture) && !fixtureClientNormalized',
    1,
)
source = source.replace(
    'if (ciHarness && !fixtureColliderNormalized',
    'if ((ciHarness || productionSmokeFixture) && !fixtureColliderNormalized',
    1,
)

# Phase 83 retires the legacy LocalPlayer replay before Phase 87 runs. Only the
# remaining native-contact compatibility guard is widened for explicit production
# opt-in. Phase 83 now names its supported-or-airborne native carriage membership
# predicate phase83NativeFrameEligible; keep that native predicate intact here.
old_carry_guard = '''            if (carryBaselineCaptured
                && phase83NativeFrameEligible'''
new_carry_guard = '''            if ((carryBaselineCaptured || explicitCarryCompat)
                && phase83NativeFrameEligible'''
carry_guard_count = source.count(old_carry_guard)
if carry_guard_count < 1:
    raise SystemExit(f"Phase 87 expected the remaining native-contact production guard, found {carry_guard_count}")
source = source.replace(old_carry_guard, new_carry_guard, 1)

# Production-world run 3 still emitted no Phase 85 replay marker. The old Phase 81
# support-continuity telemetry itself was also hidden behind carryBaselineCaptured,
# so the failed run could not tell whether strict physical support, collision
# eligibility, or broadphase overlap was the blocker. Expose at most 40 samples
# whenever explicit production compatibility is enabled. This is read-only
# telemetry; no position, velocity, contact lease, train control, or collision
# response is changed.
old_support_log = '''            if (carryBaselineCaptured && carryReplayGuardSamples <= 40) {
                LOGGER.info('''
new_support_log = '''            if ((carryBaselineCaptured || explicitCarryCompat) && carryReplayGuardSamples < 40) {
                carryReplayGuardSamples++;
                LOGGER.info('''
if old_support_log not in source:
    raise SystemExit("Phase 87 could not find Phase 81 support-continuity telemetry guard")
source = source.replace(old_support_log, new_support_log, 1)

production_required = [
    '(carryBaselineCaptured || explicitCarryCompat)',
    'phase83NativeFrameEligible',
    'phase81PhysicalSupport',
    'collisionEligible',
    'broadphaseOverlap',
    'GATE_E_PHASE85_CARRY_REPLAY',
    'GATE_E_PHASE81_SUPPORT_CONTINUITY',
    'productionSmokeFixture',
]
production_missing = [token for token in production_required if token not in source]
if production_missing:
    raise SystemExit("Phase 87 lost strict production carry anchors: " + ", ".join(production_missing))

# Sustained production-world smoke now proves repeated Create-filtered carry. Before
# attempting any use/place mutation on an assembled moving train, observe what the
# vanilla client is actually targeting during those successful carry ticks. This is
# deliberately read-only: it only records concrete HitResult geometry and does not
# call gameMode/useItemOn, alter inventory, place blocks, or touch contraption state.
interaction_anchor = '''                                LOGGER.info(
                                    "GATE_E_PHASE85_CARRY_REPLAY carriage_id={} requested={},{},{} allowed={},{},{} before={},{},{} after={},{},{}",
                                    carriage.getId(),
                                    contactMotion.x, contactMotion.y, contactMotion.z,
                                    allowedMovement.x, allowedMovement.y, allowedMovement.z,
                                    beforeX, beforeY, beforeZ,
                                    player.getX(), player.getY(), player.getZ());'''
interaction_replacement = interaction_anchor + '''
                                if (productionSmoke && explicitCarryCompat && client.hitResult != null) {
                                    net.minecraft.world.phys.HitResult interactionHit = client.hitResult;
                                    String interactionDetail = "generic";
                                    if (interactionHit instanceof net.minecraft.world.phys.BlockHitResult blockHit) {
                                        interactionDetail = "block_pos=" + blockHit.getBlockPos().toShortString()
                                            + ";direction=" + blockHit.getDirection()
                                            + ";inside=" + blockHit.isInside();
                                    }
                                    Vec3 hitLocation = interactionHit.getLocation();
                                    LOGGER.info(
                                        "GATE_F_INTERACTION_TARGET carriage_id={} player_tick={} hit_type={} hit_location={},{},{} detail={}",
                                        carriage.getId(), player.tickCount, interactionHit.getType(),
                                        hitLocation.x, hitLocation.y, hitLocation.z, interactionDetail);
                                }'''
if "GATE_F_INTERACTION_TARGET" not in source:
    if interaction_anchor not in source:
        raise SystemExit("Phase 87 could not find Phase 85 replay logger for interaction targeting")
    source = source.replace(interaction_anchor, interaction_replacement, 1)

if "hit_location={},{},{} detail={}" not in source:
    raise SystemExit("Phase 87 failed to install concrete interaction-target geometry telemetry")

client_probe.write_text(source, encoding="utf-8")

# Server-side Gate D normalization is also test-only. Production smoke keeps the
# production carry mode boundary (ci_harness=false), while productionSmokeFixture
# may opt into the one-shot contact setup when the workflow needs deterministic
# initial support. Normal users never set this property.
server = server_probe.read_text(encoding="utf-8")
old_server_guard = '''            if (!fixturePlayerChecked) {'''
new_server_guard = '''            if ((!java.lang.Boolean.getBoolean("vs2.productionSmoke") || java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")) && !fixturePlayerChecked) {'''
if new_server_guard not in server:
    if old_server_guard not in server:
        raise SystemExit("Phase 87 could not find Gate D fixture normalization guard")
    server = server.replace(old_server_guard, new_server_guard, 1)

server_required = [
    'java.lang.Boolean.getBoolean("vs2.productionSmoke")',
    'java.lang.Boolean.getBoolean("vs2.productionSmokeFixture")',
    'GATE_D_FIXTURE_PLAYER_REPOSITIONED',
    'gravity_probe_y=-0.08',
]
server_missing = [token for token in server_required if token not in server]
if server_missing:
    raise SystemExit("Phase 87 lost server fixture isolation anchors: " + ", ".join(server_missing))
server_probe.write_text(server, encoding="utf-8")

print("Phase 87: production isolation plus explicit test-only support fixture, bounded carry telemetry, and concrete read-only interaction targeting")
