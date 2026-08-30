#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateNewContraptionCellReplication.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #131 proves sustained carriage-local stability for nine consecutive
# ticks with zero local-frame span. The same run also proves the authoritative server
# placement succeeds while Create Fly's client handler rejects a packet when localPos is
# not already present; the fixture-only insertion immediately makes the exact client cell
# visible. Install the narrow compatibility fix at the client handler RETURN: only add a
# previously-missing, non-air cell that arrived in Create's own block-change packet.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import java.lang.reflect.Method;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Create Fly 6.0.9's AllHandle#onContraptionBlockChanged returns when a packet targets
 * a local position absent from the client contraption map. That is correct for ordinary
 * state updates only if the cell already exists, but it drops server-authoritative new
 * cells produced by CarriageContraptionEntity#setBlock. Preserve Create's normal handler
 * and fill only that missing-cell case from the packet it already accepted from server.
 */
@Mixin(targets = "com.zurrtum.create.client.AllHandle", remap = false)
public abstract class MixinCreateNewContraptionCellReplication {
    @Inject(method = "onContraptionBlockChanged", at = @At("RETURN"), remap = false)
    private void vs2$replicateMissingCell(@Coerce Object packet, CallbackInfo ci) {
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.level == null || packet == null) return;
        try {
            int entityId = ((Number) packet.getClass().getMethod("entityId").invoke(packet)).intValue();
            BlockPos localPos = (BlockPos) packet.getClass().getMethod("localPos").invoke(packet);
            BlockState newState = (BlockState) packet.getClass().getMethod("newState").invoke(packet);
            if (localPos == null || newState == null || newState.isAir()) return;

            Entity entity = minecraft.level.getEntity(entityId);
            if (entity == null) return;
            Object contraption = entity.getClass().getMethod("getContraption").invoke(entity);
            if (contraption == null) return;
            Object blocksObject = contraption.getClass().getMethod("getBlocks").invoke(contraption);
            if (!(blocksObject instanceof Map<?, ?> blocks) || blocks.containsKey(localPos)) return;

            @SuppressWarnings("unchecked")
            Map<Object, Object> writable = (Map<Object, Object>) (Map<?, ?>) blocks;
            StructureTemplate.StructureBlockInfo info =
                new StructureTemplate.StructureBlockInfo(localPos.immutable(), newState, null);
            writable.put(localPos.immutable(), info);

            try {
                contraption.getClass().getMethod("invalidateColliders").invoke(contraption);
            } catch (ReflectiveOperationException ignored) {
                // Rendering reset below remains sufficient on Create variants without this helper.
            }
            for (Method method : this.getClass().getMethods()) {
                if (!method.getName().equals("resetClientContraption") || method.getParameterCount() != 1) continue;
                if (!method.getParameterTypes()[0].isInstance(contraption)) continue;
                method.invoke(this, contraption);
                break;
            }
            System.out.println("VS2_CREATE_NEW_CELL_REPLICATION entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState + " inserted=true");
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            // Compatibility is intentionally fail-open: never crash Create/VS2 for an optional seam.
        }
    }
}
''', encoding="utf-8")

config = json.loads(mixin_json.read_text(encoding="utf-8"))
client_mixins = config.setdefault("client", [])
name = "MixinCreateNewContraptionCellReplication"
if name not in client_mixins:
    client_mixins.append(name)
mixin_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

required = [
    'targets = "com.zurrtum.create.client.AllHandle"',
    'method = "onContraptionBlockChanged"',
    'blocks.containsKey(localPos)',
    'new StructureTemplate.StructureBlockInfo',
    'writable.put(localPos.immutable(), info)',
    'resetClientContraption',
    'VS2_CREATE_NEW_CELL_REPLICATION',
]
text = java.read_text(encoding="utf-8")
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 128 lost Create new-cell replication anchors: " + ", ".join(missing))

for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', '.useItemOn(', '.attack(']:
    if forbidden in text:
        raise SystemExit("Phase 128 found forbidden player/train mutation: " + forbidden)

print("Phase 128: production compat fills Create Fly client new-cell replication gap from authoritative block-change packets")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase129.py")), run_name="__main__")
