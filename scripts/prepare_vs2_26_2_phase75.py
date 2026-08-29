#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderTrace.java"
source = trace.read_text(encoding="utf-8")

# Run 90 proved Create computes a non-zero getContactPointMotion while the
# LocalPlayer remains fixed in world space. Trace ContraptionCollider.collide's
# input/output for the LocalPlayer so we can distinguish a zeroed collision
# allowance from a later setPos/position-reset problem. Read-only telemetry only.
field_anchor = '''    private static int vs2$shapeCalls;'''
field_insert = '''    private static int vs2$shapeCalls;\n    private static int vs2$localPlayerCollideCalls;'''
if "vs2$localPlayerCollideCalls" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 75 could not find ContraptionCollider trace field anchor")
    source = source.replace(field_anchor, field_insert, 1)

class_end = source.rfind("}")
if class_end < 0:
    raise SystemExit("Phase 75 could not find ContraptionCollider trace class end")

handler = r'''

    @Inject(method = "collide", at = @At("RETURN"), remap = false, require = 0)
    private static void vs2$traceLocalPlayerCollide(
        net.minecraft.world.phys.Vec3 requested,
        net.minecraft.world.entity.Entity entity,
        org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable<net.minecraft.world.phys.Vec3> cir
    ) {
        if (!(entity instanceof net.minecraft.client.player.LocalPlayer)) return;
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        if (requested == null) return;
        double horizontalSq = requested.x * requested.x + requested.z * requested.z;
        if (horizontalSq < 1.0E-10) return;
        int index = ++vs2$localPlayerCollideCalls;
        if (index > 80) return;
        net.minecraft.world.phys.Vec3 allowed = cir.getReturnValue();
        VS2_GATE_E_LOGGER.info(
            "GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT index={} requested={},{},{} allowed={},{},{} pos={},{},{} on_ground={} thread={}",
            index,
            requested.x, requested.y, requested.z,
            allowed == null ? Double.NaN : allowed.x,
            allowed == null ? Double.NaN : allowed.y,
            allowed == null ? Double.NaN : allowed.z,
            entity.getX(), entity.getY(), entity.getZ(), entity.onGround(), thread);
    }
'''

if "GATE_E_CREATE_LOCALPLAYER_COLLIDE_RESULT" not in source:
    source = source[:class_end] + handler + source[class_end:]

trace.write_text(source, encoding="utf-8")
print("Phase 75: traced Create ContraptionCollider.collide requested-vs-allowed horizontal carry for LocalPlayer; read-only telemetry only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase76.py")), run_name="__main__")
