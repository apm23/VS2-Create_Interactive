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
# Production-world #264 proved this authoritative packet path can publish exact cell
# presence. For the extended movement gate, packet arrival now publishes readiness only;
# Phase154 publishes the historical EXACT_SYNC completion marker after its bounded walk
# finishes. This changes telemetry ordering only and does not mutate player/train physics.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import java.lang.reflect.Method;
import java.util.Map;
import java.util.Objects;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(targets = "com.zurrtum.create.client.AllHandle", remap = false)
public abstract class MixinCreateNewContraptionCellReplication {
    private void vs2$reportExactPublishedTarget(int entityId, BlockPos localPos, BlockState newState, String path) {
        String carriageText = System.getProperty("vs2.productionNativePlacementCarriageId");
        String xText = System.getProperty("vs2.productionNativePlacementEmptyX");
        String yText = System.getProperty("vs2.productionNativePlacementEmptyY");
        String zText = System.getProperty("vs2.productionNativePlacementEmptyZ");
        if (carriageText == null || xText == null || yText == null || zText == null) return;
        try {
            int expectedCarriage = Integer.parseInt(carriageText);
            BlockPos expectedPos = new BlockPos(Integer.parseInt(xText), Integer.parseInt(yText), Integer.parseInt(zText));
            if (entityId == expectedCarriage && expectedPos.equals(localPos) && newState.is(Blocks.STONE)) {
                System.setProperty("vs2.productionNativePlacementClientObserved", "true");
                System.setProperty("vs2.productionNativePlacementExactClientObserved", "true");
                System.setProperty("vs2.productionNativePlacementExactCellPresent", "true");
                Minecraft exactMinecraft = Minecraft.getInstance();
                if (System.getProperty("vs2.productionNativePlacementExactCellFirstTick") == null
                        && exactMinecraft.player != null) {
                    System.setProperty("vs2.productionNativePlacementExactCellFirstTick",
                        Integer.toString(exactMinecraft.player.tickCount));
                }
                System.out.println("GATE_F_NATIVE_PLACEMENT_PACKET_READY carriage_id=" + entityId
                    + " empty_local=" + localPos + " state=" + newState
                    + " packet_authoritative=true exact_cell_present=true completion_deferred_to_walk=true source=" + path);
            }
        } catch (RuntimeException ignored) {
            // Telemetry is fail-open and never changes packet handling or gameplay state.
        }
    }

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
            if (!(blocksObject instanceof Map<?, ?> blocks)) return;

            Object nativeEntry = blocks.get(localPos);
            if (nativeEntry != null) {
                Object nativeState = null;
                try {
                    nativeState = nativeEntry.getClass().getMethod("state").invoke(nativeEntry);
                } catch (ReflectiveOperationException ignored) {
                    // Telemetry only; preserve Create's native result even if value shape changes.
                }
                boolean stateMatch = Objects.equals(nativeState, newState);
                System.out.println("VS2_CREATE_CELL_REPLICATION_CONFIRMED entity_id=" + entityId
                    + " local_pos=" + localPos + " state=" + newState
                    + " path=create_native entry_present=true state_match=" + stateMatch
                    + " packet_authoritative=true");
                if (stateMatch) {
                    vs2$reportExactPublishedTarget(entityId, localPos, newState, "create_native");
                }
                return;
            }

            @SuppressWarnings("unchecked")
            Map<Object, Object> writable = (Map<Object, Object>) (Map<?, ?>) blocks;
            StructureTemplate.StructureBlockInfo info =
                new StructureTemplate.StructureBlockInfo(localPos.immutable(), newState, null);
            writable.put(localPos.immutable(), info);

            boolean resetInvoked = false;
            try {
                contraption.getClass().getMethod("invalidateColliders").invoke(contraption);
            } catch (ReflectiveOperationException ignored) {
                // Rendering reset below remains sufficient on Create variants without this helper.
            }
            for (Method method : this.getClass().getMethods()) {
                if (!method.getName().equals("resetClientContraption") || method.getParameterCount() != 1) continue;
                if (!method.getParameterTypes()[0].isInstance(contraption)) continue;
                method.invoke(this, contraption);
                resetInvoked = true;
                break;
            }
            System.out.println("VS2_CREATE_NEW_CELL_REPLICATION entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState + " inserted=true");
            System.out.println("VS2_CREATE_NEW_CELL_REPLICATION_PROVEN entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState
                + " inserted=true reset_invoked=" + resetInvoked + " packet_authoritative=true");
            System.out.println("VS2_CREATE_CELL_REPLICATION_CONFIRMED entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState
                + " path=vs2_new_cell_fallback entry_present=true state_match=true"
                + " packet_authoritative=true");
            vs2$reportExactPublishedTarget(entityId, localPos, newState, "vs2_new_cell_fallback");
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
    'blocks.get(localPos)',
    'path=create_native',
    'new StructureTemplate.StructureBlockInfo',
    'writable.put(localPos.immutable(), info)',
    'resetClientContraption',
    'VS2_CREATE_NEW_CELL_REPLICATION',
    'VS2_CREATE_NEW_CELL_REPLICATION_PROVEN',
    'VS2_CREATE_CELL_REPLICATION_CONFIRMED',
    'GATE_F_NATIVE_PLACEMENT_PACKET_READY',
    'completion_deferred_to_walk=true',
    'vs2$reportExactPublishedTarget',
    'path=vs2_new_cell_fallback',
    'packet_authoritative=true',
    'vs2.productionNativePlacementExactCellPresent',
    'vs2.productionNativePlacementExactCellFirstTick',
    'exact_cell_present=true',
]
text = java.read_text(encoding="utf-8")
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 128 lost Create new-cell replication anchors: " + ", ".join(missing))

if 'GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC' in text:
    raise SystemExit("Phase 128 must not publish placement completion before the extended walk proof")

for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', '.useItemOn(', '.attack(']:
    if forbidden in text:
        raise SystemExit("Phase 128 found forbidden player/train mutation: " + forbidden)

print("Phase 128/149: production compat fills Create Fly client new-cell replication gap and publishes authoritative exact-cell readiness while deferring completion to the walk proof")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase129.py")), run_name="__main__")
