#!/usr/bin/env python3
"""CI trigger for the M1 Create/VS2 ownership-order micro-proof.

This file is intentionally outside the cumulative source-patching chain. Changing it triggers
production-world-smoke through the existing scripts/prepare_vs2_26_2*.py path filter without
changing generated gameplay code. The workflow_run diagnostic then correlates existing read-only
Create contact, support, LocalPlayer setPos, and VS2 EntityDragger telemetry around the first
ownership loss.
"""
print("Phase 204 ownership micro-proof trigger: read-only diagnostics, no gameplay/source mutation")
