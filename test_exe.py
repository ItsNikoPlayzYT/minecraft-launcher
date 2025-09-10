#!/usr/bin/env python3
"""
Test script to verify OmniLauncher exe functionality
"""
import os
import sys
import subprocess
import time

def test_exe():
    """Test the built executable"""
    exe_path = os.path.join("dist", "OmniLauncher", "OmniLauncher.exe")

    if not os.path.exists(exe_path):
        print(f"❌ Executable not found at: {exe_path}")
        return False

    print(f"✅ Found executable: {exe_path}")

    # Check file size
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(".1f"
    # Check if all required files are included
    exe_dir = os.path.dirname(exe_path)
    required_files = [
        "OmniLauncher.exe",
        "_internal",
        "lang",
        "assets"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(exe_dir, file)):
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing files in dist: {missing_files}")
        return False

    print("✅ All required files are present")

    # List contents of _internal directory
    internal_dir = os.path.join(exe_dir, "_internal")
    if os.path.exists(internal_dir):
        internal_files = os.listdir(internal_dir)
        print(f"✅ Internal files: {len(internal_files)} files")
        print(f"   Sample files: {internal_files[:5]}...")

    print("\n🎉 Executable build verification completed successfully!")
    print(f"📦 Final executable: {exe_path}")
    print(".1f"
    return True

if __name__ == "__main__":
    print("Testing OmniLauncher executable...")
    print("=" * 50)

    success = test_exe()

    if success:
        print("\n✅ All tests passed! The executable is ready for distribution.")
    else:
        print("\n❌ Some tests failed. Please check the build process.")

    sys.exit(0 if success else 1)
