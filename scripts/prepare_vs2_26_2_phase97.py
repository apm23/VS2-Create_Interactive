#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #32 proved the synthetic hit can be assigned and restored in the
# same callback with identity preserved. Before dispatching any actual interaction,
# inventory the public runtime API exposed directly by the carriage entity. Keep this
# reflection-only: carriage is deliberately typed as vanilla Entity in this probe, so
# do not add compile-time Create calls merely for telemetry. Also pin the exact runtime
# handlePlayerInteraction seam against the already-proven synthetic block hit without
# invoking it, so the next mutation step has a concrete, signature-checked target.
anchor = '''                                                            LOGGER.info(
                                                                "GATE_F_SYNTHETIC_HIT_EPHEMERAL_ASSIGN carriage_id={} player_tick={} assigned_identity={} restored_identity={} original_type={} synthetic_type={}",
                                                                carriage.getId(), player.tickCount, assignedIdentity, restoredIdentity,
                                                                originalClientHit == null ? "null" : originalClientHit.getType(),
                                                                syntheticContraptionHit.getType());'''
replacement = anchor + '''
                                                            if (player.tickCount <= 40) {
                                                                StringBuilder interactionApi = new StringBuilder();
                                                                java.util.LinkedHashSet<String> signatures = new java.util.LinkedHashSet<>();
                                                                boolean exactHandlePlayerInteraction = false;
                                                                Object apiOwner = carriage;
                                                                for (java.lang.reflect.Method method : apiOwner.getClass().getMethods()) {
                                                                    String lower = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                    if (!(lower.contains("interact") || lower.contains("use")
                                                                            || lower.contains("block") || lower.contains("hit")
                                                                            || lower.contains("handle") || lower.contains("place")
                                                                            || lower.contains("contraption"))) continue;
                                                                    Class<?>[] params = method.getParameterTypes();
                                                                    if (method.getName().equals("handlePlayerInteraction")
                                                                            && method.getReturnType() == boolean.class
                                                                            && params.length == 4
                                                                            && params[0].getSimpleName().equals("Player")
                                                                            && params[1].getSimpleName().equals("BlockPos")
                                                                            && params[2].getSimpleName().equals("Direction")
                                                                            && params[3].getSimpleName().equals("InteractionHand")) {
                                                                        exactHandlePlayerInteraction = true;
                                                                    }
                                                                    StringBuilder sig = new StringBuilder(apiOwner.getClass().getSimpleName())
                                                                        .append('.').append(method.getName()).append('(');
                                                                    for (int pi = 0; pi < params.length; pi++) {
                                                                        if (pi > 0) sig.append(',');
                                                                        sig.append(params[pi].getSimpleName());
                                                                    }
                                                                    sig.append("):").append(method.getReturnType().getSimpleName());
                                                                    signatures.add(sig.toString());
                                                                }
                                                                for (String sig : signatures) {
                                                                    if (interactionApi.length() > 0) interactionApi.append('|');
                                                                    interactionApi.append(sig);
                                                                }
                                                                LOGGER.info(
                                                                    "GATE_F_CONTRAPTION_INTERACTION_API carriage_id={} player_tick={} methods={}",
                                                                    carriage.getId(), player.tickCount,
                                                                    interactionApi.length() == 0 ? "none" : interactionApi.toString());
                                                                LOGGER.info(
                                                                    "GATE_F_INTERACTION_DISPATCH_CANDIDATE carriage_id={} player_tick={} exact_handle_player_interaction={} target_block={} target_face={} hand=MAIN_HAND",
                                                                    carriage.getId(), player.tickCount, exactHandlePlayerInteraction,
                                                                    syntheticContraptionHit.getBlockPos(), syntheticContraptionHit.getDirection());
                                                            }'''

if "GATE_F_CONTRAPTION_INTERACTION_API" not in source:
    if anchor not in source:
        raise SystemExit("Phase 97 could not find Phase 96 ephemeral assignment anchor")
    source = source.replace(anchor, replacement, 1)
elif "GATE_F_INTERACTION_DISPATCH_CANDIDATE" not in source:
    raise SystemExit("Phase 97 found an older interaction API probe without exact dispatch-candidate telemetry")

required = [
    'GATE_F_CONTRAPTION_INTERACTION_API',
    'GATE_F_INTERACTION_DISPATCH_CANDIDATE',
    'apiOwner.getClass().getMethods()',
    'method.getName().equals("handlePlayerInteraction")',
    'params[0].getSimpleName().equals("Player")',
    'params[1].getSimpleName().equals("BlockPos")',
    'params[2].getSimpleName().equals("Direction")',
    'params[3].getSimpleName().equals("InteractionHand")',
    'syntheticContraptionHit.getBlockPos()',
    'syntheticContraptionHit.getDirection()',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 97 lost interaction dispatch-candidate anchors: " + ", ".join(missing))

for forbidden in [
    '.useItemOn(',
    '.useItem(',
    '.attack(',
    'gameMode.use',
    'method.invoke(',
    'carriage.getContraption()',
    '.handlePlayerInteraction(',
]:
    if forbidden in source:
        raise SystemExit("Phase 97 found forbidden interaction dispatch/invocation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 97: pinned exact Create handlePlayerInteraction signature and synthetic hit target via reflection-only telemetry; no invocation or mutation")
