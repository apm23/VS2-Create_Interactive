#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #32 proved the synthetic hit can be assigned and restored in the
# same callback with identity preserved. Before dispatching any actual interaction,
# inventory the public Create carriage/contraption APIs that look interaction-related.
# This is reflection-only telemetry: no method is invoked and no state is mutated.
anchor = '''                                                            LOGGER.info(
                                                                "GATE_F_SYNTHETIC_HIT_EPHEMERAL_ASSIGN carriage_id={} player_tick={} assigned_identity={} restored_identity={} original_type={} synthetic_type={}",
                                                                carriage.getId(), player.tickCount, assignedIdentity, restoredIdentity,
                                                                originalClientHit == null ? "null" : originalClientHit.getType(),
                                                                syntheticContraptionHit.getType());'''
replacement = anchor + '''
                                                            if (player.tickCount <= 40) {
                                                                StringBuilder interactionApi = new StringBuilder();
                                                                java.util.LinkedHashSet<String> signatures = new java.util.LinkedHashSet<>();
                                                                Object[] apiOwners = new Object[] { carriage, carriage.getContraption() };
                                                                for (Object apiOwner : apiOwners) {
                                                                    if (apiOwner == null) continue;
                                                                    for (java.lang.reflect.Method method : apiOwner.getClass().getMethods()) {
                                                                        String lower = method.getName().toLowerCase(java.util.Locale.ROOT);
                                                                        if (!(lower.contains("interact") || lower.contains("use")
                                                                                || lower.contains("block") || lower.contains("hit")
                                                                                || lower.contains("handle") || lower.contains("place"))) continue;
                                                                        StringBuilder sig = new StringBuilder(apiOwner.getClass().getSimpleName())
                                                                            .append('.').append(method.getName()).append('(');
                                                                        Class<?>[] params = method.getParameterTypes();
                                                                        for (int pi = 0; pi < params.length; pi++) {
                                                                            if (pi > 0) sig.append(',');
                                                                            sig.append(params[pi].getSimpleName());
                                                                        }
                                                                        sig.append("):").append(method.getReturnType().getSimpleName());
                                                                        signatures.add(sig.toString());
                                                                    }
                                                                }
                                                                for (String sig : signatures) {
                                                                    if (interactionApi.length() > 0) interactionApi.append('|');
                                                                    interactionApi.append(sig);
                                                                }
                                                                LOGGER.info(
                                                                    "GATE_F_CONTRAPTION_INTERACTION_API carriage_id={} player_tick={} methods={}",
                                                                    carriage.getId(), player.tickCount,
                                                                    interactionApi.length() == 0 ? "none" : interactionApi.toString());
                                                            }'''

if "GATE_F_CONTRAPTION_INTERACTION_API" not in source:
    if anchor not in source:
        raise SystemExit("Phase 97 could not find Phase 96 ephemeral assignment anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_CONTRAPTION_INTERACTION_API',
    'apiOwner.getClass().getMethods()',
    'lower.contains("interact")',
    'carriage.getContraption()',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 97 lost interaction API inventory anchors: " + ", ".join(missing))

for forbidden in [
    '.useItemOn(',
    '.useItem(',
    '.attack(',
    'gameMode.use',
    'method.invoke(',
]:
    if forbidden in source:
        raise SystemExit("Phase 97 found forbidden interaction dispatch/invocation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 97: inventoried public carriage/contraption interaction-looking APIs via reflection only; no invocation or mutation")
