#!/usr/bin/env python3
"""CI trigger note for the post-run native carry-gap correlation workflow.

This file is intentionally not part of the cumulative source-patching chain. Its presence
keeps the next production-world smoke run tied to a repository change while all additional
inspection remains read-only in .github/workflows/carry-gap-diagnostics.yml.
"""
print("Phase 203 diagnostics trigger: no gameplay/source mutation")
