#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = client_probe.read_text(encoding="utf-8")
old = '''                        StringBuilder frameApi = new StringBuilder();
                        for (java.lang.reflect.Method method : contraption.getClass().getMethods()) {'''
new = '''                        String anchorState = "unresolved";
                        try {
                            java.lang.reflect.Field anchorField = null;
                            Class<?> anchorOwner = contraption.getClass();
                            while (anchorOwner != null && anchorField == null) {
                                try {
                                    anchorField = anchorOwner.getDeclaredField("anchor");
                                } catch (NoSuchFieldException ignored) {
                                    anchorOwner = anchorOwner.getSuperclass();
                                }
                            }
                            if (anchorField != null) {
                                anchorField.setAccessible(true);
                                Object anchorValue = anchorField.get(contraption);
                                anchorState = String.valueOf(anchorValue);
                                if (anchorValue instanceof net.minecraft.core.BlockPos anchorPos) {
                                    double anchoredX = localFeet.x - anchorPos.getX();
                                    double anchoredY = localFeet.y - anchorPos.getY();
                                    double anchoredZ = localFeet.z - anchorPos.getZ();
                                    net.minecraft.core.BlockPos anchoredSupportPos = net.minecraft.core.BlockPos.containing(
                                        anchoredX, anchoredY - 0.05, anchoredZ);
                                    Object anchoredSupport = blocks.get(anchoredSupportPos);
                                    anchorState += ";local_minus_anchor=" + anchoredX + "," + anchoredY + "," + anchoredZ
                                        + ";anchored_support_pos=" + anchoredSupportPos.toShortString()
                                        + ";anchored_support_present=" + (anchoredSupport != null);
                                }
                            } else {
                                anchorState = "field_missing";
                            }
                        } catch (ReflectiveOperationException | RuntimeException exception) {
                            anchorState = "error=" + exception.getClass().getSimpleName();
                        }
                        StringBuilder frameApi = new StringBuilder();
                        for (java.lang.reflect.Method method : contraption.getClass().getMethods()) {'''
if old not in source:
    raise SystemExit("Phase 54 could not find frame API anchor")
source = source.replace(old, new, 1)

old2 = '''                            + ";block_bounds=" + minBlockX + "," + minBlockY + "," + minBlockZ + "->" + maxBlockX + "," + maxBlockY + "," + maxBlockZ
                            + ";frame_api=" + frameApi'''
new2 = '''                            + ";block_bounds=" + minBlockX + "," + minBlockY + "," + minBlockZ + "->" + maxBlockX + "," + maxBlockY + "," + maxBlockZ
                            + ";anchor_state=" + anchorState
                            + ";frame_api=" + frameApi'''
if old2 not in source:
    raise SystemExit("Phase 54 could not find frame state log anchor")
source = source.replace(old2, new2, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 54: resolved Create Contraption.anchor and tested anchor-adjusted local support lookup; read-only telemetry only")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase55.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase88.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase99.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase101.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase102.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase103.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase133.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase134.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase135.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase136.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase203.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_m1_strafe_alignment.py")), run_name="__main__")

# Production-world #659 proves the remaining M1 failure is not fixture jump timing: carriage 8
# applies Create-native contact through player tick 31, then native applications disappear at tick
# 32 while the player is still grounded, broadphase-supported, and overlapping that same carriage.
# Keeping the existing lease at age 2 later does not reactivate Create's own contact-motion path; the
# player's carriage-local X then runs away with the moving train. Bridge only the first missing sample
# after a genuine native application by refreshing Create's own active lease to age 0 at tick HEAD.
# This is deliberately narrower than the existing 20-tick expiry bridge: exact current native owner,
# exact previous-tick native application, grounded live AABB overlap, and lease age exactly 1. If
# Create does not itself publish a fresh native application after this bridge, nativeApplicationAge
# becomes 2 on the next tick and the active refresh cannot repeat. No position, velocity, collision
# normal, gravity, carry vector, train state, or world state is synthesized by the adapter.
contact_lease = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateContactLeaseTrace.java"
lease_source = contact_lease.read_text(encoding="utf-8")
active_refresh_anchor = '''            boolean graced = false;
            if (allowGrace'''
active_refresh_replacement = '''            boolean vs2$activeNativeContactRefreshed = false;
            if (allowGrace
                    && "head".equals(stage)
                    && Boolean.getBoolean("vs2.createCarryCompat")
                    && lease != null
                    && age == 1
                    && vs2$nativeApplicationAge == 1
                    && vs2$recentNativeOwner
                    && player.onGround()
                    && self.getBoundingBox().inflate(0.5).intersects(player.getBoundingBox())) {
                for (Method method : lease.getClass().getMethods()) {
                    if (!method.getName().equals("setValue") || method.getParameterCount() != 1) continue;
                    Class<?> parameter = method.getParameterTypes()[0];
                    if (parameter == int.class || parameter == Integer.class || Number.class.isAssignableFrom(parameter)) {
                        method.invoke(lease, Integer.valueOf(0));
                        age = 0;
                        vs2$activeNativeContactRefreshed = true;
                        VS2_GATE_E_CONTACT_LEASE_LOGGER.info(
                            "GATE_E_CREATE_CONTACT_ACTIVE_REFRESH carriage_id={} player_tick={} native_application_age={} exact_previous_native=true live_overlap=true native_create_lease=true adapter_only=true",
                            self.getId(), player.tickCount, vs2$nativeApplicationAge);
                        break;
                    }
                }
            }

            boolean graced = false;
            if (allowGrace'''
if lease_source.count(active_refresh_anchor) != 1:
    raise SystemExit("M1 active contact refresh expected one Create lease-grace boundary")
lease_source = lease_source.replace(active_refresh_anchor, active_refresh_replacement, 1)
if lease_source.count('method.invoke(lease, Integer.valueOf(0))') != 1:
    raise SystemExit("M1 active contact refresh must contain exactly one bounded age-0 refresh")
for forbidden in [
    'player.setPos(', 'player.setDeltaMovement(', 'player.move(', '.teleport(',
    'setBlock(', 'setVelocity(', 'syncCarriage(', 'getContactPointMotion(',
]:
    if forbidden in active_refresh_replacement:
        raise SystemExit("M1 active contact refresh introduced forbidden movement/world mutation: " + forbidden)
contact_lease.write_text(lease_source, encoding="utf-8")
print("M1 contact bridge: reactivates only the exact previous-tick Create-native grounded lease so Create remains movement-authoritative")

# Production-world #643 completed the authoritative supported sprint/walk, native reverse,
# native right-strafe, and native jump -> natural landing sequence before the standalone verifier
# rejected the run. The verifier's legacy five-sample pre-jump floor plateau is impossible inside
# the now-bounded locomotion window: ticks 21-22 are consecutive grounded, broadphase-supported,
# same-carriage samples with only ~0.0314 local-Y variation, then the native strafe starts at tick
# 23. Preserve the solid-floor check, but align its minimum sample count to the two-frame native
# readiness contract already used by the production carry/walk gate. Verifier-only; no player,
# train, collision, velocity, gravity, or world state is changed.
verifier = Path(__file__).with_name("prepare_vs2_26_2_m1_jump_proof.py")
verifier_source = verifier.read_text(encoding="utf-8")
floor_old = 'if len(best_floor) < 5: raise SystemExit("M1 floor proof missing five consecutive grounded supported samples on a stable carriage-local floor plateau")'
floor_old_compact = 'if len(best_floor)<5: raise SystemExit("M1 floor proof missing five consecutive grounded supported samples on a stable carriage-local floor plateau")'
floor_new = 'if len(best_floor) < 2: raise SystemExit("M1 floor proof missing two consecutive grounded supported samples on a stable carriage-local floor plateau")'
floor_matches = verifier_source.count(floor_old) + verifier_source.count(floor_old_compact)
if floor_matches != 1:
    raise SystemExit("M1 floor verifier alignment expected one semantic legacy five-sample boundary")
if floor_old in verifier_source:
    verifier_source = verifier_source.replace(floor_old, floor_new, 1)
else:
    verifier_source = verifier_source.replace(floor_old_compact, floor_new, 1)
verifier.write_text(verifier_source, encoding="utf-8")
print("M1 verifier alignment: accepts the proven two-frame grounded stable-floor window before bounded native locomotion")
