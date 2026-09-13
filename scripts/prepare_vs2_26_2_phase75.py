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
#
# Production-world #724 narrows the remaining floor-loss boundary further. At
# tick 21 vanilla Entity.move consumes -0.0363 Y before Create runs; Create's
# ContinuousOBBCollider then reports surface=true with an upward normal, but the
# observed Create position application only carries X and physical support turns
# false. The existing Phase75 trace intentionally discards zero-horizontal
# collide() requests, which hides the first totalResponse collision-resolution
# call when Create reports a surface contact with collisionResponse == ZERO.
# Add a second read-only trace for exactly those zero requests. Correlating it
# with Phase65 collideMany and Phase76 setPos telemetry will prove whether the
# native response-consumption path returns zero displacement before the later
# horizontal contact-point carry. No position, velocity, onGround, collision,
# input, gravity, train, world, lease, or reference-frame behavior is changed.
field_anchor = '''    private static int vs2$shapeCalls;'''
field_insert = '''    private static int vs2$shapeCalls;\n    private static int vs2$localPlayerCollideCalls;\n    private static int vs2$localPlayerZeroCollideCalls;'''
if "vs2$localPlayerCollideCalls" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 75 could not find ContraptionCollider trace field anchor")
    source = source.replace(field_anchor, field_insert, 1)
elif "vs2$localPlayerZeroCollideCalls" not in source:
    local_field = '''    private static int vs2$localPlayerCollideCalls;'''
    if source.count(local_field) != 1:
        raise SystemExit("Phase 75 could not find unique LocalPlayer collide trace field")
    source = source.replace(
        local_field,
        local_field + '''\n    private static int vs2$localPlayerZeroCollideCalls;''',
        1,
    )

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
    class_end = source.rfind("}")

zero_handler = r'''

    @Inject(method = "collide", at = @At("RETURN"), remap = false, require = 0)
    private static void vs2$traceLocalPlayerZeroCollide(
        net.minecraft.world.phys.Vec3 requested,
        net.minecraft.world.entity.Entity entity,
        org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable<net.minecraft.world.phys.Vec3> cir
    ) {
        if (!(entity instanceof net.minecraft.client.player.LocalPlayer)) return;
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        if (requested == null) return;
        double requestSq = requested.x * requested.x + requested.y * requested.y + requested.z * requested.z;
        if (requestSq >= 1.0E-10) return;
        int index = ++vs2$localPlayerZeroCollideCalls;
        if (index > 120) return;
        net.minecraft.world.phys.Vec3 allowed = cir.getReturnValue();
        net.minecraft.world.phys.Vec3 entityMotion = entity.getDeltaMovement();
        VS2_GATE_E_LOGGER.info(
            "GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT index={} player_tick={} requested={},{},{} allowed={},{},{} motion={},{},{} pos={},{},{} on_ground={} thread={}",
            index, entity.tickCount,
            requested.x, requested.y, requested.z,
            allowed == null ? Double.NaN : allowed.x,
            allowed == null ? Double.NaN : allowed.y,
            allowed == null ? Double.NaN : allowed.z,
            entityMotion.x, entityMotion.y, entityMotion.z,
            entity.getX(), entity.getY(), entity.getZ(), entity.onGround(), thread);
    }
'''

if "GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT" not in source:
    class_end = source.rfind("}")
    source = source[:class_end] + zero_handler + source[class_end:]

trace.write_text(source, encoding="utf-8")
print("Phase 75: traced Create LocalPlayer collide requested-vs-allowed carry plus zero-response floor path; read-only telemetry only")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase76.py")), run_name="__main__")
