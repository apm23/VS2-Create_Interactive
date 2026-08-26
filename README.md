# VS2-Create_Interactive

Fabric 26.2 project targeting Valkyrien-Skies-style moving-ship physics plus Create train interaction without radial pull, forced player teleport correction, or client-only stability hacks.

## Target environment
- Minecraft Java 26.2
- Fabric Loader 0.19.3+
- Java 25
- Create Fly 6.0.9-1
- Singleplayer integrated server and dedicated server

## Primary acceptance criteria
1. Player can stand, walk, sprint, jump, crouch, and move between Create train carriages while the train is moving without being thrown, dragged, teleported, or pulled from nearby space.
2. Creative flight can freely leave a moving train; no train-proximity gravity or velocity lock may remain active after contact ends.
3. A player standing beside a moving train is not affected merely because they are close to it.
4. Blocks can be placed into the moving train/ship space without disassembling and reassembling the train first.
5. The same JAR works in singleplayer and dedicated-server setups; client-only code must remain isolated.
6. No release candidate is considered final unless build, dedicated-server boot, clean-world smoke test, and train-world regression gates pass.

## Upstream policy
- The current modern port baseline is `Eminai-LeoVinci/VS2` branch `1.21.11`, pinned by commit in CI. That fork is GPL-3.0; any distributed derivative/binary from that source must remain GPL-compliant and retain required notices/source availability.
- Official Valkyrien Skies 2 is LGPL-3.0, but the current port harness intentionally starts from the newer GPL fork because it already contains substantial 1.21.11 movement/synchronization porting work.
- Create: Interactive upstream is All Rights Reserved. This repository must not copy its source. Interactive-style behavior will be independently implemented around the required behavior and public APIs.

## Test fixture
The project uses the provided `train test.zip` world as a local regression fixture. The fixture is not committed to Git. Every integration run must restore a fresh copy before launching the server.
