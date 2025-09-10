#!/usr/bin/env python3
"""Test script to check if modules can be imported correctly."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mods import create_mods_tab
    print("✓ mods module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import mods: {e}")

try:
    from servers import create_servers_tab
    print("✓ servers module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import servers: {e}")

try:
    from jvm_presets import create_jvm_presets_section
    print("✓ jvm_presets module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import jvm_presets: {e}")

try:
    from updater import create_updater_section
    print("✓ updater module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import updater: {e}")

try:
    from backup import create_backup_section
    print("✓ backup module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import backup: {e}")

print("\nTest completed.")
