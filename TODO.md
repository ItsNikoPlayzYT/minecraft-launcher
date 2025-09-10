# Optimization Tasks for combined_launcher.py

## Step 1: Version Checking and Installation
- [ ] Refactor version list fetching to use cached versions consistently in UI and logic
- [ ] Add version validation before installation to prevent invalid version installs
- [ ] Improve installation progress reporting with smoother UI updates
- [ ] Investigate incremental installation or parallel downloads support in minecraft_launcher_lib

## Step 2: Image Caching and Memory Management
- [ ] Review image_cache usage and LRU eviction logic
- [ ] Optimize cache size and memory usage for images

## Step 3: Reduce Unnecessary API Calls
- [ ] Minimize repeated network calls by caching results effectively
- [ ] Optimize Microsoft login token validation and refresh logic for efficiency

## Step 4: UI Rendering and Scrolling Performance
- [ ] Optimize scroll event handling and UI update calls to improve responsiveness

## Step 5: Code Refactoring and Modularization
- [ ] Split combined_launcher.py into multiple modules:
  - mods.py
  - servers.py
  - updater.py
  - backup.py
  - jvm_presets.py
- [ ] Refactor imports and UI code to use these modules

## Step 6: Threading and Performance
- [ ] Review threading usage for launching, downloading, login, etc.
- [ ] Ensure all UI updates are thread-safe and consistent

## Follow-up Steps
- [ ] Test each optimization incrementally
- [ ] Update documentation and changelog accordingly
