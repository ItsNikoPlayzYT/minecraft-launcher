from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os", "requests", "minecraft_launcher_lib", "PIL", "psutil"],
    "include_files": [
        "lang",
        "assets",
        "mods.py",
        "servers.py",
        "jvm_presets.py",
        "updater.py",
        "backup.py",
        "launcher.ico",
        "rounded_button.png",
        "config.json",
    ],
}

setup(
    name="OmniLauncher",
    version="1.5.8",
    description="Minecraft launcher with mod management and more",
    options={"build_exe": build_exe_options},
    executables=[Executable("launcher.py", base=None, icon="launcher.ico")],
)
