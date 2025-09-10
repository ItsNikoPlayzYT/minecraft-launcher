import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw
import os, threading, json, uuid, subprocess, requests, io, traceback, sys, time, minecraft_launcher_lib, webbrowser, shutil, zipfile, datetime, tempfile

# === Constants ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
MINECRAFT_DIR = minecraft_launcher_lib.utils.get_minecraft_directory()
LAUNCHER_NAME = "OmniLauncher"
LAUNCHER_VERSION = "1.6.0"
ICON = os.path.join(SCRIPT_DIR, "launcher.ico")

# === Logging Setup ===
import logging
logging.basicConfig(
    filename=os.path.join(SCRIPT_DIR, "launcher.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom Rounded Button Class
class RoundedButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # Load image if exists
        if os.path.exists("rounded_button.png"):
            img = ImageTk.PhotoImage(Image.open("rounded_button.png"))
            self.config(image=img, compound="center", relief="flat", borderwidth=0)
            self.image = img  # Keep reference

# === Themes ===
THEMES = {
    "dark": {
        "bg": "#1e1e2f", "fg": "#e0e0e0",
        "entry_bg": "#2d2d44", "entry_fg": "#ffffff",
        "button_bg": "#4a90e2", "button_fg": "#ffffff",
        "font_main": ("Segoe UI", 11), "font_bold": ("Segoe UI", 11, "bold")
    },
    "light": {
        "bg": "#f0f0f0", "fg": "#1e1e2f",
        "entry_bg": "#ffffff", "entry_fg": "#000000",
        "button_bg": "#4a90e2", "button_fg": "#ffffff",
        "font_main": ("Segoe UI", 11), "font_bold": ("Segoe UI", 11, "bold")
    },
    "blue": {
        "bg": "#e6f0ff", "fg": "#003366",
        "entry_bg": "#cce0ff", "entry_fg": "#003366",
        "button_bg": "#3399ff", "button_fg": "#ffffff",
        "font_main": ("Segoe UI", 11), "font_bold": ("Segoe UI", 11, "bold")
    },
    "green": {
        "bg": "#e6ffe6", "fg": "#004d00",
        "entry_bg": "#ccffcc", "entry_fg": "#004d00",
        "button_bg": "#33cc33", "button_fg": "#ffffff",
        "font_main": ("Segoe UI", 11), "font_bold": ("Segoe UI", 11, "bold")
    }
}

# === Load config ===
def load_json(file, default):
    return json.load(open(file, "r", encoding="utf-8")) if os.path.exists(file) else default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def save_config():
    """Save the current config_data to file"""
    try:
        save_json(CONFIG_FILE, config_data)
        append_terminal("Configuration saved successfully.")
    except Exception as e:
        append_terminal(f"Failed to save configuration: {e}")

config_data = load_json(CONFIG_FILE, {})
selected_skin_path = None

# Validate Microsoft login
if "microsoft_login" in config_data:
    try:
        valid = minecraft_launcher_lib.microsoft_account.validate_login(config_data["microsoft_login"])
        if valid:
            config_data["microsoft_login"] = valid
        else:
            config_data.pop("microsoft_login", None)
    except Exception:
        config_data.pop("microsoft_login", None)

# === UUID for offline users ===
def offline_uuid(username):
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{username}"))

# === Thread-Safe UI Updates ===
def thread_safe_ui_update(func):
    """Decorator to make UI updates thread-safe"""
    def wrapper(*args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            return func(*args, **kwargs)
        else:
            root.after(0, lambda: func(*args, **kwargs))
    return wrapper

# === Image Resource Management ===
image_cache = {}
MAX_IMAGE_CACHE_SIZE = 10

def cache_image(key, image):
    """Cache an image with size limit"""
    global image_cache
    if len(image_cache) >= MAX_IMAGE_CACHE_SIZE:
        # Remove oldest entry
        oldest_key = next(iter(image_cache))
        del image_cache[oldest_key]
    image_cache[key] = image

def clear_image_cache():
    """Clear the image cache"""
    global image_cache
    image_cache.clear()

# === Terminal ===
terminal_output = None  # Will be initialized later

@thread_safe_ui_update
def append_terminal(text):
    if terminal_output:
        terminal_output.config(state="normal")
        terminal_output.insert("end", str(text) + "\n")
        terminal_output.see("end")
        terminal_output.config(state="disabled")

@thread_safe_ui_update
def clear_terminal():
    if terminal_output:
        terminal_output.config(state="normal")
        terminal_output.delete("1.0", "end")
        terminal_output.config(state="disabled")
        append_terminal("Terminal cleared.")

# === Mods.py content ===
import time

class ModManager:
    def __init__(self, minecraft_dir, config_data, append_terminal_callback, save_config_callback=None):
        self.minecraft_dir = minecraft_dir
        self.config_data = config_data
        self.append_terminal = append_terminal_callback
        self.save_config = save_config_callback
        self.mods_dir = os.path.join(minecraft_dir, "mods")
        self.mod_list = self.config_data.get("mod_list", [])

        # Ensure mods directory exists
        os.makedirs(self.mods_dir, exist_ok=True)

    def get_mods_list(self):
        """Get list of installed mods"""
        if not os.path.exists(self.mods_dir):
            return []
        return [f for f in os.listdir(self.mods_dir) if f.endswith('.jar')]

    def install_mod_from_file(self, file_path):
        """Install a mod from a local file"""
        try:
            if not file_path.endswith('.jar'):
                raise ValueError("Only .jar files are supported")

            filename = os.path.basename(file_path)

            # Scan mod file for loader and version
            loader = 'Unknown'
            mod_version = 'Unknown'
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    if 'META-INF/MANIFEST.MF' in zip_ref.namelist():
                        with zip_ref.open('META-INF/MANIFEST.MF') as f:
                            manifest = f.read().decode('utf-8', errors='ignore')
                            if 'forge' in manifest.lower() or 'fml' in manifest.lower():
                                loader = 'Forge'
                            elif 'fabric' in manifest.lower():
                                loader = 'Fabric'
                            elif 'neoforge' in manifest.lower():
                                loader = 'NeoForge'
                            # Try to find version in manifest
                            for line in manifest.split('\n'):
                                if line.startswith('Implementation-Version:'):
                                    mod_version = line.split(':', 1)[1].strip()
                                    break
                                elif line.startswith('Specification-Version:'):
                                    mod_version = line.split(':', 1)[1].strip()
                                    break
                self.append_terminal(f"Mod {filename}: Loader {loader}, Version {mod_version}")
            except Exception as e:
                self.append_terminal(f"Could not scan mod file {filename}: {e}")

            dest_path = os.path.join(self.mods_dir, filename)

            shutil.copy2(file_path, dest_path)
            self.append_terminal(f"Mod installed: {filename}")

            # Add to mod list if not already present
            if filename not in self.mod_list:
                self.mod_list.append(filename)
                self.config_data["mod_list"] = self.mod_list
                if self.save_config:
                    self.save_config()

            return True
        except Exception as e:
            self.append_terminal(f"Failed to install mod: {e}")
            return False

    def remove_mod(self, mod_name):
        """Remove a mod"""
        try:
            mod_path = os.path.join(self.mods_dir, mod_name)
            if os.path.exists(mod_path):
                os.remove(mod_path)
                self.append_terminal(f"Mod removed: {mod_name}")

                # Remove from mod list
                if mod_name in self.mod_list:
                    self.mod_list.remove(mod_name)
                    self.config_data["mod_list"] = self.mod_list
                    if self.save_config:
                        self.save_config()

                return True
            else:
                self.append_terminal(f"Mod not found: {mod_name}")
                return False
        except Exception as e:
            self.append_terminal(f"Failed to remove mod: {e}")
            return False

    def download_mod_from_url(self, url, filename=None):
        """Download and install a mod from URL"""
        try:
            if not filename:
                filename = os.path.basename(url)
                if not filename.endswith('.jar'):
                    filename += '.jar'

            dest_path = os.path.join(self.mods_dir, filename)

            self.append_terminal(f"Downloading mod from: {url}")

            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            self.append_terminal(f"Mod downloaded: {filename}")

            # Add to mod list if not already present
            if filename not in self.mod_list:
                self.mod_list.append(filename)
                self.config_data["mod_list"] = self.mod_list
                if self.save_config:
                    self.save_config()

            return True
        except Exception as e:
            self.append_terminal(f"Failed to download mod: {e}")
            return False

    def search_mods(self, query):
        """Search for mods in the installed list"""
        if not query:
            return self.get_mods_list()
        return [mod for mod in self.get_mods_list() if query.lower() in mod.lower()]

    def get_mod_info(self, mod_name):
        """Get basic info about a mod file"""
        try:
            mod_path = os.path.join(self.mods_dir, mod_name)
            if os.path.exists(mod_path):
                stat = os.stat(mod_path)
                return {
                    "name": mod_name,
                    "size": f"{stat.st_size / 1024:.1f} KB",
                    "modified": time.ctime(stat.st_mtime)
                }
            return None
        except Exception as e:
            self.append_terminal(f"Failed to get mod info: {e}")
            return None

def create_mods_tab(parent, minecraft_dir, config_data, append_terminal_callback, current_theme, save_config_callback=None):
    """Create the Mods tab with improved UI and functionality"""
    try:
        # Debug logging
        append_terminal_callback("DEBUG: Creating Mods tab...")
        append_terminal_callback(f"DEBUG: Minecraft dir: {minecraft_dir}")
        append_terminal_callback(f"DEBUG: Config data keys: {list(config_data.keys()) if config_data else 'None'}")

        tab_mods = parent

        # Title
        tk.Label(tab_mods, text="Mod Manager", font=current_theme["font_bold"],
                 bg=current_theme["bg"], fg=current_theme["fg"]).pack(pady=(20, 10))

        # Mod Manager instance
        mod_manager = ModManager(minecraft_dir, config_data, append_terminal_callback)
        append_terminal_callback(f"DEBUG: ModManager created. Mods dir: {mod_manager.mods_dir}")
        append_terminal_callback(f"DEBUG: Initial mod list: {mod_manager.mod_list}")
    except Exception as e:
        append_terminal_callback(f"ERROR: Failed to create Mods tab: {str(e)}")
        import traceback
        append_terminal_callback(f"ERROR: {traceback.format_exc()}")
        return tk.Frame(parent, bg=current_theme["bg"])  # Return empty frame on error

    # Search frame
    search_frame = tk.Frame(tab_mods, bg=current_theme["bg"])
    search_frame.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(search_frame, text="Search:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(side="left")
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"])
    search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # Mods list frame
    list_frame = tk.Frame(tab_mods, bg=current_theme["bg"])
    list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    # Listbox with scrollbar
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    mods_listbox = tk.Listbox(list_frame, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"],
                              selectbackground=current_theme["button_bg"], selectforeground=current_theme["button_fg"],
                              yscrollcommand=scrollbar.set)
    mods_listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=mods_listbox.yview)

    # Mod info display
    info_frame = tk.Frame(tab_mods, bg=current_theme["bg"])
    info_frame.pack(fill="x", padx=20, pady=(0, 10))

    info_label = tk.Label(info_frame, text="Select a mod to view info", bg=current_theme["bg"], fg=current_theme["fg"])
    info_label.pack(anchor="w")

    # URL download frame
    url_frame = tk.Frame(tab_mods, bg=current_theme["bg"])
    url_frame.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(url_frame, text="Download from URL:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w")
    url_var = tk.StringVar()
    url_entry = tk.Entry(url_frame, textvariable=url_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"])
    url_entry.pack(fill="x", pady=(0, 5))

    # Buttons frame
    buttons_frame = tk.Frame(tab_mods, bg=current_theme["bg"])
    buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

    def refresh_mods_list():
        mods_listbox.delete(0, tk.END)
        query = search_var.get()
        mods = mod_manager.search_mods(query)
        for mod in mods:
            mods_listbox.insert(tk.END, mod)

    def install_mod():
        file_path = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=[("Jar files", "*.jar"), ("All files", "*.*")]
        )
        if file_path:
            if mod_manager.install_mod_from_file(file_path):
                refresh_mods_list()
                messagebox.showinfo("Success", "Mod installed successfully!")
            else:
                messagebox.showerror("Error", "Failed to install mod.")

    def download_mod():
        url = url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL.")
            return

        def download_thread():
            if mod_manager.download_mod_from_url(url):
                refresh_mods_list()
                messagebox.showinfo("Success", "Mod downloaded and installed successfully!")
            else:
                messagebox.showerror("Error", "Failed to download mod.")

        threading.Thread(target=download_thread, daemon=True).start()

    def remove_selected_mod():
        selection = mods_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to remove.")
            return

        mod_name = mods_listbox.get(selection[0])
        if messagebox.askyesno("Confirm", f"Remove mod '{mod_name}'?"):
            if mod_manager.remove_mod(mod_name):
                refresh_mods_list()
                messagebox.showinfo("Success", "Mod removed successfully!")
            else:
                messagebox.showerror("Error", "Failed to remove mod.")

    def show_mod_info():
        selection = mods_listbox.curselection()
        if not selection:
            info_label.config(text="Select a mod to view info")
            return

        mod_name = mods_listbox.get(selection[0])
        info = mod_manager.get_mod_info(mod_name)
        if info:
            info_text = f"Name: {info['name']}\nSize: {info['size']}\nModified: {info['modified']}"
            info_label.config(text=info_text)
        else:
            info_label.config(text="Could not retrieve mod info")

    def open_mods_folder():
        try:
            os.startfile(mod_manager.mods_dir)
        except Exception as e:
            append_terminal_callback(f"Error opening mods folder: {e}")
            messagebox.showerror("Error", f"Failed to open mods folder: {e}")

    # Bind events
    search_var.trace("w", lambda *args: refresh_mods_list())
    mods_listbox.bind('<<ListboxSelect>>', lambda *args: show_mod_info())

    # Buttons
    tk.Button(buttons_frame, text="Install Mod", command=install_mod,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    tk.Button(buttons_frame, text="Download from URL", command=download_mod,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    tk.Button(buttons_frame, text="Remove Selected", command=remove_selected_mod,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    tk.Button(buttons_frame, text="Refresh List", command=refresh_mods_list,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    tk.Button(buttons_frame, text="Open Mods Folder", command=open_mods_folder,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left")

    # Initial refresh
    refresh_mods_list()

    return tab_mods

# === updater.py content ===
class Updater:
    def __init__(self, current_version, launcher_name, append_terminal_callback):
        self.current_version = current_version
        self.launcher_name = launcher_name
        self.append_terminal = append_terminal_callback
        self.github_repo = "your-github-username/omnilancher"  # Replace with actual GitHub repo
        self.update_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"

    def check_for_updates(self):
        """Check for updates from GitHub releases"""
        try:
            self.append_terminal("Checking for launcher updates...")
            response = requests.get(self.update_url, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip('v')
            download_url = None

            # Find the appropriate asset (assuming it's a zip file)
            for asset in release_data.get("assets", []):
                if asset["name"].endswith(".zip"):
                    download_url = asset["browser_download_url"]
                    break

            if not download_url:
                # Fallback to source code zip
                download_url = release_data["zipball_url"]

            return {
                "latest_version": latest_version,
                "download_url": download_url,
                "changelog": release_data.get("body", "No changelog available"),
                "release_url": release_data["html_url"]
            }

        except Exception as e:
            self.append_terminal(f"Failed to check for updates: {e}")
            return None

    def download_and_install_update(self, update_info):
        """Download and install the update"""
        try:
            self.append_terminal("Downloading update...")

            # Download the update
            response = requests.get(update_info["download_url"], timeout=60)
            response.raise_for_status()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name

            self.append_terminal("Extracting update...")

            # Extract to temporary directory
            extract_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find the main directory (GitHub releases might have extra folder)
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                source_dir = os.path.join(extract_dir, contents[0])
            else:
                source_dir = extract_dir

            # Get current launcher directory
            current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

            # Backup current version
            backup_dir = os.path.join(current_dir, "backup")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(current_dir, backup_dir, ignore=shutil.ignore_patterns("backup", "__pycache__", "*.pyc"))

            self.append_terminal("Installing update...")

            # Copy new files (excluding certain files)
            exclude_files = {"config.json", "logs", "screenshots", ".git"}
            for item in os.listdir(source_dir):
                if item in exclude_files:
                    continue

                source_path = os.path.join(source_dir, item)
                dest_path = os.path.join(current_dir, item)

                if os.path.isdir(source_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)

            # Clean up
            os.unlink(temp_path)
            shutil.rmtree(extract_dir)

            self.append_terminal("Update installed successfully!")
            return True

        except Exception as e:
            self.append_terminal(f"Failed to install update: {e}")
            return False

    def compare_versions(self, version1, version2):
        """Compare two version strings"""
        def parse_version(v):
            return [int(x) for x in v.split('.')]

        try:
            v1_parts = parse_version(version1)
            v2_parts = parse_version(version2)

            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            return (v1_parts > v2_parts) - (v1_parts < v2_parts)
        except:
            return 0  # Assume equal if parsing fails

def create_updater_section(parent, current_version, launcher_name, append_terminal_callback, current_theme):
    """Create the updater section for settings tab"""
    updater = Updater(current_version, launcher_name, append_terminal_callback)

    # Update section frame
    update_frame = tk.LabelFrame(parent, text="Launcher Updates", bg=current_theme["bg"], fg=current_theme["fg"])
    update_frame.pack(fill="x", padx=20, pady=(20, 10))

    # Status label
    status_label = tk.Label(update_frame, text="Current version: " + current_version,
                           bg=current_theme["bg"], fg=current_theme["fg"])
    status_label.pack(anchor="w", padx=10, pady=(10, 5))

    def check_updates():
        def do_check():
            update_info = updater.check_for_updates()
            if update_info:
                latest_version = update_info["latest_version"]
                status_label.config(text=f"Current: {current_version} | Latest: {latest_version}")

                if updater.compare_versions(latest_version, current_version) > 0:
                    if messagebox.askyesno("Update Available",
                                         f"A new version is available: {latest_version}\n\n"
                                         f"Current version: {current_version}\n\n"
                                         "Would you like to download and install it?"):
                        if updater.download_and_install_update(update_info):
                            messagebox.showinfo("Success",
                                              "Update installed successfully!\n\n"
                                              "Please restart the launcher to apply the changes.")
                        else:
                            messagebox.showerror("Error", "Failed to install update.")
                else:
                    messagebox.showinfo("Up to Date", "You are running the latest version.")
            else:
                messagebox.showerror("Error", "Failed to check for updates.")

        threading.Thread(target=do_check, daemon=True).start()

    # Check for updates button
    tk.Button(update_frame, text="Check for Updates", command=check_updates,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(pady=(0, 10))

    return update_frame

# === servers.py content ===
class ServerManager:
    def __init__(self, config_data, append_terminal_callback):
        self.config_data = config_data
        self.append_terminal = append_terminal_callback
        self.servers = self.config_data.get("servers", [])

    def add_server(self, name, ip, port="25565"):
        """Add a new server to the list"""
        server = {
            "name": name,
            "ip": ip,
            "port": port
        }

        # Check if server already exists
        for existing in self.servers:
            if existing["ip"] == ip and existing["port"] == port:
                return False, "Server already exists"

        self.servers.append(server)
        self.config_data["servers"] = self.servers
        return True, "Server added successfully"

    def remove_server(self, index):
        """Remove a server from the list"""
        if 0 <= index < len(self.servers):
            removed = self.servers.pop(index)
            self.config_data["servers"] = self.servers
            return True, f"Server '{removed['name']}' removed"
        return False, "Invalid server index"

    def get_servers_list(self):
        """Get formatted list of servers"""
        return [f"{server['name']} ({server['ip']}:{server['port']})" for server in self.servers]

    def get_server_details(self, index):
        """Get server details by index"""
        if 0 <= index < len(self.servers):
            return self.servers[index]
        return None

    def ping_server(self, ip, port):
        """Ping a server to check if it's online"""
        try:
            # This is a basic implementation - in a real scenario you'd use proper Minecraft server pinging
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, int(port)))
            sock.close()
            return result == 0
        except:
            return False

def create_servers_tab(parent, config_data, append_terminal_callback, current_theme, launch_callback):
    """Create the servers management tab"""
    try:
        # Debug logging
        append_terminal_callback("DEBUG: Creating Servers tab...")
        append_terminal_callback(f"DEBUG: Config data keys: {list(config_data.keys()) if config_data else 'None'}")

        tab_servers = parent  # Use parent directly like mods tab

        server_manager = ServerManager(config_data, append_terminal_callback)
        append_terminal_callback(f"DEBUG: ServerManager created. Initial servers: {server_manager.servers}")

        # Title
        tk.Label(tab_servers, text="Server Management", bg=current_theme["bg"], fg=current_theme["fg"],
                 font=current_theme["font_bold"]).pack(pady=(20, 10))
    except Exception as e:
        append_terminal_callback(f"ERROR: Failed to create Servers tab: {str(e)}")
        import traceback
        append_terminal_callback(f"ERROR: {traceback.format_exc()}")
        return tk.Frame(parent, bg=current_theme["bg"])  # Return empty frame on error

    # Servers listbox with scrollbar
    listbox_frame = tk.Frame(tab_servers, bg=current_theme["bg"])
    listbox_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side="right", fill="y")

    servers_listbox = tk.Listbox(listbox_frame, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"],
                                 selectmode="single", yscrollcommand=scrollbar.set, height=10)
    servers_listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=servers_listbox.yview)

    # Buttons frame
    buttons_frame = tk.Frame(tab_servers, bg=current_theme["bg"])
    buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

    def refresh_servers_list():
        servers_listbox.delete(0, tk.END)
        servers = server_manager.get_servers_list()
        for server in servers:
            servers_listbox.insert(tk.END, server)

    def add_server():
        name = simpledialog.askstring("Server Name", "Enter server name:")
        if not name:
            return

        ip = simpledialog.askstring("Server IP", "Enter server IP address:")
        if not ip:
            return

        port = simpledialog.askstring("Server Port", "Enter server port (default: 25565):", initialvalue="25565")
        if not port:
            port = "25565"

        success, message = server_manager.add_server(name, ip, port)
        if success:
            refresh_servers_list()
            append_terminal_callback(f"Server added: {message}")
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def remove_selected_server():
        selection = servers_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server to remove.")
            return

        index = selection[0]
        server_details = server_manager.get_server_details(index)
        if server_details and messagebox.askyesno("Confirm", f"Remove server '{server_details['name']}'?"):
            success, message = server_manager.remove_server(index)
            if success:
                refresh_servers_list()
                append_terminal_callback(message)
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)

    def connect_to_server():
        selection = servers_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server to connect to.")
            return

        index = selection[0]
        server = server_manager.get_server_details(index)
        if server:
            # This would integrate with the launch system to connect to the server
            append_terminal_callback(f"Connecting to server: {server['name']} ({server['ip']}:{server['port']})")
            # For now, just show a message - full integration would require modifying the launch function
            messagebox.showinfo("Connect to Server",
                              f"To connect to {server['name']}, launch Minecraft and use Direct Connect with:\n\n"
                              f"Server Address: {server['ip']}:{server['port']}")

    def ping_selected_server():
        selection = servers_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server to ping.")
            return

        index = selection[0]
        server = server_manager.get_server_details(index)
        if server:
            append_terminal_callback(f"Pinging {server['name']}...")
            online = server_manager.ping_server(server['ip'], server['port'])
            if online:
                append_terminal_callback(f"✓ {server['name']} is online")
                messagebox.showinfo("Server Status", f"{server['name']} is online!")
            else:
                append_terminal_callback(f"✗ {server['name']} is offline or unreachable")
                messagebox.showwarning("Server Status", f"{server['name']} is offline or unreachable")

    # Buttons
    RoundedButton(buttons_frame, text="Add Server", command=add_server,
                  bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    RoundedButton(buttons_frame, text="Remove Selected", command=remove_selected_server,
                  bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    RoundedButton(buttons_frame, text="Connect", command=connect_to_server,
                  bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    RoundedButton(buttons_frame, text="Ping Server", command=ping_selected_server,
                  bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))

    # Initial refresh
    refresh_servers_list()

    return tab_servers

# === jvm_presets.py content ===
JVM_PRESETS = {
    "Default": {
        "args": "",
        "description": "No custom JVM arguments - uses Minecraft defaults"
    },
    "Performance": {
        "args": "-Xmx4G -Xms4G -XX:+UseG1GC -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+UseAdaptiveGCBoundary -XX:MaxGCPauseMillis=100 -XX:+UseStringDeduplication -XX:+UseCompressedOops -XX:+OptimizeStringConcat -XX:+UseFastAccessorMethods",
        "description": "Optimized for performance with G1GC and memory management"
    },
    "Low Memory": {
        "args": "-Xmx2G -Xms1G -XX:+UseSerialGC -XX:+OptimizeStringConcat",
        "description": "Minimal memory usage for low-end systems"
    },
    "High Performance": {
        "args": "-Xmx8G -Xms4G -XX:+UseG1GC -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M -XX:+UseStringDeduplication -XX:+UseCompressedOops -XX:+OptimizeStringConcat -XX:+UseFastAccessorMethods -XX:+AggressiveOpts",
        "description": "High-performance settings for powerful systems with 8GB+ RAM"
    },
    "Debug": {
        "args": "-Xmx4G -Xms2G -XX:+UnlockDiagnosticVMOptions -XX:+DebugNonSafepoints -XX:+PrintGC -XX:+PrintGCDetails -XX:+PrintGCTimeStamps",
        "description": "Debug settings with GC logging for troubleshooting"
    },
    "Server": {
        "args": "-Xmx6G -Xms3G -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+UseCGroupMemoryLimitForHeap -XX:+UseLargePages -XX:LargePageSizeInBytes=2m",
        "description": "Server-optimized settings for dedicated server environments"
    }
}

JVM_ARG_EXPLANATIONS = {
    "-Xmx": "Maximum heap size (e.g., -Xmx4G for 4GB)",
    "-Xms": "Initial heap size (e.g., -Xms2G for 2GB)",
    "-XX:+UseG1GC": "Use G1 Garbage Collector (recommended for most cases)",
    "-XX:+UseSerialGC": "Use Serial Garbage Collector (for low memory systems)",
    "-XX:+UseParallelGC": "Use Parallel Garbage Collector",
    "-XX:+UseConcMarkSweepGC": "Use Concurrent Mark Sweep Garbage Collector",
    "-XX:+UnlockExperimentalVMOptions": "Allow experimental JVM options",
    "-XX:+DisableExplicitGC": "Disable explicit garbage collection calls",
    "-XX:MaxGCPauseMillis": "Maximum GC pause time in milliseconds",
    "-XX:+UseStringDeduplication": "Enable string deduplication to save memory",
    "-XX:+UseCompressedOops": "Use compressed object pointers (64-bit systems)",
    "-XX:+OptimizeStringConcat": "Optimize string concatenation",
    "-XX:+UseFastAccessorMethods": "Use fast accessor methods",
    "-XX:+AggressiveOpts": "Enable aggressive optimizations",
    "-XX:+PrintGC": "Print GC information",
    "-XX:+PrintGCDetails": "Print detailed GC information",
    "-XX:+PrintGCTimeStamps": "Print GC timestamps",
    "-XX:G1NewSizePercent": "Percentage of heap for young generation (G1GC)",
    "-XX:G1ReservePercent": "Reserved heap percentage (G1GC)",
    "-XX:G1HeapRegionSize": "Heap region size for G1GC",
    "-XX:+UseCGroupMemoryLimitForHeap": "Use cgroup memory limits for heap sizing",
    "-XX:+UseLargePages": "Use large pages for better performance",
    "-XX:LargePageSizeInBytes": "Large page size in bytes"
}

class JVMPresetManager:
    def __init__(self, current_jvm_args_var, append_terminal_callback):
        self.current_jvm_args_var = current_jvm_args_var
        self.append_terminal = append_terminal_callback

    def apply_preset(self, preset_name):
        """Apply a JVM preset"""
        if preset_name in JVM_PRESETS:
            preset = JVM_PRESETS[preset_name]
            self.current_jvm_args_var.set(preset["args"])
            self.append_terminal(f"JVM preset '{preset_name}' applied")
            return True
        return False

    def get_preset_description(self, preset_name):
        """Get description for a preset"""
        if preset_name in JVM_PRESETS:
            return JVM_PRESETS[preset_name]["description"]
        return ""

def create_jvm_presets_section(parent, current_jvm_args_var, append_terminal_callback, current_theme):
    """Create JVM presets section for settings tab"""
    jvm_manager = JVMPresetManager(current_jvm_args_var, append_terminal_callback)

    # JVM Presets frame
    presets_frame = tk.LabelFrame(parent, text="JVM Presets", bg=current_theme["bg"], fg=current_theme["fg"])
    presets_frame.pack(fill="x", padx=20, pady=(10, 10))

    # Preset selector
    preset_frame = tk.Frame(presets_frame, bg=current_theme["bg"])
    preset_frame.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(preset_frame, text="Select Preset:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(side="left")

    preset_var = tk.StringVar()
    preset_combo = ttk.Combobox(preset_frame, textvariable=preset_var,
                               values=list(JVM_PRESETS.keys()), state="readonly")
    preset_combo.pack(side="left", padx=(10, 0))
    preset_combo.set("Default")

    # Description label
    desc_label = tk.Label(presets_frame, text="", bg=current_theme["bg"], fg=current_theme["fg"],
                         wraplength=400, justify="left")
    desc_label.pack(anchor="w", padx=10, pady=(0, 5))

    def on_preset_change(*args):
        selected = preset_var.get()
        description = jvm_manager.get_preset_description(selected)
        desc_label.config(text=f"Description: {description}")

    preset_var.trace_add("write", on_preset_change)
    on_preset_change()  # Initialize description

    def apply_preset():
        selected = preset_var.get()
        if jvm_manager.apply_preset(selected):
            messagebox.showinfo("Success", f"JVM preset '{selected}' applied successfully!")
        else:
            messagebox.showerror("Error", "Failed to apply JVM preset.")

    tk.Button(preset_frame, text="Apply Preset", command=apply_preset,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="right", padx=(10, 0))

    # JVM Arguments Help
    help_frame = tk.LabelFrame(presets_frame, text="JVM Arguments Help", bg=current_theme["bg"], fg=current_theme["fg"])
    help_frame.pack(fill="x", padx=10, pady=(5, 10))

    # Scrollable text for explanations
    help_text = tk.Text(help_frame, height=8, wrap="word", bg=current_theme["entry_bg"], fg=current_theme["entry_fg"])
    scrollbar = tk.Scrollbar(help_frame, command=help_text.yview)
    help_text.config(yscrollcommand=scrollbar.set)

    help_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
    scrollbar.pack(side="right", fill="y", pady=5)

    # Insert explanations
    help_text.insert("1.0", "Common JVM Arguments:\n\n")
    for arg, desc in JVM_ARG_EXPLANATIONS.items():
        help_text.insert("end", f"• {arg}: {desc}\n")

    help_text.config(state="disabled")

    return presets_frame

# === backup.py content ===
class BackupManager:
    def __init__(self, minecraft_dir, config_data, append_terminal_callback):
        self.minecraft_dir = minecraft_dir
        self.config_data = config_data
        self.append_terminal = append_terminal_callback
        self.backup_dir = os.path.join(os.path.dirname(minecraft_dir), "launcher_backups")

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, include_mods=True, include_screenshots=True):
        """Create a backup of launcher data"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"launcher_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_name)

            self.append_terminal("Creating backup...")

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup config.json
                config_path = os.path.join(os.path.dirname(self.minecraft_dir), "config.json")
                if os.path.exists(config_path):
                    zipf.write(config_path, "config.json")
                    self.append_terminal("✓ Config backed up")

                # Backup mods if requested
                if include_mods:
                    mods_dir = os.path.join(self.minecraft_dir, "mods")
                    if os.path.exists(mods_dir):
                        for root, dirs, files in os.walk(mods_dir):
                            for file in files:
                                if file.endswith('.jar'):
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.join("mods", os.path.relpath(file_path, mods_dir))
                                    zipf.write(file_path, arcname)
                        self.append_terminal("✓ Mods backed up")

                # Backup screenshots if requested
                if include_screenshots:
                    screenshots_dir = os.path.join(self.minecraft_dir, "screenshots")
                    if os.path.exists(screenshots_dir):
                        for root, dirs, files in os.walk(screenshots_dir):
                            for file in files:
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.join("screenshots", os.path.relpath(file_path, screenshots_dir))
                                    zipf.write(file_path, arcname)
                        self.append_terminal("✓ Screenshots backed up")

                # Create backup info file
                backup_info = {
                    "timestamp": timestamp,
                    "minecraft_version": self.config_data.get("last_version", "unknown"),
                    "launcher_version": self.config_data.get("launcher_version", "unknown"),
                    "included_mods": include_mods,
                    "included_screenshots": include_screenshots
                }
                zipf.writestr("backup_info.json", json.dumps(backup_info, indent=2))

            self.append_terminal(f"Backup created: {backup_name}")
            return backup_path

        except Exception as e:
            self.append_terminal(f"Failed to create backup: {e}")
            return None

    def restore_backup(self, backup_path):
        """Restore from a backup"""
        try:
            self.append_terminal("Restoring from backup...")

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Check backup info
                if "backup_info.json" in zipf.namelist():
                    with zipf.open("backup_info.json") as f:
                        backup_info = json.load(f)
                        self.append_terminal(f"Restoring backup from {backup_info.get('timestamp', 'unknown')}")

                # Restore config.json
                if "config.json" in zipf.namelist():
                    extract_path = os.path.join(os.path.dirname(self.minecraft_dir), "config.json")
                    with zipf.open("config.json") as source, open(extract_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    self.append_terminal("✓ Config restored")

                # Restore mods
                mods_dir = os.path.join(self.minecraft_dir, "mods")
                os.makedirs(mods_dir, exist_ok=True)

                for item in zipf.namelist():
                    if item.startswith("mods/") and item.endswith('.jar'):
                        extract_path = os.path.join(self.minecraft_dir, item)
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                        with zipf.open(item) as source, open(extract_path, 'wb') as target:
                            shutil.copyfileobj(source, target)

                if any(item.startswith("mods/") for item in zipf.namelist()):
                    self.append_terminal("✓ Mods restored")

                # Restore screenshots
                for item in zipf.namelist():
                    if item.startswith("screenshots/"):
                        extract_path = os.path.join(self.minecraft_dir, item)
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                        with zipf.open(item) as source, open(extract_path, 'wb') as target:
                            shutil.copyfileobj(source, target)

                if any(item.startswith("screenshots/") for item in zipf.namelist()):
                    self.append_terminal("✓ Screenshots restored")

            self.append_terminal("Backup restored successfully!")
            return True

        except Exception as e:
            self.append_terminal(f"Failed to restore backup: {e}")
            return False

    def list_backups(self):
        """List available backups"""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith("launcher_backup_") and file.endswith(".zip"):
                file_path = os.path.join(self.backup_dir, file)
                backups.append({
                    "name": file,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "date": datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                })

        # Sort by date (newest first)
        backups.sort(key=lambda x: x["date"], reverse=True)
        return backups

def create_backup_section(parent, minecraft_dir, config_data, append_terminal_callback, current_theme):
    """Create backup/restore section for settings tab"""
    backup_manager = BackupManager(minecraft_dir, config_data, append_terminal_callback)

    # Backup section frame
    backup_frame = tk.LabelFrame(parent, text="Backup & Restore", bg=current_theme["bg"], fg=current_theme["fg"])
    backup_frame.pack(fill="x", padx=20, pady=(10, 10))

    # Backup options
    options_frame = tk.Frame(backup_frame, bg=current_theme["bg"])
    options_frame.pack(fill="x", padx=10, pady=(10, 5))

    include_mods_var = tk.BooleanVar(value=True)
    include_screenshots_var = tk.BooleanVar(value=True)

    tk.Checkbutton(options_frame, text="Include Mods", variable=include_mods_var,
                   bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w")
    tk.Checkbutton(options_frame, text="Include Screenshots", variable=include_screenshots_var,
                   bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w")

    def create_backup():
        include_mods = include_mods_var.get()
        include_screenshots = include_screenshots_var.get()

        backup_path = backup_manager.create_backup(include_mods, include_screenshots)
        if backup_path:
            messagebox.showinfo("Success", f"Backup created successfully!\n\nSaved to: {backup_path}")
        else:
            messagebox.showerror("Error", "Failed to create backup.")

    def restore_backup():
        backup_path = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("Zip files", "*.zip")],
            initialdir=backup_manager.backup_dir
        )

        if backup_path:
            if messagebox.askyesno("Confirm Restore",
                                 "This will overwrite your current config and mods.\n\n"
                                 "Are you sure you want to restore from this backup?"):
                if backup_manager.restore_backup(backup_path):
                    messagebox.showinfo("Success", "Backup restored successfully!\n\nPlease restart the launcher.")
                else:
                    messagebox.showerror("Error", "Failed to restore backup.")

    def open_backups_folder():
        try:
            os.startfile(backup_manager.backup_dir)
        except Exception as e:
            append_terminal_callback(f"Error opening backups folder: {e}")
            messagebox.showerror("Error", f"Failed to open backups folder: {e}")

    # Buttons
    buttons_frame = tk.Frame(backup_frame, bg=current_theme["bg"])
    buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

    tk.Button(buttons_frame, text="Create Backup", command=create_backup,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    tk.Button(buttons_frame, text="Restore Backup", command=restore_backup,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left", padx=(0, 10))
    tk.Button(buttons_frame, text="Open Backups Folder", command=open_backups_folder,
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(side="left")

    return backup_frame

# === Setup UI ===
current_theme_name = config_data.get("theme", "dark")
current_theme = THEMES.get(current_theme_name, THEMES["dark"])

root = tk.Tk()
root.title(f"{LAUNCHER_NAME} v{LAUNCHER_VERSION}")
root.geometry("700x650")
root.configure(bg=current_theme["bg"])
root.resizable(True, True)

if os.path.exists(ICON):
    root.iconbitmap(ICON)

# === Variables ===
username_var = tk.StringVar(value=config_data.get("saved_username", ""))
version_var = tk.StringVar()
jvm_args_var = tk.StringVar(value=config_data.get("jvm_args", ""))
auto_save_var = tk.BooleanVar(value=config_data.get("auto_save", True))
save_username_var = tk.BooleanVar(value=config_data.get("save_username", True))
theme_var = tk.StringVar(value=current_theme_name)
custom_button_bg_var = tk.StringVar(value=config_data.get("custom_button_bg", ""))
custom_button_fg_var = tk.StringVar(value=config_data.get("custom_button_fg", ""))
progress_var = tk.DoubleVar()

# === Internationalization ===
def load_language(lang_code):
    lang_file = os.path.join(SCRIPT_DIR, "lang", f"{lang_code}.json")
    if os.path.exists(lang_file):
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

current_language_code = config_data.get("language", "en")
lang_strings = load_language(current_language_code)

def translate(key):
    return lang_strings.get(key, key)

# === Tabs ===
tabs = ttk.Notebook(root)
tab_launcher = tk.Frame(tabs, bg=current_theme["bg"])
tab_terminal = tk.Frame(tabs, bg=current_theme["bg"])
tab_settings = tk.Frame(tabs, bg=current_theme["bg"])
tab_mods = tk.Frame(tabs, bg=current_theme["bg"])
tab_servers = tk.Frame(tabs, bg=current_theme["bg"])
tabs.add(tab_launcher, text="Launcher")
tabs.add(tab_mods, text="Mods")
tabs.add(tab_servers, text="Servers")
tabs.add(tab_terminal, text="Terminal")
tabs.add(tab_settings, text="Settings")
tabs.pack(expand=1, fill="both")

# === Scrollable Launcher Tab ===
launcher_canvas = tk.Canvas(tab_launcher, bg=current_theme["bg"], highlightthickness=0)
launcher_scrollbar = tk.Scrollbar(tab_launcher, orient="vertical", command=launcher_canvas.yview)
launcher_scrollable_frame = tk.Frame(launcher_canvas, bg=current_theme["bg"])

launcher_scrollable_frame.bind(
    "<Configure>",
    lambda e: launcher_canvas.configure(scrollregion=launcher_canvas.bbox("all"))
)

launcher_canvas.create_window((0, 0), window=launcher_scrollable_frame, anchor="nw")
launcher_canvas.configure(yscrollcommand=launcher_scrollbar.set)

launcher_canvas.pack(side="left", fill="both", expand=True)
launcher_scrollbar.pack(side="right", fill="y")

# Bind mousewheel to launcher canvas
def _on_launcher_mousewheel(event):
    launcher_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

launcher_canvas.bind_all("<MouseWheel>", _on_launcher_mousewheel)

# === Scrollable Settings Tab ===
settings_canvas = tk.Canvas(tab_settings, bg=current_theme["bg"], highlightthickness=0)
settings_scrollbar = tk.Scrollbar(tab_settings, orient="vertical", command=settings_canvas.yview)
settings_scrollable_frame = tk.Frame(settings_canvas, bg=current_theme["bg"])

settings_scrollable_frame.bind(
    "<Configure>",
    lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
)

settings_canvas.create_window((0, 0), window=settings_scrollable_frame, anchor="nw")
settings_canvas.configure(yscrollcommand=settings_scrollbar.set)

settings_canvas.pack(side="left", fill="both", expand=True)
settings_scrollbar.pack(side="right", fill="y")

# Bind mousewheel to canvas
def _on_mousewheel(event):
    settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

settings_canvas.bind_all("<MouseWheel>", _on_mousewheel)

# === Terminal ===
terminal_output = tk.Text(tab_terminal, bg="#111", fg="#ccc", state="disabled", height=20, font=("Consolas", 10))
terminal_output.pack(expand=1, fill="both", padx=10, pady=10)

# Add Clear Terminal button
RoundedButton(tab_terminal, text="Clear Terminal", command=clear_terminal).pack(pady=5)

# === Launcher Tab ===
tk.Label(launcher_scrollable_frame, text="Username:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(padx=20, pady=(20, 5), anchor="w")
tk.Entry(launcher_scrollable_frame, textvariable=username_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"], font=current_theme["font_main"]).pack(fill="x", padx=20)

tk.Checkbutton(launcher_scrollable_frame, text=translate("remember_username"), variable=save_username_var,
               bg=current_theme["bg"], fg=current_theme["fg"], selectcolor=current_theme["bg"],
               font=current_theme["font_main"]).pack(anchor="w", padx=20, pady=5)

# Add Clear Cache and Open Minecraft Folder buttons
def clear_cache():
    cache_dir = os.path.join(MINECRAFT_DIR, "cache")
    if os.path.exists(cache_dir):
        try:
            for root_dir, dirs, files in os.walk(cache_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root_dir, name))
                for name in dirs:
                    os.rmdir(os.path.join(root_dir, name))
            os.rmdir(cache_dir)
            append_terminal("Cache cleared successfully.")
            messagebox.showinfo("Clear Cache", "Cache cleared successfully.")
        except Exception as e:
            append_terminal(f"Error clearing cache: {e}")
            messagebox.showerror("Clear Cache Error", str(e))
    else:
        messagebox.showinfo("Clear Cache", "No cache directory found.")

def open_minecraft_folder():
    try:
        os.startfile(MINECRAFT_DIR)
    except Exception as e:
        append_terminal(f"Error opening Minecraft folder: {e}")
        messagebox.showerror("Open Folder Error", str(e))

RoundedButton(launcher_scrollable_frame, text=translate("clear_cache"), command=clear_cache).pack(pady=5)
RoundedButton(launcher_scrollable_frame, text=translate("open_minecraft_folder"), command=open_minecraft_folder).pack(pady=5)

# === Version Selector ===
tk.Label(tab_launcher, text="Minecraft Version:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(15, 5))

def get_versions():
    try:
        return [v["id"] for v in minecraft_launcher_lib.utils.get_available_versions(MINECRAFT_DIR)]
    except:
        return ["1.20.1", "1.19.4"]

versions = get_versions()
version_var.set(versions[0])
ttk.Combobox(tab_launcher, textvariable=version_var, values=versions, state="readonly").pack(fill="x", padx=20)

# === Progress Bar ===
tk.Label(tab_launcher, text="Installation Progress:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(15, 5))
progress_bar = ttk.Progressbar(tab_launcher, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=20, pady=(0, 10))

# === Skin Preview ===
skin_label = tk.Label(tab_launcher, text="No Skin", bg=current_theme["bg"], fg=current_theme["fg"])
skin_label.pack(pady=10)

def fetch_skin(username):
    if not username:
        skin_label.config(image="", text="No Skin")
        return
    try:
        url = f"https://minotar.net/avatar/{username}/64.png"
        img_data = requests.get(url).content
        img = Image.open(io.BytesIO(img_data)).resize((64, 64))
        photo = ImageTk.PhotoImage(img)
        skin_label.photo = photo
        skin_label.config(image=photo, text="")
    except:
        skin_label.config(image="", text="Skin Load Failed")

# Fix skin preview update on username change
def on_username_change(*args):
    if not selected_skin_path:
        fetch_skin(username_var.get())

username_var.trace_add("write", on_username_change)

RoundedButton(tab_launcher, text="Choose Custom Skin", command=lambda: choose_skin()).pack()
RoundedButton(tab_launcher, text="Clear Skin", command=lambda: clear_skin()).pack()

def choose_skin():
    global selected_skin_path
    path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
    if path:
        selected_skin_path = path
        img = Image.open(path).resize((64, 64))
        photo = ImageTk.PhotoImage(img)
        skin_label.photo = photo
        skin_label.config(image=photo)

def clear_skin():
    global selected_skin_path
    selected_skin_path = None
    fetch_skin(username_var.get())

# === Microsoft Login ===
def microsoft_login():
    def do_login():
        try:
            # Check network connectivity first
            try:
                requests.get("https://login.microsoftonline.com", timeout=5)
                append_terminal("Network connectivity check passed.")
            except requests.exceptions.RequestException:
                messagebox.showerror("Network Error", "Unable to connect to Microsoft servers. Please check your internet connection.")
                return

            client_id = "00000000402b5328"
            redirect_uri = "https://login.microsoftonline.com/common/oauth2/nativeclient"
            login_url = minecraft_launcher_lib.microsoft_account.get_login_url(client_id, redirect_uri)
            webbrowser.open(login_url)
            append_terminal("Browser opened for Microsoft login.")
            messagebox.showinfo("Microsoft Login", "A browser window has opened. Please login with your Microsoft account. After login, you will be redirected. Copy the url from the address bar and paste it here.")
            url = simpledialog.askstring("Enter URL", "Paste the url you were redirected to:")
            if url and minecraft_launcher_lib.microsoft_account.url_contains_auth_code(url):
                auth_code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(url, redirect_uri)
                login_data = minecraft_launcher_lib.microsoft_account.complete_login(client_id, None, redirect_uri, auth_code)
                config_data["microsoft_login"] = login_data
                save_json(CONFIG_FILE, config_data)
                username_var.set(login_data["name"])
                append_terminal(f"Successfully logged in as {login_data['name']}")
                messagebox.showinfo("Login Success", f"Logged in as {login_data['name']}")
            else:
                append_terminal("Invalid url or no auth code found.")
                messagebox.showerror("Login Failed", "Invalid url or no auth code found.")
        except Exception as e:
            append_terminal(f"Microsoft login failed: {str(e)}")
            messagebox.showerror("Login Error", f"Login failed: {str(e)}")

    threading.Thread(target=do_login, daemon=True).start()

RoundedButton(tab_launcher, text="Microsoft Login", command=microsoft_login).pack(pady=10)

# === Launch ===
def launch():
    username = username_var.get().strip()
    if not username:
        messagebox.showerror("Error", "Username is required.")
        return

    if save_username_var.get():
        config_data["saved_username"] = username
    else:
        config_data.pop("saved_username", None)
    config_data["save_username"] = save_username_var.get()
    config_data["jvm_args"] = jvm_args_var.get()
    config_data["theme"] = theme_var.get()
    save_json(CONFIG_FILE, config_data)

    def run():
        try:
            version = version_var.get()
            append_terminal(f"Preparing to launch Minecraft {version}...")

            # Check if version is already installed
            installed_versions = minecraft_launcher_lib.utils.get_installed_versions(MINECRAFT_DIR)
            installed_version_ids = [v['id'] for v in installed_versions]
            if version not in installed_version_ids:
                append_terminal("Version not installed. Starting download...")
                progress_var.set(0)  # Reset progress bar

                # Create progress callback
                def progress_callback(current, total):
                    if total > 0:
                        progress = int((current / total) * 100)
                        progress_var.set(progress)  # Update progress bar
                        append_terminal(f"Download progress: {progress}% ({current}/{total} bytes)")

                # Install with progress callback
                minecraft_launcher_lib.install.install_minecraft_version(
                    version,
                    MINECRAFT_DIR,
                    callback={"setStatus": lambda status: append_terminal(f"Status: {status}"),
                             "setProgress": progress_callback,
                             "setMax": lambda max_val: append_terminal(f"Total size: {max_val} bytes")}
                )
                progress_var.set(100)  # Set to complete
                append_terminal("Installation completed!")
            else:
                append_terminal("Version already installed. Skipping download.")

            # Prepare login options
            if "microsoft_login" in config_data:
                login = config_data["microsoft_login"]
                try:
                    valid = minecraft_launcher_lib.microsoft_account.validate_login(login)
                    if not valid:
                        append_terminal("Refreshing Microsoft login token...")
                        refreshed = minecraft_launcher_lib.microsoft_account.refresh_login(login)
                        config_data["microsoft_login"] = refreshed
                        save_json(CONFIG_FILE, config_data)
                        login = refreshed
                        append_terminal("Microsoft login token refreshed successfully.")
                except Exception as e:
                    append_terminal(f"Failed to refresh Microsoft login: {e}. Falling back to offline mode.")
                    config_data.pop("microsoft_login", None)
                    save_json(CONFIG_FILE, config_data)
                    login = None
                if login:
                    options = {
                        "username": login["name"],
                        "uuid": login["uuid"],
                        "token": login["access_token"],
                        "launcherName": LAUNCHER_NAME,
                        "launcherVersion": LAUNCHER_VERSION,
                    }
                    append_terminal(f"Using Microsoft account: {login['name']}")
                else:
                    options = {
                        "username": username,
                        "uuid": offline_uuid(username),
                        "token": "",
                        "launcherName": LAUNCHER_NAME,
                        "launcherVersion": LAUNCHER_VERSION,
                    }
                    append_terminal("Using offline mode")
            else:
                options = {
                    "username": username,
                    "uuid": offline_uuid(username),
                    "token": "",
                    "launcherName": LAUNCHER_NAME,
                    "launcherVersion": LAUNCHER_VERSION,
                }
                append_terminal("Using offline mode")

            append_terminal("Generating launch command...")
            command = minecraft_launcher_lib.command.get_minecraft_command(version, MINECRAFT_DIR, options)
            jvm = jvm_args_var.get().strip().split()
            if jvm:
                command = command[:1] + jvm + command[1:]
                append_terminal(f"JVM arguments applied: {' '.join(jvm)}")

            append_terminal("Launching Minecraft...")
            append_terminal(f"Command: {' '.join(command)}")
            subprocess.Popen(command, cwd=MINECRAFT_DIR)
            append_terminal("Minecraft launched successfully!")

        except Exception as e:
            append_terminal(f"Launch failed: {traceback.format_exc()}")
            messagebox.showerror("Launch Error", str(e))

    threading.Thread(target=run, daemon=True).start()

RoundedButton(tab_launcher, text="Launch Minecraft", command=launch).pack(pady=15)

# === Settings Tab ===
tk.Label(settings_scrollable_frame, text="JVM Arguments:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w", padx=20, pady=(20, 5))
tk.Entry(settings_scrollable_frame, textvariable=jvm_args_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"], font=current_theme["font_main"]).pack(fill="x", padx=20)

tk.Label(settings_scrollable_frame, text="Theme:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w", padx=20, pady=(20, 5))
ttk.Combobox(settings_scrollable_frame, textvariable=theme_var, values=list(THEMES.keys()), state="readonly").pack(fill="x", padx=20)

tk.Checkbutton(settings_scrollable_frame, text="Auto Save Settings", variable=auto_save_var, bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w", padx=20, pady=10)

# Add language selector
language_var = tk.StringVar(value=current_language_code)
tk.Label(settings_scrollable_frame, text="Language:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w", padx=20, pady=(10, 5))
ttk.Combobox(settings_scrollable_frame, textvariable=language_var, values=[os.path.splitext(f)[0] for f in os.listdir(os.path.join(SCRIPT_DIR, "lang")) if f.endswith(".json")], state="readonly").pack(fill="x", padx=20)

tk.Label(settings_scrollable_frame, text="Custom Button Background Color:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w", padx=20, pady=(10, 5))
tk.Entry(settings_scrollable_frame, textvariable=custom_button_bg_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"], font=current_theme["font_main"]).pack(fill="x", padx=20)

tk.Label(settings_scrollable_frame, text="Custom Button Foreground Color:", bg=current_theme["bg"], fg=current_theme["fg"]).pack(anchor="w", padx=20, pady=(10, 5))
tk.Entry(settings_scrollable_frame, textvariable=custom_button_fg_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"], font=current_theme["font_main"]).pack(fill="x", padx=20)

def restart_launcher():
    config_data["jvm_args"] = jvm_args_var.get()
    config_data["theme"] = theme_var.get()
    config_data["auto_save"] = auto_save_var.get()
    config_data["language"] = language_var.get()
    config_data["custom_button_bg"] = custom_button_bg_var.get()
    config_data["custom_button_fg"] = custom_button_fg_var.get()
    save_json(CONFIG_FILE, config_data)
    # Auto restart
    subprocess.Popen([sys.executable, "combined_launcher.py"])
    root.destroy()

RoundedButton(settings_scrollable_frame, text="Apply & Auto Restart", command=restart_launcher).pack(pady=10)

# === Changelog feature ===
CHANGELOG_FILE = "CHANGELOG.md"

def show_changelog():
    if not os.path.exists(CHANGELOG_FILE):
        messagebox.showinfo("Changelog", "No changelog available.")
        return
    with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
        changelog_text = f.read()
    changelog_window = tk.Toplevel(root)
    changelog_window.title("Changelog")
    changelog_window.geometry("600x400")
    text_widget = tk.Text(changelog_window, wrap="word")
    text_widget.insert("1.0", changelog_text)
    text_widget.config(state="disabled")
    text_widget.pack(expand=1, fill="both")
    RoundedButton(changelog_window, text="Close", command=changelog_window.destroy).pack(pady=5)

# === Check for Library Updates ===
def check_library_updates():
    def do_check():
        try:
            append_terminal("Checking for minecraft_launcher_lib updates...")
            # Try to get the latest version from PyPI
            response = requests.get("https://pypi.org/pypi/minecraft-launcher-lib/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_version = data["info"]["version"]
                current_version = getattr(minecraft_launcher_lib, "__version__", "unknown")

                append_terminal(f"Current version: {current_version}")
                append_terminal(f"Latest version: {latest_version}")

                if current_version != latest_version and current_version != "unknown":
                    messagebox.showinfo("Update Available",
                        f"A new version of minecraft_launcher_lib is available!\n\n"
                        f"Current: {current_version}\n"
                        f"Latest: {latest_version}\n\n"
                        "Please update using: pip install --upgrade minecraft-launcher-lib")
                else:
                    messagebox.showinfo("Up to Date", "minecraft_launcher_lib is up to date.")
            else:
                append_terminal("Failed to check for updates from PyPI.")
                messagebox.showwarning("Check Failed", "Unable to check for updates. Please check your internet connection.")
        except Exception as e:
            append_terminal(f"Error checking for updates: {e}")
            messagebox.showerror("Update Check Error", f"Failed to check for updates: {str(e)}")

    threading.Thread(target=do_check, daemon=True).start()

RoundedButton(settings_scrollable_frame, text="Check for Library Updates", command=check_library_updates).pack(pady=5)

RoundedButton(settings_scrollable_frame, text=translate("view_changelog"), command=show_changelog).pack(pady=10)

# === Mods Tab ===
create_mods_tab(tab_mods, MINECRAFT_DIR, config_data, append_terminal, current_theme, save_config)

# === Servers Tab ===
create_servers_tab(tab_servers, config_data, append_terminal, current_theme, launch)

# === Profile Management Section ===
tk.Label(settings_scrollable_frame, text="Profile Management:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

profile_var = tk.StringVar()
profile_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
profile_frame.pack(fill="x", padx=20, pady=5)

tk.Entry(profile_frame, textvariable=profile_var, bg=current_theme["entry_bg"], fg=current_theme["entry_fg"], font=current_theme["font_main"]).pack(side="left", fill="x", expand=True)

def save_profile():
    profile_name = profile_var.get().strip()
    if not profile_name:
        messagebox.showerror("Error", "Profile name is required.")
        return

    profile_data = {
        "username": username_var.get(),
        "version": version_var.get(),
        "jvm_args": jvm_args_var.get(),
        "theme": theme_var.get(),
        "language": language_var.get(),
        "custom_button_bg": custom_button_bg_var.get(),
        "custom_button_fg": custom_button_fg_var.get(),
        "auto_save": auto_save_var.get(),
        "save_username": save_username_var.get()
    }

    profiles_dir = "profiles"
    if not os.path.exists(profiles_dir):
        os.makedirs(profiles_dir)

    profile_file = os.path.join(profiles_dir, f"{profile_name}.json")
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=4)

    append_terminal(f"Profile '{profile_name}' saved successfully.")
    messagebox.showinfo("Profile Saved", f"Profile '{profile_name}' saved successfully.")

def load_profile():
    profile_name = profile_var.get().strip()
    if not profile_name:
        messagebox.showerror("Error", "Profile name is required.")
        return

    profile_file = os.path.join("profiles", f"{profile_name}.json")
    if not os.path.exists(profile_file):
        messagebox.showerror("Error", f"Profile '{profile_name}' not found.")
        return

    with open(profile_file, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    # Load profile data into variables
    username_var.set(profile_data.get("username", ""))
    version_var.set(profile_data.get("version", version_var.get()))
    jvm_args_var.set(profile_data.get("jvm_args", ""))
    theme_var.set(profile_data.get("theme", "dark"))
    language_var.set(profile_data.get("language", "en"))
    custom_button_bg_var.set(profile_data.get("custom_button_bg", ""))
    custom_button_fg_var.set(profile_data.get("custom_button_fg", ""))
    auto_save_var.set(profile_data.get("auto_save", True))
    save_username_var.set(profile_data.get("save_username", True))

    append_terminal(f"Profile '{profile_name}' loaded successfully.")
    messagebox.showinfo("Profile Loaded", f"Profile '{profile_name}' loaded successfully.")

def list_profiles():
    profiles_dir = "profiles"
    if not os.path.exists(profiles_dir):
        messagebox.showinfo("Profiles", "No profiles found.")
        return

    profiles = [f[:-5] for f in os.listdir(profiles_dir) if f.endswith(".json")]
    if not profiles:
        messagebox.showinfo("Profiles", "No profiles found.")
        return

    profile_list = "\n".join(profiles)
    messagebox.showinfo("Available Profiles", f"Available profiles:\n{profile_list}")

RoundedButton(profile_frame, text="Save Profile", command=save_profile).pack(side="left", padx=(5, 0))
RoundedButton(profile_frame, text="Load Profile", command=load_profile).pack(side="left", padx=(5, 0))
RoundedButton(profile_frame, text="List Profiles", command=list_profiles).pack(side="left", padx=(5, 0))

# === Configuration Export/Import Section ===
tk.Label(settings_scrollable_frame, text="Configuration Export/Import:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

config_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
config_frame.pack(fill="x", padx=20, pady=5)

def export_config():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            append_terminal("Configuration exported successfully.")
            messagebox.showinfo("Export Successful", "Configuration exported successfully.")
        except Exception as e:
            append_terminal(f"Error exporting configuration: {e}")
            messagebox.showerror("Export Error", str(e))

def import_config():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_config = json.load(f)

            # Update config_data with imported data
            config_data.update(imported_config)
            save_json(CONFIG_FILE, config_data)

            # Update UI variables
            username_var.set(config_data.get("saved_username", ""))
            jvm_args_var.set(config_data.get("jvm_args", ""))
            theme_var.set(config_data.get("theme", "dark"))
            language_var.set(config_data.get("language", "en"))
            custom_button_bg_var.set(config_data.get("custom_button_bg", ""))
            custom_button_fg_var.set(config_data.get("custom_button_fg", ""))
            auto_save_var.set(config_data.get("auto_save", True))
            save_username_var.set(config_data.get("save_username", True))

            append_terminal("Configuration imported successfully.")
            messagebox.showinfo("Import Successful", "Configuration imported successfully. Please restart the launcher to apply all changes.")
        except Exception as e:
            append_terminal(f"Error importing configuration: {e}")
            messagebox.showerror("Import Error", str(e))

RoundedButton(config_frame, text="Export Config", command=export_config).pack(side="left", padx=(5, 0))
RoundedButton(config_frame, text="Import Config", command=import_config).pack(side="left", padx=(5, 0))

# === System Information Section ===
tk.Label(settings_scrollable_frame, text="System Information:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

system_info_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
system_info_frame.pack(fill="x", padx=20, pady=5)

def show_system_info():
    import platform
    import psutil

    try:
        # Get system information
        python_version = platform.python_version()
        minecraft_lib_version = getattr(minecraft_launcher_lib, "__version__", "unknown")
        os_info = f"{platform.system()} {platform.release()}"
        cpu_info = platform.processor() or "Unknown"
        memory_info = f"{psutil.virtual_memory().total // (1024**3)} GB"

        info_text = f"""
Python Version: {python_version}
Minecraft Launcher Lib Version: {minecraft_lib_version}
Operating System: {os_info}
Processor: {cpu_info}
Total Memory: {memory_info}
Minecraft Directory: {MINECRAFT_DIR}
Launcher Version: {LAUNCHER_VERSION}
"""

        messagebox.showinfo("System Information", info_text.strip())
    except ImportError:
        # Fallback if psutil is not available
        python_version = platform.python_version()
        minecraft_lib_version = getattr(minecraft_launcher_lib, "__version__", "unknown")
        os_info = f"{platform.system()} {platform.release()}"

        info_text = f"""
Python Version: {python_version}
Minecraft Launcher Lib Version: {minecraft_lib_version}
Operating System: {os_info}
Minecraft Directory: {MINECRAFT_DIR}
Launcher Version: {LAUNCHER_VERSION}
"""

        messagebox.showinfo("System Information", info_text.strip())

RoundedButton(system_info_frame, text="Show System Info", command=show_system_info).pack(side="left", padx=(5, 0))

# === Installed Versions Section ===
tk.Label(settings_scrollable_frame, text="Installed Versions:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

versions_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
versions_frame.pack(fill="x", padx=20, pady=5)

def show_installed_versions():
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(MINECRAFT_DIR)
        if not installed_versions:
            messagebox.showinfo("Installed Versions", "No Minecraft versions are currently installed.")
            return

        versions_list = "\n".join([f"{v['id']} ({v.get('type', 'unknown')})" for v in installed_versions])
        messagebox.showinfo("Installed Versions", f"Installed Minecraft versions:\n\n{versions_list}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get installed versions: {str(e)}")

def remove_version():
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(MINECRAFT_DIR)
        if not installed_versions:
            messagebox.showinfo("Installed Versions", "No Minecraft versions are currently installed.")
            return

        version_names = [v["id"] for v in installed_versions]
        version_to_remove = simpledialog.askstring("Remove Version", f"Select version to remove:\n\n{chr(10).join(version_names)}")

        if version_to_remove and version_to_remove in version_names:
            confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove Minecraft version '{version_to_remove}'?\n\nThis action cannot be undone.")
            if confirm:
                try:
                    minecraft_launcher_lib.utils.delete_version(version_to_remove, MINECRAFT_DIR)
                    append_terminal(f"Version '{version_to_remove}' removed successfully.")
                    messagebox.showinfo("Success", f"Minecraft version '{version_to_remove}' has been removed.")
                except Exception as e:
                    append_terminal(f"Failed to remove version '{version_to_remove}': {str(e)}")
                    messagebox.showerror("Error", f"Failed to remove version: {str(e)}")
        elif version_to_remove:
            messagebox.showerror("Error", "Invalid version selected.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get installed versions: {str(e)}")

RoundedButton(versions_frame, text="Show Installed", command=show_installed_versions).pack(side="left", padx=(5, 0))
RoundedButton(versions_frame, text="Remove Version", command=remove_version).pack(side="left", padx=(5, 0))

# === Disk Usage Section ===
tk.Label(settings_scrollable_frame, text="Disk Usage:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

disk_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
disk_frame.pack(fill="x", padx=20, pady=5)

def get_directory_size(path):
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
    except (OSError, IOError):
        pass
    return total_size

def format_size(bytes_size):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} GB"

def show_disk_usage():
    try:
        minecraft_size = get_directory_size(MINECRAFT_DIR)
        formatted_size = format_size(minecraft_size)

        # Get breakdown by subdirectories
        breakdown = []
        try:
            for item in os.listdir(MINECRAFT_DIR):
                item_path = os.path.join(MINECRAFT_DIR, item)
                if os.path.isdir(item_path):
                    item_size = get_directory_size(item_path)
                    if item_size > 0:
                        breakdown.append(f"{item}: {format_size(item_size)}")
        except (OSError, IOError):
            pass

        breakdown_text = "\n".join(breakdown) if breakdown else "Unable to calculate breakdown"

        info_text = f"""Minecraft Directory Size: {formatted_size}

Breakdown by folder:
{breakdown_text}

Location: {MINECRAFT_DIR}"""

        messagebox.showinfo("Disk Usage", info_text)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to calculate disk usage: {str(e)}")

def clean_temp_files():
    """Clean temporary and cache files to free up space."""
    try:
        cleaned_size = 0
        temp_dirs = [
            os.path.join(MINECRAFT_DIR, "cache"),
            os.path.join(MINECRAFT_DIR, "temp"),
            os.path.join(MINECRAFT_DIR, "natives"),
        ]

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for root_dir, dirs, files in os.walk(temp_dir, topdown=False):
                        for name in files:
                            file_path = os.path.join(root_dir, name)
                            try:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned_size += size
                            except (OSError, IOError):
                                pass
                        for name in dirs:
                            try:
                                os.rmdir(os.path.join(root_dir, name))
                            except (OSError, IOError):
                                pass
                    # Try to remove the temp directory itself if empty
                    try:
                        os.rmdir(temp_dir)
                    except (OSError, IOError):
                        pass
                except (OSError, IOError):
                    pass

        if cleaned_size > 0:
            append_terminal(f"Cleaned {format_size(cleaned_size)} of temporary files.")
            messagebox.showinfo("Cleanup Complete", f"Successfully cleaned {format_size(cleaned_size)} of temporary files.")
        else:
            messagebox.showinfo("Cleanup Complete", "No temporary files found to clean.")
    except Exception as e:
        append_terminal(f"Error during cleanup: {str(e)}")
        messagebox.showerror("Cleanup Error", f"Failed to clean temporary files: {str(e)}")

RoundedButton(disk_frame, text="Show Disk Usage", command=show_disk_usage).pack(side="left", padx=(5, 0))
RoundedButton(disk_frame, text="Clean Temp Files", command=clean_temp_files).pack(side="left", padx=(5, 0))

# === Performance Monitoring Section ===
tk.Label(settings_scrollable_frame, text="Performance Monitoring:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

performance_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
performance_frame.pack(fill="x", padx=20, pady=5)

def show_performance_stats():
    """Show performance statistics for the launcher."""
    try:
        import psutil
        import platform

        # Get current process info
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent(interval=1)

        # System info
        system_memory = psutil.virtual_memory()
        system_memory_used = system_memory.used / 1024 / 1024 / 1024  # GB
        system_memory_total = system_memory.total / 1024 / 1024 / 1024  # GB

        # Disk usage for Minecraft directory
        minecraft_size = get_directory_size(MINECRAFT_DIR) / 1024 / 1024 / 1024  # GB

        info_text = f"""Launcher Performance Stats:

Memory Usage: {memory_usage:.1f} MB
CPU Usage: {cpu_percent:.1f}%

System Memory: {system_memory_used:.1f} GB / {system_memory_total:.1f} GB ({system_memory.percent:.1f}%)

Minecraft Directory Size: {minecraft_size:.2f} GB

Platform: {platform.system()} {platform.release()}
Python Version: {platform.python_version()}"""

        messagebox.showinfo("Performance Stats", info_text)
    except ImportError:
        messagebox.showerror("Error", "psutil module is required for performance monitoring.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get performance stats: {str(e)}")

def optimize_launcher():
    """Perform basic optimization tasks."""
    try:
        optimizations = []

        # Clear Python cache files
        cache_cleared = 0
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.pyc', '.pyo', '__pycache__')):
                    try:
                        if file == '__pycache__':
                            import shutil
                            shutil.rmtree(os.path.join(root, file))
                        else:
                            os.remove(os.path.join(root, file))
                        cache_cleared += 1
                    except:
                        pass

        if cache_cleared > 0:
            optimizations.append(f"Cleared {cache_cleared} Python cache files")

        # Clean temp files
        temp_cleaned = clean_temp_files()
        if temp_cleaned:
            optimizations.append("Cleaned temporary files")

        if optimizations:
            messagebox.showinfo("Optimization Complete", "Optimizations performed:\n\n" + "\n".join(optimizations))
        else:
            messagebox.showinfo("Optimization Complete", "No optimizations were needed.")

    except Exception as e:
        messagebox.showerror("Optimization Error", f"Failed to perform optimizations: {str(e)}")

RoundedButton(performance_frame, text="Show Performance", command=show_performance_stats).pack(side="left", padx=(5, 0))
RoundedButton(performance_frame, text="Optimize Launcher", command=optimize_launcher).pack(side="left", padx=(5, 0))

# === Network Diagnostics Section ===
tk.Label(settings_scrollable_frame, text="Network Diagnostics:", bg=current_theme["bg"], fg=current_theme["fg"], font=current_theme["font_bold"]).pack(anchor="w", padx=20, pady=(20, 5))

network_frame = tk.Frame(settings_scrollable_frame, bg=current_theme["bg"])
network_frame.pack(fill="x", padx=20, pady=5)

def test_network_connectivity():
    """Test network connectivity to various Minecraft services."""
    try:
        import socket
        import time

        results = []
        services = [
            ("Minecraft Session Server", "sessionserver.mojang.com", 443),
            ("Minecraft Auth Server", "authserver.mojang.com", 443),
            ("Minecraft API", "api.mojang.com", 443),
            ("Microsoft Login", "login.microsoftonline.com", 443),
        ]

        for name, host, port in services:
            try:
                start_time = time.time()
                socket.create_connection((host, port), timeout=5)
                response_time = (time.time() - start_time) * 1000  # ms
                results.append(f"✓ {name}: Connected ({response_time:.1f}ms)")
            except (socket.timeout, socket.gaierror, OSError) as e:
                results.append(f"✗ {name}: Failed ({str(e)})")

        # Test internet connectivity
        try:
            requests.get("https://www.google.com", timeout=5)
            results.append("✓ Internet: Connected")
        except requests.exceptions.RequestException:
            results.append("✗ Internet: Disconnected")

        result_text = "Network Diagnostics Results:\n\n" + "\n".join(results)
        messagebox.showinfo("Network Test", result_text)

    except Exception as e:
        messagebox.showerror("Network Test Error", f"Failed to run network diagnostics: {str(e)}")

def check_launcher_updates():
    """Check for launcher updates from GitHub."""
    try:
        # This would typically check a GitHub repository for updates
        # For now, we'll simulate this functionality
        current_version = LAUNCHER_VERSION

        # Simulate checking for updates
        append_terminal("Checking for launcher updates...")

        # In a real implementation, you would:
        # 1. Fetch latest release from GitHub API
        # 2. Compare versions
        # 3. Download and install if newer version available

        messagebox.showinfo("Update Check", f"Current version: {current_version}\n\nUpdate checking is not implemented yet.\n\nTo check for updates manually, visit the project's GitHub repository.")

    except Exception as e:
        append_terminal(f"Update check failed: {str(e)}")
        messagebox.showerror("Update Check Error", f"Failed to check for updates: {str(e)}")

RoundedButton(network_frame, text="Test Connectivity", command=test_network_connectivity).pack(side="left", padx=(5, 0))
RoundedButton(network_frame, text="Check Updates", command=check_launcher_updates).pack(side="left", padx=(5, 0))

# === Additional Settings Sections ===
create_jvm_presets_section(settings_scrollable_frame, jvm_args_var, append_terminal, current_theme)
create_updater_section(settings_scrollable_frame, LAUNCHER_VERSION, LAUNCHER_NAME, append_terminal, current_theme)
create_backup_section(settings_scrollable_frame, MINECRAFT_DIR, config_data, append_terminal, current_theme)

tk.Label(root, text=f"{LAUNCHER_NAME} v{LAUNCHER_VERSION}", bg=current_theme["bg"], fg=current_theme["fg"]).pack(side="bottom", pady=5)

# === Final Setup ===
if username_var.get() and not selected_skin_path:
    threading.Thread(target=lambda: fetch_skin(username_var.get()), daemon=True).start()

root.mainloop()
