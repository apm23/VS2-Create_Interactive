# Regression and Release Test Plan

A build is not final merely because Gradle succeeds.

## Gate A — static/build
- Clean checkout on Java 25.
- Gradle wrapper validation.
- `clean build` succeeds from an empty Gradle cache when CI permits.
- No unresolved mappings/mixins.
- No Fabric entrypoint loads client-only Minecraft classes on dedicated server.

## Gate B — dedicated-server smoke
- Server boots with the production mod set.
- World loads without registry remap errors.
- Server reaches ready state and remains alive long enough to detect delayed startup crashes.
- Clean shutdown completes without save exceptions.

## Gate C — supplied train-world regression
Always restore a fresh copy of `train test.zip` before this gate.

Required scenarios:
- Automatic train begins moving under its existing schedule/driver.
- Player boards while stopped and while moving.
- Walk front/back/left/right in carriage.
- Sprint and crouch while train moves.
- Jump repeatedly on floor, slabs, and transitions.
- Cross between carriages at steady speed.
- Cross between carriages during curves, slopes, acceleration, and braking.
- Stand at carriage edge without sticky pull.
- Leave the train in survival movement where safe.
- Creative-fly away from the moving train in every direction.
- Fly near but not touching the train and confirm there is no attraction.
- Stand beside track while train passes and confirm zero proximity pull.
- Re-enter after leaving and confirm no stale velocity/transform state.
- Confirm camera and hit detection remain aligned with visible train blocks.

## Gate D — moving-ship block interaction
- Place a full block while train/ship is moving.
- Place slab/stair in multiple orientations.
- Break newly placed block while moving.
- Interact with newly placed block if it has use behavior.
- Confirm block remains in ship-local coordinates through curves and speed changes.
- Confirm placement does not require disassemble/reassemble.
- Confirm server authority: reconnect and verify state persists.

## Gate E — multiplayer synchronization
- Dedicated server plus at least two logical clients/test actors when tooling permits.
- One actor rides while another observes from world space.
- Observer sees correct player/train transform.
- Block placement/breaking is synchronized and persisted.
- No duplicate placement, ghost blocks, rubber-banding, or desync after reconnect.

## Failure policy
Any failure in A-D blocks release. A failure must get a reproducible regression case before the fix is considered complete. Existing passing cases must be rerun after every physics/player-transform change.
