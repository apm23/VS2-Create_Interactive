#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderTrace.java"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = trace.read_text(encoding="utf-8")
old_fields = '''    private static int vs2$collideCalls;\n    private static int vs2$shapeCalls;'''
new_fields = '''    private static int vs2$serverCollideCalls;\n    private static int vs2$clientCollideCalls;\n    private static int vs2$shapeCalls;'''
if old_fields not in source:
    raise SystemExit("Phase 63 could not find narrowphase counter fields")
source = source.replace(old_fields, new_fields, 1)

old_handler = '''    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)\n    private static void vs2$traceCollideEntities(CallbackInfo ci) {\n        if (vs2$collideCalls++ < 12) {\n            VS2_GATE_E_LOGGER.info("GATE_E_CREATE_COLLIDE_ENTITIES_CALL index={}", vs2$collideCalls);\n        }\n    }'''
new_handler = '''    @Inject(method = "collideEntities", at = @At("HEAD"), remap = false, require = 0)\n    private static void vs2$traceCollideEntities(CallbackInfo ci) {\n        String thread = Thread.currentThread().getName();\n        boolean clientThread = thread.contains("Render") || thread.contains("Client");\n        int index = clientThread ? ++vs2$clientCollideCalls : ++vs2$serverCollideCalls;\n        if (index <= 24) {\n            VS2_GATE_E_LOGGER.info(\n                "GATE_E_CREATE_COLLIDE_ENTITIES_CALL side={} index={} thread={}",\n                clientThread ? "client" : "server", index, thread);\n        }\n    }'''
if old_handler not in source:
    raise SystemExit("Phase 63 could not find collideEntities trace handler")
source = source.replace(old_handler, new_handler, 1)
trace.write_text(source, encoding="utf-8")

probe = client_probe.read_text(encoding="utf-8")
old_decl = '''    private static boolean createPlayerTypeLogged;\n    private static long ticks;'''
new_decl = '''    private static boolean createPlayerTypeLogged;\n    private static boolean createColliderApiLogged;\n    private static long ticks;'''
if old_decl not in probe:
    raise SystemExit("Phase 63 could not find Gate E API-log state anchor")
probe = probe.replace(old_decl, new_decl, 1)

old_ready = '''            var player = client.player;\n            if (!createPlayerTypeLogged) {'''
new_ready = '''            var player = client.player;\n            if (!createColliderApiLogged) {\n                createColliderApiLogged = true;\n                try {\n                    Class<?> colliderClass = Class.forName("com.zurrtum.create.content.contraptions.ContraptionCollider");\n                    StringBuilder methods = new StringBuilder();\n                    for (java.lang.reflect.Method method : colliderClass.getDeclaredMethods()) {\n                        String lower = method.getName().toLowerCase(java.util.Locale.ROOT);\n                        if (!(lower.contains("collid") || lower.contains("shape") || lower.contains("entity"))) continue;\n                        if (methods.length() > 0) methods.append('|');\n                        methods.append(method.getName()).append('(');\n                        Class<?>[] params = method.getParameterTypes();\n                        for (int i = 0; i < params.length; i++) {\n                            if (i > 0) methods.append(',');\n                            methods.append(params[i].getSimpleName());\n                        }\n                        methods.append(")->").append(method.getReturnType().getSimpleName());\n                    }\n                    LOGGER.info("GATE_E_CREATE_COLLIDER_API methods={}", methods);\n                } catch (ReflectiveOperationException | RuntimeException exception) {\n                    LOGGER.info("GATE_E_CREATE_COLLIDER_API error={}", exception.getClass().getSimpleName());\n                }\n            }\n            if (!createPlayerTypeLogged) {'''
if old_ready not in probe:
    raise SystemExit("Phase 63 could not find Gate E ready-player anchor")
probe = probe.replace(old_ready, new_ready, 1)
client_probe.write_text(probe, encoding="utf-8")

print("Phase 63: separated client/server collideEntities traces and enumerated the runtime Create collider API so silent require=0 misses can be diagnosed without changing collision behavior")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase64.py")), run_name="__main__")
