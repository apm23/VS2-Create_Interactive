#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

# Phase 99 depends on the cumulative Phase 98 native-target profile. Apply Phase 98
# first so this script is safe to chain from Phase 54 as well as invoke standalone.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase98.py")), run_name="__main__")
source = client_probe.read_text(encoding="utf-8")

# Production-world #46 proved the exact native target is a Copycats structural block
# with an empty main hand. Before any real dispatch, inventory the target block's public
# interaction-shaped methods so we can tell whether an empty-hand click could still
# invoke Copycats behavior. Reflection only; never invoke block/use/interaction methods.
anchor = '''                                                                                    targetStateProfile = String.valueOf(stateObject);'''
replacement = anchor + '''
                                                                                    Object targetBlockObject = stateObject.getClass().getMethod("getBlock").invoke(stateObject);
                                                                                    java.util.LinkedHashSet<String> targetInteractionSurface = new java.util.LinkedHashSet<>();
                                                                                    for (java.lang.reflect.Method targetMethod : targetBlockObject.getClass().getMethods()) {
                                                                                        String targetName = targetMethod.getName().toLowerCase(java.util.Locale.ROOT);
                                                                                        if (!(targetName.contains("use") || targetName.contains("interact")
                                                                                                || targetName.contains("click") || targetName.contains("place")
                                                                                                || targetName.contains("attack"))) continue;
                                                                                        StringBuilder targetSig = new StringBuilder(targetMethod.getName()).append('(');
                                                                                        Class<?>[] targetParams = targetMethod.getParameterTypes();
                                                                                        for (int ti = 0; ti < targetParams.length; ti++) {
                                                                                            if (ti > 0) targetSig.append(',');
                                                                                            targetSig.append(targetParams[ti].getSimpleName());
                                                                                        }
                                                                                        targetSig.append("):").append(targetMethod.getReturnType().getSimpleName());
                                                                                        targetInteractionSurface.add(targetSig.toString());
                                                                                    }
                                                                                    LOGGER.info(
                                                                                        "GATE_F_TARGET_BLOCK_INTERACTION_SURFACE carriage_id={} player_tick={} block_class={} methods={}",
                                                                                        carriage.getId(), player.tickCount, targetBlockObject.getClass().getName(),
                                                                                        targetInteractionSurface.isEmpty() ? "none" : String.join("|", targetInteractionSurface));'''

if "GATE_F_TARGET_BLOCK_INTERACTION_SURFACE" not in source:
    if anchor not in source:
        raise SystemExit("Phase 99 could not find Phase 98 target-state profile anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_TARGET_BLOCK_INTERACTION_SURFACE',
    'getMethod("getBlock").invoke(stateObject)',
    'targetMethod.getName().toLowerCase(java.util.Locale.ROOT)',
    'targetInteractionSurface.add(targetSig.toString())',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 99 lost target interaction-surface anchors: " + ", ".join(missing))

for forbidden in [
    '.handlePlayerInteraction(', 'handleMethod.invoke(',
    'rightClickingOnContraptionsGetsHandledLocally(client',
    'ContraptionInteractionPacket', '.useItemOn(', '.useItem(', '.attack(', 'gameMode.use',
]:
    if forbidden in source:
        raise SystemExit("Phase 99 found forbidden interaction dispatch/mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 99: inventoried the exact moving-train target block interaction surface via reflection only; no interaction dispatch or mutation")
