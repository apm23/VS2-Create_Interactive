#!/usr/bin/env python3
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
# Earlier 26.2 port phases isolate legacy Create compat Java sources. Keep these
# tiny new mixins in their own non-isolated package so Loom actually compiles them.
legacy_java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/compat/create/MixinContraptionColliderLocalPlayer.java"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderLocalPlayer.java"
exact_shapes_java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderClientExactShapes.java"
resources = ROOT / "fabric/src/main/resources"
fabric_mod = resources / "fabric.mod.json"
mixin_json = resources / "vs2-create-compat.mixins.json"

if legacy_java.exists():
    legacy_java.unlink()
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Create Fly 26.2 currently classifies every Player as SERVER inside the common
 * ContraptionCollider#getPlayerType, so the local client player is skipped before
 * collision resolution on that path. Override only the actual LocalPlayer.
 */
@Mixin(targets = "com.zurrtum.create.content.contraptions.ContraptionCollider", remap = false)
public abstract class MixinContraptionColliderLocalPlayer {
    @Inject(method = "getPlayerType", at = @At("HEAD"), cancellable = true, remap = false)
    private static void vs2$createLocalPlayerType(Entity entity, CallbackInfoReturnable<Object> cir) {
        if (!"net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName())) return;
        try {
            Class<?> playerType = Class.forName(
                "com.zurrtum.create.content.contraptions.ContraptionCollider$PlayerType",
                false,
                entity.getClass().getClassLoader());
            Object[] constants = playerType.getEnumConstants();
            if (constants == null) return;
            for (Object constant : constants) {
                if ("CLIENT".equals(String.valueOf(constant))) {
                    cir.setReturnValue(constant);
                    return;
                }
            }
        } catch (ClassNotFoundException ignored) {
            // Create absent: target mixin is client-gated and this path is never used.
        }
    }
}
''', encoding="utf-8")

# Production-world #719 proves the remaining M1 wall failure occurs inside Create's
# client collision boundary, not in fixture input sequencing. Native forward, reverse,
# and strafe all execute, the occupied wall cells are present, but Create's simplified
# collider path returns a zero OBB response while LocalPlayer crosses the wall plane.
# For the LocalPlayer only, under explicit carry compat, let Create fall through to its
# own exact per-block VoxelShape path (getPotentiallyCollidedShapes). ContinuousOBBCollider,
# collision normals, allowed movement, contact registration and setPos remain entirely
# Create-native. No clamp, teleport, synthetic velocity, gravity, or duplicated world state.
exact_shapes_java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import com.zurrtum.create.content.contraptions.Contraption;
import com.zurrtum.create.content.contraptions.ContraptionCollider.PlayerType;
import com.zurrtum.create.foundation.collision.CollisionList;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(targets = "com.zurrtum.create.client.content.contraptions.ContraptionColliderClient", remap = false)
public abstract class MixinContraptionColliderClientExactShapes {
    @Unique
    private static final ThreadLocal<Boolean> VS2_LOCAL_PLAYER_COLLISION = ThreadLocal.withInitial(() -> false);

    @Inject(method = "getPlayerType", at = @At("RETURN"), remap = false)
    private static void vs2$rememberLocalPlayer(Entity entity, CallbackInfoReturnable<PlayerType> cir) {
        VS2_LOCAL_PLAYER_COLLISION.set(entity instanceof LocalPlayer && cir.getReturnValue() == PlayerType.CLIENT);
    }

    @Redirect(
        method = "collideEntities",
        at = @At(
            value = "INVOKE",
            target = "Lcom/zurrtum/create/content/contraptions/Contraption;getSimplifiedEntityColliders()Lcom/zurrtum/create/foundation/collision/CollisionList;"
        ),
        remap = false
    )
    private static CollisionList vs2$useExactCreateShapesForLocalPlayer(Contraption contraption) {
        if (Boolean.getBoolean("vs2.createCarryCompat") && Boolean.TRUE.equals(VS2_LOCAL_PLAYER_COLLISION.get())) {
            return null;
        }
        return contraption.getSimplifiedEntityColliders();
    }
}
''', encoding="utf-8")

mixin_json.write_text(json.dumps({
    "required": False,
    "minVersion": "0.8",
    "package": "org.valkyrienskies.mod.fabric.mixin.gatee",
    "compatibilityLevel": "JAVA_25",
    "client": ["MixinContraptionColliderLocalPlayer", "MixinContraptionColliderClientExactShapes"],
    "injectors": {"defaultRequire": 1}
}, indent=2) + "\n", encoding="utf-8")

metadata = json.loads(fabric_mod.read_text(encoding="utf-8"))
mixins = metadata.setdefault("mixins", [])
entry = {"config": "vs2-create-compat.mixins.json", "environment": "client"}
if entry not in mixins:
    mixins.append(entry)
fabric_mod.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

required_exact = [
    'MixinContraptionColliderClientExactShapes',
    'VS2_LOCAL_PLAYER_COLLISION',
    'entity instanceof LocalPlayer',
    'Boolean.getBoolean("vs2.createCarryCompat")',
    'return null;',
    'return contraption.getSimplifiedEntityColliders();',
]
exact_text = exact_shapes_java.read_text(encoding="utf-8")
missing_exact = [token for token in required_exact if token not in exact_text]
if missing_exact:
    raise SystemExit("Phase 58 lost exact Create LocalPlayer collision-shape anchors: " + ", ".join(missing_exact))
for forbidden in ['setPos(', 'setDeltaMovement(', 'move(', 'teleport(', 'setOnGround(', 'getContactPointMotion(']:
    if forbidden in exact_text:
        raise SystemExit("Phase 58 exact-shape adapter introduced forbidden movement synthesis: " + forbidden)

print("Phase 58: maps common Create LocalPlayer type and routes only client LocalPlayer collision through Create's exact native block shapes")

# Continue with read-only geometry proof so the smoke still validates real carriage geometry.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase59.py")), run_name="__main__")
