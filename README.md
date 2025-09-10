# OmniLauncher

OmniLauncher is a feature-rich Minecraft launcher designed for ease of use, performance, and customization. It supports mod management, server management, JVM presets, backups, and more.

## Features

- Modular architecture with advanced mod management
- Server favorites and ping functionality
- Game settings profiles for easy configuration switching
- Minecraft API integration for version updates and news
- Multiple UI themes and custom color schemes
- Keyboard shortcuts and progress indicators
- Background update checking and installation
- Backup and restore system for mods and settings
- Microsoft account login support
- Skin preview system
- Performance monitoring and network diagnostics
- Configuration import/export
- Installer with uninstaller for easy setup

## Screenshots

![Launcher Main](assets/screenshot_main.png)
![Mods Tab](assets/screenshot_mods.png)
![Settings Tab](assets/screenshot_settings.png)

## Installation

Download the latest installer from the [Releases](https://github.com/your-github-username/omnilancher/releases) page and follow the setup instructions.

## Building from Source

Requirements:
- Python 3.8+
- PyInstaller
- NSIS (for creating installer)

To build the executable:

```bash
pyinstaller OmniLauncher.spec
```

To create the installer, run the NSIS script (provided in the `installer` folder).

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
