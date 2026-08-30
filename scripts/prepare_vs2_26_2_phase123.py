#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #120 proved the authoritative server mutation still succeeds while the
# exact client carriage and all rendered sibling contraptions lack the new cell. Phase 122
# could not resolve vanilla's internal tracker reflectively. Create Fly's packet delegates
# handling through AllClientHandle.INSTANCE; inspect that runtime instance and the declaring
# class of onContraptionBlockChanged before changing packet or placement behavior.
anchor = '''                            LOGGER.info(
                                "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_PENDING carriage_id={} player_tick={} empty_local={} entity_present={} entry_present={} state={} synced=false read_only=true",
                                exactCarriageId, player.tickCount, exactPos, exactEntity != null, exactEntry != null, exactState);'''
probe = anchor + '''
                            if (!java.lang.Boolean.getBoolean("vs2.productionNativePlacementClientHandlerProbed")) {
                                System.setProperty("vs2.productionNativePlacementClientHandlerProbed", "true");
                                String instanceClass = "none";
                                String handlerDeclaringClass = "none";
                                String handlerSignature = "none";
                                String handlerError = "none";
                                try {
                                    Class<?> handleClass = Class.forName("com.zurrtum.create.AllClientHandle");
                                    java.lang.reflect.Field instanceField = handleClass.getField("INSTANCE");
                                    Object handleInstance = instanceField.get(null);
                                    if (handleInstance != null) {
                                        instanceClass = handleInstance.getClass().getName();
                                        for (java.lang.reflect.Method method : handleInstance.getClass().getMethods()) {
                                            if (!method.getName().equals("onContraptionBlockChanged") || method.getParameterCount() != 1) continue;
                                            handlerDeclaringClass = method.getDeclaringClass().getName();
                                            handlerSignature = method.toGenericString();
                                            break;
                                        }
                                    }
                                } catch (ReflectiveOperationException | RuntimeException handlerException) {
                                    handlerError = handlerException.getClass().getSimpleName();
                                }
                                LOGGER.info(
                                    "GATE_F_NATIVE_PLACEMENT_CLIENT_HANDLER carriage_id={} player_tick={} instance_class={} handler_declaring_class={} handler_signature={} error={} read_only=true",
                                    exactCarriageId, player.tickCount, instanceClass, handlerDeclaringClass, handlerSignature, handlerError);
                            }'''

if "GATE_F_NATIVE_PLACEMENT_CLIENT_HANDLER" not in source:
    if anchor not in source:
        raise SystemExit("Phase 123 could not find exact client pending anchor")
    source = source.replace(anchor, probe, 1)

required = [
    'GATE_F_NATIVE_PLACEMENT_CLIENT_HANDLER',
    'productionNativePlacementClientHandlerProbed',
    'com.zurrtum.create.AllClientHandle',
    'onContraptionBlockChanged',
    'handler_declaring_class={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 123 lost client handler telemetry anchors: " + ", ".join(missing))

for forbidden in [
    '.put(', '.remove(', '.clear(', 'setBlock(', 'setPos(', 'setDeltaMovement(',
    '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in probe:
        raise SystemExit("Phase 123 found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 123: traces Create Fly client block-change handler ownership read-only; no packet, block, player, train, or physics mutation")
