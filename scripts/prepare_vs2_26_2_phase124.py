#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #122 failed before the placement-pending path because the disposable
# moving-train fixture experienced a large carriage-frame discontinuity after carry proof.
# Phase 123 telemetry therefore never executed. Move the same ownership observation to a
# class-load static probe so it is independent of fixture timing and remains strictly
# read-only. This does not send packets or mutate player/train/world/physics state.
marker = "GATE_F_CREATE_CLIENT_HANDLER_CLASSLOAD"
if marker not in source:
    block = r'''
    static {
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
            "GATE_F_CREATE_CLIENT_HANDLER_CLASSLOAD instance_class={} handler_declaring_class={} handler_signature={} error={} read_only=true",
            instanceClass, handlerDeclaringClass, handlerSignature, handlerError);
    }
'''
    head, sep, tail = source.rpartition("}")
    if not sep:
        raise SystemExit("Phase 124 could not find GateEClientProbe closing brace")
    source = head + block + sep + tail

required = [
    marker,
    'Class.forName("com.zurrtum.create.AllClientHandle")',
    'onContraptionBlockChanged',
    'handler_declaring_class={}',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 124 lost class-load handler telemetry anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 124: probes Create Fly client block-change handler ownership at Gate E class load; read-only and fixture-timing independent")
