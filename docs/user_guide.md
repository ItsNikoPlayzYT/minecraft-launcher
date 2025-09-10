# OmniLauncher User Guide

## Getting Started

### Installation
1. Download the installer from the [Releases](https://github.com/your-github-username/omnilancher/releases) page
2. Run the installer and follow the setup wizard
3. Launch OmniLauncher from the desktop shortcut or start menu

### First Time Setup
1. Enter your Minecraft username
2. Select your preferred Minecraft version
3. Configure JVM arguments if needed
4. Choose your preferred theme

## Main Features

### Launcher Tab
- **Username**: Enter your Minecraft username
- **Version Selection**: Choose from available Minecraft versions
- **Skin Preview**: View your Minecraft skin
- **Microsoft Login**: Authenticate with Microsoft account
- **Launch Button**: Start Minecraft with your settings

### Mods Tab
- **Install Mods**: Add mods from local files or URLs
- **Mod Management**: View, remove, and organize installed mods
- **Search**: Find specific mods in your collection
- **Mod Info**: View details about installed mods
- **Open Mods Folder**: Access your mods directory

### Servers Tab
- **Add Servers**: Save favorite servers with custom names
- **Server List**: View all saved servers
- **Ping Servers**: Test server connectivity
- **Quick Connect**: Launch Minecraft and connect to servers

### Settings Tab
- **JVM Presets**: Choose from optimized JVM configurations
- **Themes**: Customize the launcher appearance
- **Profiles**: Save and load different configurations
- **Backup & Restore**: Create backups of your setup
- **System Info**: View system specifications
- **Network Diagnostics**: Test connectivity to Minecraft services

## Advanced Configuration

### JVM Arguments
OmniLauncher includes several JVM presets:
- **Default**: Standard Minecraft settings
- **Performance**: Optimized for gaming performance
- **Low Memory**: Reduced memory usage
- **High Performance**: Maximum performance settings
- **Debug**: Diagnostic settings for troubleshooting

### Custom JVM Arguments
You can also enter custom JVM arguments in the settings tab. Common arguments include:
- `-Xmx4G`: Set maximum heap size to 4GB
- `-Xms2G`: Set initial heap size to 2GB
- `-XX:+UseG1GC`: Use G1 garbage collector

### Profiles
Save different configurations for different play styles:
1. Configure your settings
2. Click "Save Profile"
3. Enter a profile name
4. Load profiles anytime with "Load Profile"

## Troubleshooting

### Common Issues

**Launcher won't start**
- Ensure you have Python 3.8+ installed
- Check that all dependencies are installed
- Verify your antivirus isn't blocking the launcher

**Minecraft won't launch**
- Check your Java installation
- Verify your Minecraft account credentials
- Ensure your selected version is compatible

**Mods not working**
- Check mod compatibility with your Minecraft version
- Ensure you have the correct mod loader (Forge/Fabric)
- Verify mod dependencies are installed

**Connection issues**
- Check your internet connection
- Use Network Diagnostics in settings
- Verify Minecraft services are online

### Logs and Debugging
- View the terminal tab for real-time logs
- Check the launcher.log file for detailed information
- Enable debug mode in settings for additional logging

## Support

For support and bug reports:
- Open an issue on [GitHub](https://github.com/your-github-username/omnilancher/issues)
- Check the changelog for recent fixes
- Join our Discord community (link in README)

## Advanced Features

### Backup System
- Automatic backups of mods and settings
- Restore from previous backups
- Export/import configurations

### Performance Monitoring
- Real-time system resource usage
- Launcher performance statistics
- Disk usage analysis

### Customization
- Custom themes and colors
- Keyboard shortcuts
- Custom button images
- Language support

## Development

### Building from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller OmniLauncher.spec

# Create installer (requires NSIS)
makensis installer/omnilancher_installer.nsi
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

OmniLauncher is licensed under the MIT License. See LICENSE file for details.
