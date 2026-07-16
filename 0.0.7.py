import os
import string
import json
import importlib.util
from colorama import init, Fore, Style, Back
import subprocess
import datetime
import cv2
import time
import msvcrt  # For keyboard input on Windows
import math
import platform
import sys
import psutil  # For detailed system info
import base64
import http.server
import socketserver
import threading

init(autoreset=True)  # Colors reset automatically

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
THEMES_PATH = os.path.join(APP_DIR, "themes.json")
HISTORY_PATH = os.path.join(APP_DIR, "history.log")
PLUGINS_DIR = os.path.join(APP_DIR, "plugins")

current_path = None
camera_active = False
video_recording = False
video_writer = None
cap = None
active_app = None  # Stores the name of the currently active built-in app
web_mode = False   # True if browsing web
current_url = None # Current active site URL

COMMANDS = {}
COMMAND_HELP = {}
CONFIG = {}
THEMES = {}
ACTIVE_THEME = {}
HISTORY = []
LOADED_PLUGINS = []

# Global web server holder so we can stop it if needed
http_server_thread = None
http_server_instance = None

SAFE_COMMANDS = {
    "shutdown",
    "restart",
    "sleep",
    "end",
    "restart_pid",
    "delete",
    "cleanup",
}

BASE_HELP = [
    {"names": ["bc"], "display": "BC", "desc": "Show all available drives (interactive)", "icon": "💾"},
    {"names": ["c", "d", "e"], "display": "C / D / E", "desc": "Switch to specified drive", "icon": "🔄"},
    {"names": ["cd"], "display": "CD <folder>", "desc": "Enter specified folder", "icon": "📂"},
    {"names": [">>"], "display": ">> <folder>", "desc": "Quick enter folder (shortcut for CD)", "icon": "⚡"},
    {"names": [".."], "display": "..", "desc": "Go back to parent folder / exit drive root", "icon": "⬆️"},
    {"names": ["cdt"], "display": "CDT", "desc": "Display current path", "icon": "📍"},
    {"names": ["ls"], "display": "ls", "desc": "List files and folders", "icon": "📋"},
    {"names": ["browse"], "display": "browse", "desc": "Interactive file browser (arrow keys)", "icon": "🎯"},
    {"names": ["tasks"], "display": "tasks", "desc": "Show all running processes", "icon": "⚙️"},
    {"names": ["tasks browse"], "display": "tasks browse", "desc": "Interactive task manager (E=End, R=Restart)", "icon": "🎯"},
    {"names": ["x", "y", "tb"], "display": "x / y / tb", "desc": "Quick open task browser", "icon": "🎯"},
    {"names": ["end"], "display": "end <pid>", "desc": "End task by PID number", "icon": "❌"},
    {"names": ["restart"], "display": "restart <pid>", "desc": "Restart task by PID number", "icon": "🔄"},
    {"names": ["wifi"], "display": "wifi", "desc": "Scan and show available WiFi networks", "icon": "📡"},
    {"names": ["wifipass"], "display": "wifipass <name>", "desc": "Show password for saved WiFi network", "icon": "🔑"},
    {"names": ["ip"], "display": "ip", "desc": "Show detailed IP and network information", "icon": "🌐"},
    {"names": ["copy"], "display": "copy <src> <dst>", "desc": "Copy file from source to destination", "icon": "📋"},
    {"names": ["move"], "display": "move <src> <dst>", "desc": "Move file from source to destination", "icon": "🚚"},
    {"names": ["rename"], "display": "rename <old> <new>", "desc": "Rename a file", "icon": "✏️"},
    {"names": ["search"], "display": "search <pattern>", "desc": "Search files by pattern (*.txt, file*)", "icon": "🔍"},
    {"names": ["info"], "display": "info <file>", "desc": "Show detailed file information", "icon": "ℹ️"},
    {"names": ["note"], "display": "note", "desc": "Quick note taking (saves as .txt file)", "icon": "📝"},
    {"names": ["cleanup"], "display": "cleanup", "desc": "Clean temporary files and free disk space", "icon": "🧹"},
    {"names": ["tree"], "display": "tree", "desc": "Display directory tree structure", "icon": "🌳"},
    {"names": ["open"], "display": "open <file>", "desc": "Open file with default program", "icon": "🚀"},
    {"names": ["create"], "display": "create <file>", "desc": "Create new file in current folder", "icon": "✨"},
    {"names": ["delete"], "display": "delete <file>", "desc": "Delete file in current folder", "icon": "🗑️"},
    {"names": ["run"], "display": "run <file>", "desc": "Run file (HTML→Chrome, Code→VS Code)", "icon": "⚡"},
    {"names": ["code"], "display": "code <file>", "desc": "Open file in VS Code", "icon": "💻"},
    {"names": ["acode"], "display": "acode", "desc": "Enter Python interactive mode", "icon": "🐍"},
    {"names": ["calc"], "display": "calc", "desc": "Open advanced calculator", "icon": "🧮"},
    {"names": ["server"], "display": "server port <num>", "desc": "Start local HTTP server", "icon": "🌐"},
    {"names": ["camera"], "display": "camera", "desc": "Open camera preview", "icon": "📷"},
    {"names": ["take"], "display": "take", "desc": "Take a photo", "icon": "📸"},
    {"names": ["vid"], "display": "vid", "desc": "Start video recording", "icon": "🎥"},
    {"names": ["endvid"], "display": "endvid", "desc": "Stop video recording", "icon": "⏹️"},
    {"names": ["clear"], "display": "clear", "desc": "Clear screen", "icon": "🧹"},
    {"names": ["version"], "display": "version", "desc": "Show version information", "icon": "ℹ️"},
    {"names": ["debug"], "display": "debug", "desc": "System diagnostics and information", "icon": "🔧"},
    {"names": ["shutdown"], "display": "shutdown", "desc": "Shutdown computer", "icon": "🔴"},
    {"names": ["sleep"], "display": "sleep", "desc": "Put computer to sleep", "icon": "😴"},
    {"names": ["restartsys"], "display": "restart", "desc": "Restart computer", "icon": "🔄"},
    {"names": ["exit", "bsx"], "display": "exit / bsx", "desc": "Exit terminal (quick exit)", "icon": "🚪"},
    {"names": ["history"], "display": "history", "desc": "Show recent commands", "icon": "🧾"},
    {"names": ["theme"], "display": "theme", "desc": "List/set UI theme", "icon": "🎨"},
    {"names": ["safe"], "display": "safe", "desc": "Toggle safe mode on/off", "icon": "🛡️"},
    {"names": ["plugins"], "display": "plugins", "desc": "List loaded plugins", "icon": "🧩"},
    {"names": ["help"], "display": "help [command]", "desc": "Show help or details for a command", "icon": "📚"},
    {"names": ["dpa"], "display": "dpa <file>", "desc": "Run/open a .dpa file (Danrode Python App)", "icon": "🔐"},
    {"names": ["encrypt"], "display": "encrypt <file.py> [key]", "desc": "Encrypt a .py file into a legacy .dpa (XOR+Base64 text)", "icon": "🔒"},
    {"names": ["decrypt"], "display": "decrypt <file.dpa> [key]", "desc": "Decrypt a legacy text .dpa and show original Python source", "icon": "🔓"},
    {"names": ["pack"], "display": "pack <folder> [out.dpa] [key]", "desc": "Package a folder into an encrypted binary .dpa app (ZIP-based, like APK)", "icon": "📦"},
    {"names": ["unpack"], "display": "unpack <file.dpa> [dest] [key]", "desc": "Extract a binary .dpa app package without running it", "icon": "📤"},
    {"names": ["dpainfo"], "display": "dpainfo <file.dpa>", "desc": "Show format/manifest info about any .dpa file", "icon": "🧾"},
    {"names": ["zip"], "display": "zip <folder> [out.zip]", "desc": "Compress a folder into a .zip archive", "icon": "🗜️"},
    {"names": ["unzip"], "display": "unzip <file.zip> [dest]", "desc": "Extract a .zip archive", "icon": "📬"},
    {"names": ["hash"], "display": "hash <file> [md5|sha1|sha256]", "desc": "Compute a file's hash checksum", "icon": "🔢"},
    {"names": ["ping"], "display": "ping <host>", "desc": "Ping a network host", "icon": "📶"},
    {"names": ["cmd"], "display": "cmd [command]", "desc": "Run one real Windows CMD command, or enter a live CMD session", "icon": "⬛"},
    {"names": ["alias"], "display": "alias <name> <cmd> | list | remove <name>", "desc": "Create/manage custom command shortcuts", "icon": "🏷️"},
    {"names": ["apps"], "display": "apps", "desc": "List and launch system/built-in apps", "icon": "📱"},
    {"names": ["new"], "display": "new", "desc": "Show new commands in this version", "icon": "🆕"},
    {"names": ["sit"], "display": "sit [option] [value]", "desc": "Configure system settings (logo display, safe mode, history)", "icon": "⚙️"},
]

def register_command(name, handler, description=""):
    COMMANDS[name.lower()] = handler
    if description:
        COMMAND_HELP[name.lower()] = description

def _ensure_default_files():
    default_config = {
        "safe_mode": True,
        "theme": "classic",
        "history_enabled": True,
        "history_max": 200,
        "history_path": HISTORY_PATH,
        "dpa_key": "DanrodeDefaultKey2024",
        "aliases": {},
    }
    default_themes = {
        "classic": {
            "separator": "CYAN",
            "prompt_path": "GREEN",
            "prompt_label": "CYAN",
            "prompt_bracket": "YELLOW",
        },
        "sunset": {
            "separator": "MAGENTA",
            "prompt_path": "YELLOW",
            "prompt_label": "RED",
            "prompt_bracket": "WHITE",
        },
    }

    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
        except Exception:
            pass

    if not os.path.exists(THEMES_PATH):
        try:
            with open(THEMES_PATH, "w", encoding="utf-8") as f:
                json.dump(default_themes, f, indent=2)
        except Exception:
            pass

def _get_key_hint(key):
    """Produces a short public hint of the key (Base64 of first 3 chars)"""
    import base64
    return base64.b64encode(key[:3].encode()).decode()

def _load_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback

def load_config():
    _ensure_default_files()
    cfg = _load_json(CONFIG_PATH, {})
    cfg.setdefault("safe_mode", True)
    cfg.setdefault("theme", "classic")
    cfg.setdefault("history_enabled", True)
    cfg.setdefault("history_max", 200)
    cfg.setdefault("history_path", HISTORY_PATH)
    cfg.setdefault("dpa_key", "DanrodeDefaultKey2024")
    cfg.setdefault("aliases", {})
    cfg.setdefault("show_logo", True)
    if not os.path.isabs(cfg["history_path"]):
        cfg["history_path"] = os.path.join(APP_DIR, cfg["history_path"])
    return cfg

def load_themes():
    return _load_json(THEMES_PATH, {})

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print_error(f"Failed to save config: {e}")

def _color_from_name(name, fallback=Fore.WHITE):
    try:
        return getattr(Fore, name.upper())
    except Exception:
        return fallback

def apply_theme():
    global ACTIVE_THEME
    theme_name = CONFIG.get("theme", "classic")
    theme = THEMES.get(theme_name, THEMES.get("classic", {}))
    ACTIVE_THEME = theme

def append_history(cmd):
    if not CONFIG.get("history_enabled", True):
        return
    HISTORY.append(cmd)
    max_len = int(CONFIG.get("history_max", 200))
    if max_len > 0 and len(HISTORY) > max_len:
        HISTORY.pop(0)
    try:
        with open(CONFIG.get("history_path", HISTORY_PATH), "a", encoding="utf-8") as f:
            f.write(cmd + "\n")
    except Exception:
        pass

def load_history():
    if not CONFIG.get("history_enabled", True):
        return
    path = CONFIG.get("history_path", HISTORY_PATH)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line:
                        HISTORY.append(line)
    except Exception:
        pass

def safe_mode_blocked(cmd_key):
    return CONFIG.get("safe_mode", True) and cmd_key in SAFE_COMMANDS

def load_plugins():
    if not os.path.isdir(PLUGINS_DIR):
        return
    for filename in os.listdir(PLUGINS_DIR):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        plugin_path = os.path.join(PLUGINS_DIR, filename)
        mod_name = f"plugin_{os.path.splitext(filename)[0]}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, plugin_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "register"):
                    mod.register(register_command)
                LOADED_PLUGINS.append(filename)
        except Exception as e:
            print_error(f"Plugin load failed ({filename}): {e}")

def init_base_help():
    for entry in BASE_HELP:
        for name in entry["names"]:
            COMMAND_HELP[name.lower()] = entry["desc"]

def show_help(topic=None):
    if not topic:
        print(Fore.CYAN + Style.BRIGHT + "\n📚 DCMDS COMMAND REFERENCE\n")
        for entry in BASE_HELP:
            print(f"{Fore.GREEN}{entry['icon']} {Fore.YELLOW}{entry['display']:<25} {Fore.WHITE}→ {Fore.CYAN}{entry['desc']}")
        if COMMAND_HELP:
            print(Fore.MAGENTA + "\n🔌 Plugin Commands:")
            for name, desc in sorted(COMMAND_HELP.items()):
                if any(name in e["names"] for e in BASE_HELP):
                    continue
                print(f"{Fore.GREEN}🧩 {Fore.YELLOW}{name:<25} {Fore.WHITE}→ {Fore.CYAN}{desc}")
        separator()
        return

    key = topic.lower()
    if key in ["c", "d", "e"]:
        key = "c"
    if key == "restart":
        pass

    for entry in BASE_HELP:
        if key in [n.lower() for n in entry["names"]]:
            print(Fore.CYAN + Style.BRIGHT + f"\n📌 Help: {entry['display']}\n")
            print(Fore.WHITE + "Description: " + Fore.CYAN + entry["desc"])
            separator()
            return

    if key in COMMAND_HELP:
        print(Fore.CYAN + Style.BRIGHT + f"\n📌 Help: {key}\n")
        print(Fore.WHITE + "Description: " + Fore.CYAN + COMMAND_HELP[key])
        separator()
        return

    print_error(f"No help found for: {topic}")

def print_logo():
    """Display DCMDS system logo with colors"""
    if not CONFIG.get("show_logo", True):
        print(Fore.CYAN + Style.BRIGHT + "\n[DCMDS Terminal: Settings option 'logo' is disabled]\n")
        return
    logo = f"""
{Fore.CYAN}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   {Fore.GREEN}██████╗  {Fore.YELLOW}█████╗  {Fore.MAGENTA}███╗   ███╗ {Fore.RED}██████╗  {Fore.BLUE}██████╗{Fore.CYAN}               ║
║   {Fore.GREEN}██╔══██╗{Fore.YELLOW}██╔══██╗ {Fore.MAGENTA}████╗ ████║ {Fore.RED}██╔══██╗ {Fore.BLUE}██╔════╝{Fore.CYAN}              ║
║   {Fore.GREEN}██║  ██║{Fore.YELLOW}██║  ╚═╝ {Fore.MAGENTA}██╔████╔██║ {Fore.RED}██║  ██║ {Fore.BLUE}╚█████╗{Fore.CYAN}               ║
║   {Fore.GREEN}██║  ██║{Fore.YELLOW}██║  ██╗ {Fore.MAGENTA}██║╚██╔╝██║ {Fore.RED}██║  ██║ {Fore.BLUE}░╚═══██╗{Fore.CYAN}              ║
║   {Fore.GREEN}██████╔╝{Fore.YELLOW}╚█████╔╝ {Fore.MAGENTA}██║ ╚═╝ ██║ {Fore.RED}██████╔╝ {Fore.BLUE}██████╔╝{Fore.CYAN}              ║
║   {Fore.GREEN}╚═════╝  {Fore.YELLOW}╚════╝  {Fore.MAGENTA}╚═╝     ╚═╝ {Fore.RED}╚═════╝  {Fore.BLUE}╚═════╝{Fore.CYAN}               ║
║                                                               ║
║      {Fore.WHITE}{Style.BRIGHT}█▀▄ ▄▀█ █▄ █ █▀█ █▀█ █▀▄ █▀▀   █▀▀ █▀█ █▀▄▀█ █▀▄▀█{Fore.CYAN}       ║
║      {Fore.WHITE}{Style.BRIGHT}█▄▀ █▀█ █ ▀█ █▀▄ █▄█ █▄▀ ██▄   █▄▄ █▄█ █ ▀ █ █ ▀ █{Fore.CYAN}       ║
║                                                               ║
║               {Fore.WHITE}{Style.BRIGHT}█▀ █▄█ █▀ ▀█▀ █▀▀ █▀▄▀█{Fore.CYAN}                         ║
║               {Fore.WHITE}{Style.BRIGHT}▄█  █  ▄█  █  ██▄ █ ▀ █{Fore.CYAN}                         ║
║                                                               ║
║            {Fore.YELLOW}⚡ Advanced Terminal Interface ⚡{Fore.CYAN}                  ║
║                 {Fore.RED}Alpha {Fore.GREEN}Version 0.0.7{Fore.CYAN}                           ║
║              {Fore.CYAN}Build: {Fore.YELLOW}  jul,  15, 2026{Fore.CYAN}                          ║
║                 {Fore.YELLOW}[Under Development]{Fore.CYAN}                           ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(logo)
    time.sleep(0.5)

def separator():
    """Enhanced separator with gradient effect"""
    color = _color_from_name(ACTIVE_THEME.get("separator", "CYAN"), Fore.CYAN)
    print(color + "═" * 70)

def animated_separator():
    """Animated loading separator"""
    if not CONFIG.get("show_logo", True):
        return
    chars = ["▰", "▱"]
    for i in range(35):
        print(Fore.MAGENTA + chars[i % 2], end="", flush=True)
        time.sleep(0.01)
    print()

def list_drives():
    return [f"{l}:\\" for l in string.ascii_uppercase if os.path.exists(f"{l}:\\")]

def show_items():
    global current_path
    if not current_path:
        print_error("⚠ No path selected. Use BC or drive letter first.")
        return
    try:
        items = os.listdir(current_path)
        print(Fore.WHITE + Style.BRIGHT + f"\n📂 Contents of {current_path}:")
        separator()
        
        folders = []
        files = []
        
        for item in items:
            full = os.path.join(current_path, item)
            if os.path.isdir(full):
                folders.append(item)
            else:
                files.append(item)
        
        for folder in sorted(folders):
            print(Fore.CYAN + Style.BRIGHT + "📁 [DIR]  " + Fore.YELLOW + folder)
        
        for file in sorted(files):
            ext = os.path.splitext(file)[1].lower()
            if ext == ".dpa":
                icon = "🔐"
                color = Fore.RED
            elif ext in ['.py', '.js', '.java', '.cpp', '.c']:
                icon = "💻"
                color = Fore.GREEN
            elif ext in ['.html', '.css', '.jsx']:
                icon = "🌐"
                color = Fore.MAGENTA
            elif ext in ['.txt', '.md', '.doc', '.docx']:
                icon = "📄"
                color = Fore.WHITE
            elif ext in ['.jpg', '.png', '.gif', '.bmp']:
                icon = "🖼️"
                color = Fore.BLUE
            elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                icon = "🎬"
                color = Fore.RED
            else:
                icon = "📋"
                color = Fore.YELLOW
            
            print(color + f"{icon}        " + file)
        
        separator()
        print(Fore.WHITE + f"Total: {len(folders)} folders, {len(files)} files")
        print(Fore.CYAN + f"\n💡 Tip: Type " + Fore.GREEN + "'browse'" + Fore.CYAN + " to navigate with arrow keys!")
        
    except Exception as e:
        print_error(f"❌ Cannot access this folder: {e}")

def browse_files():
    """Interactive file browser with arrow key navigation"""
    global current_path
    if not current_path:
        print_error("⚠ No path selected. Use BC or drive letter first.")
        return None
    
    try:
        items = os.listdir(current_path)
        all_items = []
        
        for item in sorted(items):
            full = os.path.join(current_path, item)
            if os.path.isdir(full):
                all_items.append(("📁 [DIR]  " + item, item, "folder"))
            else:
                ext = os.path.splitext(item)[1].lower()
                if ext == ".dpa":
                    icon = "🔐"
                elif ext in ['.py', '.js', '.java', '.cpp', '.c']:
                    icon = "💻"
                elif ext in ['.html', '.css', '.jsx']:
                    icon = "🌐"
                elif ext in ['.txt', '.md', '.doc', '.docx']:
                    icon = "📄"
                elif ext in ['.jpg', '.png', '.gif', '.bmp']:
                    icon = "🖼️"
                elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                    icon = "🎬"
                else:
                    icon = "📋"
                all_items.append((f"{icon}        {item}", item, "file"))
        
        if not all_items:
            print_error("No files or folders found")
            return None
        
        selected = 0
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print_logo()
            print(Fore.CYAN + Style.BRIGHT + f"\n📂 Browsing: {current_path}")
            print(Fore.WHITE + "Use ↑↓ arrows, Enter to select, ESC to cancel\n")
            separator()
            
            display_start = max(0, selected - 15)
            display_end = min(len(all_items), display_start + 30)
            
            for i in range(display_start, display_end):
                display, name, item_type = all_items[i]
                if i == selected:
                    print(Back.WHITE + Fore.BLACK + "► " + display + " " * (60 - len(display)))
                else:
                    if item_type == "folder":
                        print(Fore.CYAN + "  " + display)
                    else:
                        print(Fore.YELLOW + "  " + display)
            
            separator()
            print(Fore.GREEN + f"\nSelected: " + Fore.YELLOW + all_items[selected][1])
            print(Fore.CYAN + f"Item {selected + 1} of {len(all_items)}")
            
            key = msvcrt.getch()
            
            if key == b'\xe0':
                key = msvcrt.getch()
                if key == b'H':
                    selected = (selected - 1) % len(all_items)
                elif key == b'P':
                    selected = (selected + 1) % len(all_items)
            
            elif key == b'\r':
                return all_items[selected][1]
            
            elif key == b'\x1b':
                print_info("\nBrowse cancelled")
                return None
            
            elif key.lower() == b'c':
                return all_items[selected][1]
    
    except Exception as e:
        print_error(f"Error browsing: {e}")
        return None

def show_tasks():
    """Display all running tasks/processes"""
    try:
        print(Fore.CYAN + Style.BRIGHT + "\n⚙️  RUNNING TASKS/PROCESSES\n")
        separator()
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes = sorted(processes, key=lambda x: x['memory_percent'] if x['memory_percent'] else 0, reverse=True)
        
        print(f"{Fore.YELLOW}{'PID':<8} {'Name':<30} {'CPU %':<8} {'RAM %':<8} {'Status':<12}")
        separator()
        
        for proc in processes[:30]:
            pid = proc['pid']
            name = proc['name'][:28] if len(proc['name']) > 28 else proc['name']
            cpu = f"{proc['cpu_percent']:.1f}%" if proc['cpu_percent'] else "0.0%"
            ram = f"{proc['memory_percent']:.1f}%" if proc['memory_percent'] else "0.0%"
            status = proc['status'][:10] if proc['status'] else "unknown"
            
            if proc['memory_percent'] and proc['memory_percent'] > 5:
                color = Fore.RED
            elif proc['memory_percent'] and proc['memory_percent'] > 2:
                color = Fore.YELLOW
            else:
                color = Fore.WHITE
            
            print(f"{color}{pid:<8} {name:<30} {cpu:<8} {ram:<8} {status:<12}")
        
        separator()
        print(Fore.CYAN + f"\nTotal Processes: {len(processes)}")
        print(Fore.YELLOW + f"💡 Tip: Type " + Fore.GREEN + "'tasks browse'" + Fore.YELLOW + " to interact with tasks!")
        
    except Exception as e:
        print_error(f"Failed to retrieve tasks: {e}")

def list_apps():
    """Display and launch system apps"""
    global active_app
    print(Fore.CYAN + Style.BRIGHT + "\n📱 SYSTEM & BUILT-IN APPLICATIONS\n")
    separator()
    
    # Predefined common system apps + some built-in concepts
    apps = [
        {"name": "Notepad", "exec": "notepad.exe", "type": "System"},
        {"name": "Calculator", "exec": "calc.exe", "type": "System"},
        {"name": "Task Manager", "exec": "taskmgr.exe", "type": "System"},
        {"name": "Paint", "exec": "mspaint.exe", "type": "System"},
        {"name": "Alarm (Built-in)", "exec": "INTERNAL_ALARM", "type": "Built-in"},
        {"name": "X-O Game", "exec": "INTERNAL_XO", "type": "Game"},
    ]
    
    for i, app in enumerate(apps, 1):
        if app["type"] == "Built-in": color = Fore.GREEN
        elif app["type"] == "Game": color = Fore.MAGENTA
        else: color = Fore.YELLOW
        print(f"{Fore.WHITE}{i}. {color}{app['name']:<20} {Fore.CYAN}[{app['type']}]")
    
    separator()
    choice = input(Fore.YELLOW + "Launch app (number) or ESC to cancel: " + Fore.WHITE).strip()
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(apps):
            app = apps[idx]
            if app["exec"] == "INTERNAL_ALARM":
                active_app = "Alarm"
                print_info("Launched Built-in Alarm.")
                alarm_app()
            elif app["exec"] == "INTERNAL_XO":
                active_app = "X-O Game"
                xo_game()
            else:
                try:
                    subprocess.Popen(app["exec"])
                    print_success(f"Launched {app['name']}")
                except Exception as e:
                    print_error(f"Failed to launch {app['name']}: {e}")
    else:
        print_info("Cancelled")

def alarm_app():
    """Simple built-in alarm app"""
    global active_app
    print(Fore.CYAN + Style.BRIGHT + "\n⏰ ALARM APP\n")
    separator()
    print(Fore.WHITE + "1. Set Timer (Seconds)")
    print(Fore.WHITE + "2. Back to Apps")
    print(Fore.WHITE + "3. Exit App")
    separator()
    
    choice = input(Fore.YELLOW + "Choice: " + Fore.WHITE).strip()
    
    if choice == "1":
        try:
            sec = int(input(Fore.YELLOW + "Seconds: " + Fore.WHITE).strip())
            print_info(f"Timer set for {sec} seconds...")
            time.sleep(sec)
            print("\a" * 3) # Beep
            print(Fore.RED + Style.BRIGHT + "\n🔔 TIME IS UP! 🔔\n")
            separator()
        except ValueError:
            print_error("Invalid input")
    elif choice == "2":
        list_apps()
    elif choice == "3":
        active_app = None
        print_info("Alarm closed")
    else:
        print_info("Invalid choice")

def xo_game():
    """Built-in X-O Game"""
    global active_app
    print(Fore.MAGENTA + Style.BRIGHT + "\n🎮 X-O GAME (Tic-Tac-Toe)\n")
    separator()
    board = [" " for _ in range(9)]
    current_player = "X"
    
    def print_board():
        print(Fore.WHITE + f" {board[0]} | {board[1]} | {board[2]} ")
        print(Fore.WHITE + "-----------")
        print(Fore.WHITE + f" {board[3]} | {board[4]} | {board[5]} ")
        print(Fore.WHITE + "-----------")
        print(Fore.WHITE + f" {board[6]} | {board[7]} | {board[8]} ")

    while active_app == "X-O Game":
        os.system('cls' if os.name == 'nt' else 'clear')
        print_logo()
        print_board()
        print(f"\nPlayer {current_player}'s turn")
        print("Enter 1-9 to move, or 'exit' to quit")
        
        move = input(Fore.YELLOW + "> " + Fore.WHITE).strip().lower()
        if move == "exit":
            active_app = None
            break
        
        if move.isdigit() and 1 <= int(move) <= 9:
            idx = int(move) - 1
            if board[idx] == " ":
                board[idx] = current_player
                # Check win
                wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
                if any(board[i] == board[j] == board[k] == current_player for i,j,k in wins):
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print_board()
                    print_success(f"PLAYER {current_player} WINS!")
                    time.sleep(2)
                    break
                if " " not in board:
                    print_info("It's a draw!")
                    time.sleep(2)
                    break
                current_player = "O" if current_player == "X" else "X"
            else:
                print_error("Spot already taken!")
                time.sleep(1)
        else:
            print_error("Invalid move!")
            time.sleep(1)

def embedded_browser(url="https://www.google.com"):
    """Simulated embedded browser window using Tkinter"""
    global active_app, web_mode, current_url
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.title(f"DCMDS Browser - {url}")
        root.geometry("800x600")
        root.attributes("-topmost", True)
        
        # Simple UI elements
        frame = tk.Frame(root, bg="white")
        frame.pack(fill=tk.BOTH, expand=True)
        
        label = tk.Label(frame, text=f"🌐 Viewing: {url}", font=("Arial", 12), bg="white", fg="blue")
        label.pack(pady=10)
        
        content = tk.Label(frame, text="[Simulated Web Content]\n\nWelcome to DCMDS Embedded Browser.\nThis window is controlled by the terminal.\n\nType 'exit' in terminal to close.", 
                          font=("Arial", 10), bg="white", fg="black", justify=tk.LEFT)
        content.pack(pady=50)
        
        def on_closing():
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print_info(f"Browser window opened for {url}")
        root.mainloop()
        
    except Exception as e:
        print_error(f"Failed to launch embedded browser: {e}")
        # Fallback to console simulation
        print(Fore.MAGENTA + f"\n[EMBEDDED BROWSER SIMULATION - {url}]")
        print(Fore.WHITE + "--------------------------------------")
        print(Fore.WHITE + "  [Search Bar: google.com             ]")
        print(Fore.WHITE + "  [Results for 'Python Terminal'      ]")
        print(Fore.WHITE + "  (Content hidden in console mode)     ")
        print(Fore.WHITE + "--------------------------------------\n")

def browse_tasks():
    """Interactive task browser with options to end or restart tasks"""
    try:
        selected = 0
        
        while True:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes = sorted(processes, key=lambda x: x['memory_percent'] if x['memory_percent'] else 0, reverse=True)
            
            if not processes:
                print_error("No processes found")
                return
            
            if selected >= len(processes):
                selected = len(processes) - 1
            
            os.system('cls' if os.name == 'nt' else 'clear')
            print_logo()
            print(Fore.CYAN + Style.BRIGHT + "\n⚙️  TASK MANAGER - INTERACTIVE MODE")
            print(Fore.WHITE + "Use ↑↓ arrows | " + Fore.RED + "E" + Fore.WHITE + " to End Task | " + Fore.GREEN + "R" + Fore.WHITE + " to Restart | ESC to exit\n")
            separator()
            
            print(f"{Fore.YELLOW}{'PID':<8} {'Name':<35} {'CPU %':<8} {'RAM %':<8}")
            separator()
            
            display_start = max(0, selected - 10)
            display_end = min(len(processes), display_start + 20)
            
            for i in range(display_start, display_end):
                proc = processes[i]
                pid = proc['pid']
                name = proc['name'][:33] if len(proc['name']) > 33 else proc['name']
                cpu = f"{proc['cpu_percent']:.1f}%" if proc['cpu_percent'] else "0.0%"
                ram = f"{proc['memory_percent']:.1f}%" if proc['memory_percent'] else "0.0%"
                
                display_line = f"{pid:<8} {name:<35} {cpu:<8} {ram:<8}"
                
                if i == selected:
                    print(Back.WHITE + Fore.BLACK + "► " + display_line + " " * (70 - len(display_line)))
                else:
                    if proc['memory_percent'] and proc['memory_percent'] > 5:
                        color = Fore.RED
                    elif proc['memory_percent'] and proc['memory_percent'] > 2:
                        color = Fore.YELLOW
                    else:
                        color = Fore.WHITE
                    print(color + "  " + display_line)
            
            separator()
            selected_proc = processes[selected]
            print(Fore.GREEN + f"\nSelected: " + Fore.YELLOW + f"{selected_proc['name']} " + Fore.CYAN + f"(PID: {selected_proc['pid']})")
            print(Fore.WHITE + f"Status: " + Fore.CYAN + f"{selected_proc['status']}")
            print(Fore.CYAN + f"Process {selected + 1} of {len(processes)}")
            
            key = msvcrt.getch()
            
            if key == b'\xe0':
                key = msvcrt.getch()
                if key == b'H':
                    selected = max(0, selected - 1)
                elif key == b'P':
                    selected = min(len(processes) - 1, selected + 1)
            
            elif key == b'\x1b':
                print_info("\nExited task browser")
                return
            
            elif key.lower() == b'e':
                proc_to_end = processes[selected]
                print(Fore.RED + f"\n⚠️  End task: {proc_to_end['name']} (PID: {proc_to_end['pid']})?")
                confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
                
                if confirm == 'yes':
                    try:
                        process = psutil.Process(proc_to_end['pid'])
                        process.terminate()
                        time.sleep(0.5)
                        
                        if process.is_running():
                            process.kill()
                        
                        print_success(f"Task ended: {proc_to_end['name']}")
                        time.sleep(1)
                    except psutil.NoSuchProcess:
                        print_error("Process no longer exists")
                        time.sleep(1)
                    except psutil.AccessDenied:
                        print_error("Access denied - cannot end this task (try running as administrator)")
                        time.sleep(2)
                    except Exception as e:
                        print_error(f"Failed to end task: {e}")
                        time.sleep(2)
                else:
                    print_info("Cancelled")
                    time.sleep(1)
            
            elif key.lower() == b'r':
                proc_to_restart = processes[selected]
                print(Fore.YELLOW + f"\n🔄 Restart task: {proc_to_restart['name']} (PID: {proc_to_restart['pid']})?")
                confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
                
                if confirm == 'yes':
                    try:
                        process = psutil.Process(proc_to_restart['pid'])
                        exe_path = process.exe()
                        
                        process.terminate()
                        time.sleep(0.5)
                        
                        if process.is_running():
                            process.kill()
                        
                        time.sleep(1)
                        
                        subprocess.Popen([exe_path])
                        print_success(f"Task restarted: {proc_to_restart['name']}")
                        time.sleep(1)
                        
                    except psutil.NoSuchProcess:
                        print_error("Process no longer exists")
                        time.sleep(1)
                    except psutil.AccessDenied:
                        print_error("Access denied - cannot restart this task (try running as administrator)")
                        time.sleep(2)
                    except Exception as e:
                        print_error(f"Failed to restart task: {e}")
                        time.sleep(2)
                else:
                    print_info("Cancelled")
                    time.sleep(1)
    
    except Exception as e:
        print_error(f"Error in task browser: {e}")
        time.sleep(2)

def print_command(text):
    print(Fore.GREEN + Style.BRIGHT + "✓ " + text)

def print_output(text):
    print(Fore.MAGENTA + Style.BRIGHT + "➤ " + text)

def print_error(text):
    print(Fore.RED + Style.BRIGHT + "✗ " + text)

def print_success(text):
    print(Fore.GREEN + Back.BLACK + Style.BRIGHT + "✓ " + text)

def print_info(text):
    print(Fore.CYAN + Style.BRIGHT + "ℹ " + text)

def show_wifi_networks():
    try:
        print(Fore.CYAN + Style.BRIGHT + "\n📡 SCANNING WIFI NETWORKS...\n")
        separator()
        result = subprocess.run(['netsh', 'wlan', 'show', 'networks'], 
                              capture_output=True, text=True, encoding='cp1256')
        if result.returncode == 0:
            print(Fore.WHITE + result.stdout)
        else:
            print_error("Failed to scan WiFi networks")
        separator()
    except Exception as e:
        print_error(f"Error scanning WiFi: {e}")

def show_wifi_password(network_name):
    try:
        print(Fore.CYAN + f"\n🔑 Retrieving password for: {Fore.YELLOW}{network_name}\n")
        separator()
        result = subprocess.run(['netsh', 'wlan', 'show', 'profile', network_name, 'key=clear'], 
                              capture_output=True, text=True, encoding='cp1256')
        if result.returncode == 0:
            output = result.stdout
            for line in output.split('\n'):
                if 'Key Content' in line or 'محتوى المفتاح' in line:
                    password = line.split(':')[-1].strip()
                    print(Fore.GREEN + f"Network: {Fore.YELLOW}{network_name}")
                    print(Fore.GREEN + f"Password: {Fore.RED}{password}")
                    separator()
                    return
            print(Fore.YELLOW + "Password not found or network not saved")
        else:
            print_error(f"Network '{network_name}' not found in saved networks")
        separator()
    except Exception as e:
        print_error(f"Error retrieving password: {e}")

def show_ip_info():
    try:
        print(Fore.CYAN + Style.BRIGHT + "\n🌐 NETWORK INFORMATION\n")
        separator()
        
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for interface_name, addresses in interfaces.items():
            if interface_name in stats:
                stat = stats[interface_name]
                if stat.isup:
                    print(Fore.YELLOW + f"\n📶 {interface_name}")
                    print(Fore.WHITE + "  Status: " + Fore.GREEN + "UP")
                    print(Fore.WHITE + f"  Speed: " + Fore.CYAN + f"{stat.speed} Mbps")
                    
                    for addr in addresses:
                        if str(addr.family) == 'AddressFamily.AF_INET':
                            print(Fore.WHITE + f"  IPv4: " + Fore.GREEN + addr.address)
                            if addr.netmask:
                                print(Fore.WHITE + f"  Netmask: " + Fore.YELLOW + addr.netmask)
                        elif str(addr.family) == 'AddressFamily.AF_INET6':
                            print(Fore.WHITE + f"  IPv6: " + Fore.CYAN + addr.address)
                        elif str(addr.family) == 'AddressFamily.AF_LINK':
                            print(Fore.WHITE + f"  MAC: " + Fore.MAGENTA + addr.address)
        
        separator()
    except Exception as e:
        print_error(f"Error getting IP info: {e}")

def copy_file(source, destination):
    try:
        import shutil
        if os.path.isfile(source):
            shutil.copy2(source, destination)
            print_success(f"File copied: {Fore.YELLOW}{source} {Fore.WHITE}→ {Fore.CYAN}{destination}")
        else:
            print_error("Source file not found")
    except Exception as e:
        print_error(f"Failed to copy file: {e}")

def move_file(source, destination):
    try:
        import shutil
        if os.path.isfile(source):
            shutil.move(source, destination)
            print_success(f"File moved: {Fore.YELLOW}{source} {Fore.WHITE}→ {Fore.CYAN}{destination}")
        else:
            print_error("Source file not found")
    except Exception as e:
        print_error(f"Failed to move file: {e}")

def rename_file(old_name, new_name):
    try:
        if os.path.exists(old_name):
            os.rename(old_name, new_name)
            print_success(f"File renamed: {Fore.YELLOW}{old_name} {Fore.WHITE}→ {Fore.CYAN}{new_name}")
        else:
            print_error("File not found")
    except Exception as e:
        print_error(f"Failed to rename file: {e}")

def search_files(pattern):
    global current_path
    if not current_path:
        print_error("No path selected")
        return
    
    try:
        import fnmatch
        print(Fore.CYAN + Style.BRIGHT + f"\n🔍 Searching for: {Fore.YELLOW}{pattern}\n")
        separator()
        
        found_files = []
        for root, dirs, files in os.walk(current_path):
            for filename in files:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, current_path)
                    found_files.append(relative_path)
        
        if found_files:
            for i, file in enumerate(found_files[:50], 1):
                print(Fore.GREEN + f"{i}. " + Fore.WHITE + file)
            
            if len(found_files) > 50:
                print(Fore.YELLOW + f"\n... and {len(found_files) - 50} more files")
            
            print(Fore.CYAN + f"\nTotal found: {len(found_files)} files")
        else:
            print(Fore.YELLOW + "No files found matching the pattern")
        
        separator()
    except Exception as e:
        print_error(f"Search error: {e}")

def show_file_info(filename):
    global current_path
    if not current_path:
        print_error("No path selected")
        return
    
    try:
        filepath = os.path.join(current_path, filename)
        if not os.path.exists(filepath):
            print_error("File not found")
            return
        
        stat_info = os.stat(filepath)
        
        print(Fore.CYAN + Style.BRIGHT + f"\n📄 FILE INFORMATION\n")
        separator()
        
        print(Fore.WHITE + "Name:         " + Fore.YELLOW + filename)
        print(Fore.WHITE + "Path:         " + Fore.CYAN + filepath)
        print(Fore.WHITE + "Size:         " + Fore.GREEN + f"{stat_info.st_size:,} bytes ({stat_info.st_size / 1024:.2f} KB)")
        print(Fore.WHITE + "Type:         " + Fore.MAGENTA + ("Directory" if os.path.isdir(filepath) else "File"))
        
        creation_time = datetime.datetime.fromtimestamp(stat_info.st_ctime)
        print(Fore.WHITE + "Created:      " + Fore.YELLOW + creation_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        modified_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
        print(Fore.WHITE + "Modified:     " + Fore.YELLOW + modified_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        if not os.path.isdir(filepath):
            ext = os.path.splitext(filename)[1]
            print(Fore.WHITE + "Extension:    " + Fore.CYAN + (ext if ext else "No extension"))
        
        separator()
    except Exception as e:
        print_error(f"Error getting file info: {e}")

def quick_note():
    print(Fore.CYAN + Style.BRIGHT + "\n📝 QUICK NOTE\n")
    separator()
    print(Fore.WHITE + "Type your note (press Enter twice to save):\n")
    
    lines = []
    empty_count = 0
    
    while True:
        line = input(Fore.YELLOW + "")
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
            lines.append(line)
    
    if lines:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"note_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print_success(f"Note saved: {Fore.YELLOW}{filename}")
        except Exception as e:
            print_error(f"Failed to save note: {e}")
    else:
        print_info("Note cancelled - no content")

def system_cleanup():
    print(Fore.CYAN + Style.BRIGHT + "\n🧹 SYSTEM CLEANUP\n")
    separator()
    
    print(Fore.YELLOW + "This will clean temporary files from:")
    print(Fore.WHITE + "  • Windows Temp folder")
    print(Fore.WHITE + "  • User Temp folder")
    print(Fore.WHITE + "  • Recycle Bin (optional)")
    print()
    
    confirm = input(Fore.YELLOW + "Continue? (yes/no): " + Fore.WHITE).strip().lower()
    
    if confirm not in ['yes', 'y']:
        print_info("Cleanup cancelled")
        return
    
    try:
        import shutil
        deleted_size = 0
        deleted_count = 0
        
        temp_paths = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            'C:\\Windows\\Temp'
        ]
        
        print(Fore.CYAN + "\n🔄 Cleaning temporary files...\n")
        
        for temp_path in temp_paths:
            if temp_path and os.path.exists(temp_path):
                for item in os.listdir(temp_path):
                    item_path = os.path.join(temp_path, item)
                    try:
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            os.remove(item_path)
                            deleted_size += size
                            deleted_count += 1
                        elif os.path.isdir(item_path):
                            size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                     for dirpath, dirnames, filenames in os.walk(item_path)
                                     for filename in filenames)
                            shutil.rmtree(item_path)
                            deleted_size += size
                            deleted_count += 1
                    except:
                        pass
        
        separator()
        print(Fore.GREEN + f"✓ Cleanup complete!")
        print(Fore.WHITE + f"  Files deleted: " + Fore.YELLOW + f"{deleted_count}")
        print(Fore.WHITE + f"  Space freed:   " + Fore.GREEN + f"{deleted_size / (1024**2):.2f} MB")
        separator()
        
    except Exception as e:
        print_error(f"Cleanup error: {e}")


# ════════════════════════════════════════════════════════════════
#  NEW DIRECT IMPLEMENTATIONS (CAMERA, CALC, TREE, PYTHON RUNNERS)
# ════════════════════════════════════════════════════════════════

def handle_camera():
    """Handle standard camera preview screen"""
    global camera_active, cap
    if camera_active:
        print_error("Camera is already active.")
        return
    
    print_info("Initializing Camera... Press 'q' inside window to close.")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print_error("Error: Could not open video device / camera.")
        return
    
    camera_active = True
    while camera_active:
        ret, frame = cap.read()
        if not ret:
            print_error("Failed to grab frame.")
            break
        cv2.imshow("DCMDS Camera Live Preview", frame)
        # Check if 'q' is pressed on keyboard to exit window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    camera_active = False
    print_success("Camera preview stopped.")

def handle_camera_take():
    """Capture instant photo from camera feed"""
    cap_temp = cv2.VideoCapture(0)
    if not cap_temp.isOpened():
        print_error("Could not access camera for photo capture.")
        return
    
    # Let sensor adjust to light
    time.sleep(0.5)
    ret, frame = cap_temp.read()
    if ret:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"capture_{timestamp}.png"
        filepath = os.path.join(current_path, filename) if current_path else filename
        cv2.imwrite(filepath, frame)
        print_success(f"Photo captured and saved as: {Fore.YELLOW}{filename}")
    else:
        print_error("Failed to capture image.")
    cap_temp.release()

def handle_video_record():
    """Start video recording loop"""
    global video_recording, video_writer, cap
    if video_recording:
        print_error("Video recording is already running.")
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print_error("Could not access camera device.")
        return
        
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"video_{timestamp}.mp4"
    filepath = os.path.join(current_path, filename) if current_path else filename
    
    # Default parameters
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = 20.0
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(filepath, fourcc, fps, (frame_width, frame_height))
    
    video_recording = True
    print_success(f"Video Recording Started! Saved to: {filename}")
    print_info("Type 'endvid' to stop and finalize the video recording.")
    
    def record_loop():
        global video_recording, cap, video_writer
        while video_recording:
            ret, frame = cap.read()
            if not ret:
                break
            video_writer.write(frame)
            cv2.imshow("DCMDS Recording...", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                video_recording = False
                break
        
        if video_writer:
            video_writer.release()
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        video_recording = False
        print_success("Video finalized successfully.")

    # Run loop in background thread to keep console input alive
    thread = threading.Thread(target=record_loop, daemon=True)
    thread.start()

def handle_advanced_calculator():
    """Mathematical solver module"""
    print(Fore.CYAN + Style.BRIGHT + "\n🧮 ADVANCED CALCULATOR MODE\n")
    print(Fore.WHITE + "Supports: +, -, *, /, sin, cos, tan, log, log10, sqrt, **")
    print(Fore.WHITE + "Type 'exit' to close the calculator.\n")
    separator()
    while True:
        expr = input(Fore.YELLOW + "calc> " + Fore.WHITE).strip()
        if expr.lower() == 'exit':
            print_info("Calculator closed.")
            break
        if not expr:
            continue
        try:
            # Preparing safe math namespace evaluation
            allowed_names = {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'log10': math.log10, 'sqrt': math.sqrt,
                'pi': math.pi, 'e': math.e, 'pow': math.pow
            }
            result = eval(expr, {"__builtins__": None}, allowed_names)
            print_success(f"Result: {Fore.YELLOW}{result}")
        except Exception as e:
            print_error(f"Calculation Error: {e}")

def handle_tree_view(path, prefix=""):
    """Recursive directory tree rendering"""
    try:
        if not os.path.exists(path):
            print_error("Path doesn't exist.")
            return
        
        items = sorted(os.listdir(path))
        for idx, item in enumerate(items):
            item_path = os.path.join(path, item)
            is_last = (idx == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            if os.path.isdir(item_path):
                print(prefix + connector + Fore.CYAN + f"📁 {item}")
                new_prefix = prefix + ("    " if is_last else "│   ")
                handle_tree_view(item_path, new_prefix)
            else:
                print(prefix + connector + Fore.YELLOW + f"📄 {item}")
    except Exception as e:
        print_error(f"Error building tree: {e}")

def handle_local_web_server(port=8000):
    """Starts Python-based web server thread on specified path"""
    global http_server_thread, http_server_instance
    if not current_path:
        print_error("No folder selected to serve. Use BC command first.")
        return
        
    if http_server_instance:
        print_info("Stopping already running server...")
        http_server_instance.shutdown()
        
    os.chdir(current_path)
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        http_server_instance = socketserver.TCPServer(("", port), handler)
        print_success(f"Web Server started successfully at: http://localhost:{port}/")
        print_info(f"Serving folder: {current_path}")
        
        def run_server():
            http_server_instance.serve_forever()
            
        http_server_thread = threading.Thread(target=run_server, daemon=True)
        http_server_thread.start()
    except Exception as e:
        print_error(f"Failed to bind local server on port {port}: {e}")

def handle_python_interactive():
    """Interactive Python REPL console"""
    print(Fore.GREEN + Style.BRIGHT + "\n🐍 PYTHON INTERACTIVE REPL (acode)")
    print(Fore.WHITE + "Write Python code directly below. Type 'exit()' to leave session.\n")
    separator()
    import code
    # Starts standard interactive shell console
    code.interact(local=locals())
    print_info("Interactive Mode Closed.")


# ════════════════════════════════════════════════════════════════
#  DPA FILE HANDLER - Danrode Protected Archive
# ════════════════════════════════════════════════════════════════

# =====================================================================
# DPA (Danrode Python App) Engine
#   v1  -> plain text, no encryption (#DPA-PLAIN)
#   v2  -> legacy single-file text encryption, XOR + Base64 (#DPA-XOR2)
#   v3  -> NEW: binary ZIP-based encrypted app package (APK-style).
#          A whole folder (multiple files, assets, a manifest.json with
#          an entry point) is zipped, then the raw ZIP bytes are
#          XOR-encrypted and written as pure binary (no Base64/text
#          wrapping), prefixed with a small binary header.
# =====================================================================
DPA_HEADER_PLAIN = "#DPA-PLAIN"
DPA_HEADER_XOR   = "#DPA-XOR2" # Version 2 supports embedded key hints
DPA_MAGIC_V3     = b"DPA3BIN\x00"  # Binary ZIP-based app package magic
DEFAULT_DPA_KEY  = "DanrodeDefaultKey2024"

# Common typo dictionary for smart fix suggestions
_COMMON_TYPOS = {
    "ptint": "print", "pritn": "print", "prnit": "print", "prin": "print",
    "prnt": "print", "prit": "print",
    "imput": "input", "inpt": "input",
    "improt": "import", "imort": "import", "imprort": "import",
    "retrun": "return", "retunr": "return", "reutrn": "return",
    "esle": "else", "eles": "else", "elif:": "elif",
    "fucntion": "function", "defien": "define",
    "len(": "len(", "rang": "range", "ragne": "range",
    "Tru": "True", "Flase": "False", "Fasle": "False", "ture": "True",
    "Non": "None", "none": "None",
}

def _get_dpa_key(custom=None):
    if custom:
        return custom
    try:
        return CONFIG.get("dpa_key", DEFAULT_DPA_KEY) or DEFAULT_DPA_KEY
    except Exception:
        return DEFAULT_DPA_KEY

def xor_encode(plaintext: str, key: str) -> str:
    """XOR encrypt then Base64 encode. Returns ASCII string. (legacy v2 text engine)"""
    pb = plaintext.encode("utf-8")
    kb = key.encode("utf-8")
    if not kb:
        kb = DEFAULT_DPA_KEY.encode("utf-8")
    out = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(pb))
    return base64.b64encode(out).decode("ascii")

def xor_decode(ciphertext: str, key: str) -> str:
    """Base64 decode then XOR decrypt. Returns plaintext string. (legacy v2 text engine)"""
    raw = base64.b64decode(ciphertext.encode("ascii"))
    kb = key.encode("utf-8")
    if not kb:
        kb = DEFAULT_DPA_KEY.encode("utf-8")
    out = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw))
    return out.decode("utf-8")

def _xor_bytes(data: bytes, key: str) -> bytes:
    kb = key.encode("utf-8") if key else b""
    if not kb:
        kb = DEFAULT_DPA_KEY.encode("utf-8")
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))

def encrypt_to_dpa(py_path: str, dpa_path: str = None, key: str = None) -> str:
    """(Legacy v2) Encrypt a single .py file into a text .dpa file. Kept for backward compatibility."""
    key = _get_dpa_key(key)
    with open(py_path, "r", encoding="utf-8") as f:
        source = f.read()
    if dpa_path is None:
        base, _ = os.path.splitext(py_path)
        dpa_path = base + ".dpa"
    encoded = xor_encode(source, key)
    hint = _get_key_hint(key)
    # Wrap to 76 chars per line for nicer files
    chunks = [encoded[i:i+76] for i in range(0, len(encoded), 76)]
    with open(dpa_path, "w", encoding="utf-8") as f:
        f.write(f"{DPA_HEADER_XOR} {hint}\n")
        f.write("\n".join(chunks) + "\n")
    return dpa_path

def decrypt_dpa(dpa_path: str, key: str = None) -> str:
    """(Legacy v1/v2) Decrypt a text-based .dpa file and return the original Python source."""
    key = _get_dpa_key(key)
    with open(dpa_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    if not lines:
        raise ValueError("Empty .dpa file")
    header = lines[0].strip()
    body = "\n".join(lines[1:])
    if header == DPA_HEADER_PLAIN:
        return body
    if header.startswith("#DPA-XOR"):
        # Version 2+ might have key hint in the header line
        # Format: #DPA-XOR2 [KeyHint]
        parts = header.split()
        if len(parts) > 1 and not key:
             hint = parts[1]
             # If the hint matches our default key or config key, use it
             if hint == _get_key_hint(DEFAULT_DPA_KEY):
                 key = DEFAULT_DPA_KEY
             elif hint == _get_key_hint(CONFIG.get("dpa_key", "")):
                 key = CONFIG.get("dpa_key")
        
        # Fallback to default if still no key
        if not key:
            key = _get_dpa_key()
            
        encoded = "".join(body.split())
        return xor_decode(encoded, key)
    # Legacy / no header → assume plain Python
    return content

def pack_to_dpa(folder_path: str, dpa_path: str = None, key: str = None, entry: str = None) -> str:
    """
    (NEW v3) Pack a whole folder into a binary, encrypted .dpa app package —
    similar in spirit to how an APK bundles files inside a signed/zipped
    container. Steps:
      1. Zip every file under folder_path (recursively) + write manifest.json.
      2. XOR-encrypt the raw ZIP bytes.
      3. Write a small binary header (magic, version, key hint, checksum,
         payload length) followed by the encrypted bytes to a .dpa file.
    """
    import zipfile, io, zlib

    key = _get_dpa_key(key)
    folder_path = folder_path.rstrip("\\/")
    if not os.path.isdir(folder_path):
        raise ValueError("Not a folder")

    if dpa_path is None:
        dpa_path = folder_path + ".dpa"

    # Auto-detect an entry point if the caller didn't specify one
    if entry is None:
        for candidate in ("main.py", "app.py", "__main__.py"):
            if os.path.exists(os.path.join(folder_path, candidate)):
                entry = candidate
                break
        if entry is None:
            py_files = sorted(f for f in os.listdir(folder_path) if f.endswith(".py"))
            entry = py_files[0] if py_files else None

    # Load from info.json or manifest.json if exists in folder
    manifest_data = None
    info_path = os.path.join(folder_path, "info.json")
    manifest_path = os.path.join(folder_path, "manifest.json")
    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception:
            pass
    elif os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception:
            pass

    if manifest_data is None:
        manifest_data = {
            "name": os.path.basename(folder_path),
            "entry": entry,
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "dpa_version": 3,
        }
    else:
        if "name" not in manifest_data:
            manifest_data["name"] = os.path.basename(folder_path)
        if "entry" not in manifest_data or not manifest_data["entry"]:
            manifest_data["entry"] = entry
        manifest_data["dpa_version"] = 3
        if "created" not in manifest_data:
            manifest_data["created"] = datetime.datetime.now().isoformat(timespec="seconds")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write both info.json and manifest.json for compatibility
        manifest_str = json.dumps(manifest_data, indent=2)
        zf.writestr("info.json", manifest_str)
        zf.writestr("manifest.json", manifest_str)
        
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f in ("info.json", "manifest.json"):
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, folder_path)
                zf.write(full, rel)

    zip_bytes = buf.getvalue()
    checksum = zlib.crc32(zip_bytes) & 0xFFFFFFFF
    encrypted = _xor_bytes(zip_bytes, key)
    hint = _get_key_hint(key).encode("ascii")

    with open(dpa_path, "wb") as f:
        f.write(DPA_MAGIC_V3)                     # 8 bytes magic
        f.write(bytes([3]))                        # 1 byte format version
        f.write(bytes([len(hint)]))                 # 1 byte key-hint length
        f.write(hint)                                # key hint bytes
        f.write(checksum.to_bytes(4, "big"))          # 4 bytes CRC32 of plain zip
        f.write(len(encrypted).to_bytes(8, "big"))     # 8 bytes payload length
        f.write(encrypted)                              # encrypted zip payload

    return dpa_path

def _read_dpa_v3(dpa_path: str, key: str = None):
    """Reads & decrypts a v3 binary .dpa file. Returns (zip_bytes, manifest_dict)."""
    import zlib

    with open(dpa_path, "rb") as f:
        data = f.read()

    if not data.startswith(DPA_MAGIC_V3):
        raise ValueError("Not a v3 binary .dpa app package")

    pos = len(DPA_MAGIC_V3)
    version = data[pos]; pos += 1
    hint_len = data[pos]; pos += 1
    hint = data[pos:pos + hint_len].decode("ascii"); pos += hint_len
    checksum = int.from_bytes(data[pos:pos + 4], "big"); pos += 4
    payload_len = int.from_bytes(data[pos:pos + 8], "big"); pos += 8
    payload = data[pos:pos + payload_len]

    if not key:
        if hint == _get_key_hint(DEFAULT_DPA_KEY):
            key = DEFAULT_DPA_KEY
        elif hint == _get_key_hint(CONFIG.get("dpa_key", "") or ""):
            key = CONFIG.get("dpa_key")
        else:
            key = _get_dpa_key()

    zip_bytes = _xor_bytes(payload, key)

    if (zlib.crc32(zip_bytes) & 0xFFFFFFFF) != checksum:
        raise ValueError("Checksum mismatch — wrong key or the file is corrupted")

    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        manifest = None
        for candidate in ("info.json", "manifest.json"):
            try:
                manifest = json.loads(zf.read(candidate).decode("utf-8"))
                break
            except KeyError:
                continue
        if manifest is None:
            manifest = {"name": os.path.basename(dpa_path), "entry": None, "dpa_version": 3}

    return zip_bytes, manifest

def unpack_dpa(dpa_path: str, dest_folder: str = None, key: str = None):
    """Extract a v3 binary .dpa package to a folder WITHOUT executing it."""
    import zipfile, io

    zip_bytes, manifest = _read_dpa_v3(dpa_path, key)
    if not dest_folder:
        dest_folder = os.path.splitext(dpa_path)[0] + "_extracted"
    os.makedirs(dest_folder, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(dest_folder)
    return dest_folder, manifest

def run_dpa_v3(dpa_path: str, key: str = None):
    """Decrypt, extract to a temp dir and execute the entry point of a v3 app package."""
    import zipfile, io, tempfile, shutil as _shutil

    zip_bytes, manifest = _read_dpa_v3(dpa_path, key)
    entry = manifest.get("entry")

    print(Fore.GREEN + f"✓ App:      {Fore.YELLOW}{manifest.get('name', '?')}")
    print(Fore.GREEN + f"✓ Entry:    {Fore.YELLOW}{entry or '(none found)'}")
    print(Fore.GREEN + f"✓ Packed:   {Fore.YELLOW}{manifest.get('created', '?')}")
    separator()

    if not entry:
        print_error("No entry point defined in manifest.json/info.json — cannot run. Use 'unpack' to inspect files instead.")
        return

    tmp_dir = tempfile.mkdtemp(prefix="dpa_run_")
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(tmp_dir)

        entry_path = os.path.join(tmp_dir, entry)
        if not os.path.exists(entry_path):
            print_error(f"Entry file missing inside package: {entry}")
            return

        with open(entry_path, "r", encoding="utf-8") as f:
            source = f.read()

        print(Fore.CYAN + "▶ Executing...\n")
        separator()

        ns = {"__name__": "__main__", "__file__": entry_path}
        
        # Save old working directory and change to temp directory so relative asset references work
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        sys.path.insert(0, tmp_dir)
        try:
            compiled = compile(source, entry_path, "exec")
            exec(compiled, ns)
            separator()
            print_success("App finished successfully!")
        except SystemExit:
            separator()
            print_info("App called sys.exit().")
        except SyntaxError as e:
            separator()
            print_error(f"SyntaxError: {e.msg} (line {e.lineno})")
            suggest_fix(source, e)
        except Exception as e:
            import traceback as _tb
            separator()
            print_error(f"{type(e).__name__}: {e}")
            tb_lines = _tb.format_exception(type(e), e, e.__traceback__)
            for tl in tb_lines[-3:]:
                print(Fore.RED + tl.rstrip())
            suggest_fix(source, e)
        finally:
            # Restore working directory
            os.chdir(old_cwd)
            if tmp_dir in sys.path:
                sys.path.remove(tmp_dir)
    finally:
        _shutil.rmtree(tmp_dir, ignore_errors=True)

def suggest_fix(source: str, error: Exception):
    """Print a friendly fix hint for common Python errors."""
    src_lines = source.splitlines()
    msg = str(error)
    print(Fore.YELLOW + "\n💡 Fix suggestion:" + Style.RESET_ALL)

    # SyntaxError → location info
    if isinstance(error, SyntaxError) and error.lineno:
        ln = error.lineno
        if 1 <= ln <= len(src_lines):
            bad = src_lines[ln - 1]
            print(Fore.WHITE + f"   Line {ln}: " + Fore.RED + bad)

            # Unterminated string literal
            if 'unterminated' in msg.lower() or 'EOL while scanning' in msg:
                # try to close last unmatched quote
                fixed = bad
                if bad.count('"') % 2 == 1:
                    fixed = bad + '"'
                elif bad.count("'") % 2 == 1:
                    fixed = bad + "'"
                print(Fore.GREEN + f"   Try:    {fixed}")
                return
            # Missing parenthesis
            if bad.count('(') > bad.count(')'):
                print(Fore.GREEN + f"   Try:    {bad + ')' * (bad.count('(') - bad.count(')'))}")
                return
            print(Fore.WHITE + "   Check brackets, quotes, and colons on this line.")
            return

    # NameError → check typos
    if isinstance(error, NameError):
        # extract name
        import re as _re
        m = _re.search(r"name '([^']+)' is not defined", msg)
        if m:
            bad_name = m.group(1)
            if bad_name in _COMMON_TYPOS:
                fix = _COMMON_TYPOS[bad_name]
                print(Fore.WHITE + f"   '{bad_name}' is not a function. " +
                      Fore.GREEN + f"Did you mean: {fix}?")
                # Find line & rewrite
                for i, ln in enumerate(src_lines, 1):
                    if bad_name in ln:
                        print(Fore.WHITE + f"   Line {i}: " + Fore.RED + ln)
                        print(Fore.GREEN + f"   Try:    {ln.replace(bad_name, fix)}")
                        break
                return
            print(Fore.WHITE + f"   '{bad_name}' is not defined. Check spelling or define it first.")
            return

    print(Fore.WHITE + "   " + msg)

def run_dpa(filepath: str, key: str = None):
    """Decrypt (if needed) and execute a .dpa file. Auto-detects legacy text (v1/v2)
    vs. the new binary ZIP-based app package (v3) by checking the file's magic bytes."""
    try:
        with open(filepath, "rb") as f:
            head = f.read(len(DPA_MAGIC_V3))
    except Exception as e:
        print_error(f"Cannot read file: {e}")
        return

    # ---- NEW v3: binary ZIP-based encrypted app package ----
    if head == DPA_MAGIC_V3:
        print(Fore.CYAN + Style.BRIGHT + "\n🚀 DPA RUNNER (v3 — Binary App Package)\n")
        separator()
        try:
            run_dpa_v3(filepath, key)
        except Exception as e:
            separator()
            print_error(f"Failed to run .dpa app: {e}")
            print_info("Tip: pass the correct key with 'dpa <file> <key>' if it was packed with a custom key.")
        separator()
        return

    # ---- Legacy v1/v2 (single-file, text-based) ----
    print(Fore.CYAN + Style.BRIGHT + "\n🚀 DPA RUNNER\n")
    separator()
    print(Fore.GREEN + f"✓ File:   {Fore.YELLOW}{os.path.basename(filepath)}")
    print(Fore.GREEN + f"✓ Path:   {Fore.YELLOW}{filepath}")
    try:
        size = os.path.getsize(filepath)
        print(Fore.GREEN + f"✓ Size:   {Fore.YELLOW}{size:,} bytes")
    except Exception:
        pass

    try:
        source = decrypt_dpa(filepath, key)
    except Exception as e:
        separator()
        print_error(f"Failed to decrypt .dpa file: {e}")
        print_info("Tip: ensure the correct key is set in config.json (dpa_key) "
                   "or pass it as the 2nd argument: dpa <file> <key>")
        separator()
        return

    # Determine type for display
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first = f.readline().strip()
    except Exception:
        first = ""
    if first == DPA_HEADER_XOR:
        print(Fore.CYAN + "🔐 Type:   " + Fore.YELLOW + "Encrypted (Legacy v2, XOR+Base64)")
    elif first == DPA_HEADER_PLAIN:
        print(Fore.CYAN + "📄 Type:   " + Fore.YELLOW + "Plain Python (v1)")
    else:
        print(Fore.CYAN + "📄 Type:   " + Fore.YELLOW + "Legacy (no header)")
    separator()
    print(Fore.CYAN + "▶ Executing...\n")
    separator()

    # Execute in isolated namespace
    ns = {"__name__": "__main__", "__file__": filepath}
    try:
        compiled = compile(source, filepath, "exec")
        exec(compiled, ns)
        separator()
        print_success("Script finished successfully!")
    except SystemExit:
        separator()
        print_info("Script called sys.exit().")
    except SyntaxError as e:
        separator()
        print_error(f"SyntaxError: {e.msg} (line {e.lineno})")
        suggest_fix(source, e)
    except Exception as e:
        import traceback as _tb
        separator()
        print_error(f"{type(e).__name__}: {e}")
        # Show short traceback
        tb_lines = _tb.format_exception(type(e), e, e.__traceback__)
        for tl in tb_lines[-3:]:
            print(Fore.RED + tl.rstrip())
        suggest_fix(source, e)
    separator()

def open_dpa_file(filepath):
    """Entry point for .dpa files. Auto-detects v3 binary app packages vs legacy
    text-based (v1/v2) scripts and offers the right menu for each."""
    print(Fore.CYAN + Style.BRIGHT + "\n🔐 DPA FILE HANDLER\n")
    separator()
    print(Fore.GREEN + f"✓ File:   {Fore.YELLOW}{os.path.basename(filepath)}")

    try:
        with open(filepath, "rb") as f:
            head = f.read(len(DPA_MAGIC_V3))
    except Exception as e:
        print_error(f"Cannot read file: {e}")
        return

    # ---- NEW v3: binary ZIP-based app package ----
    if head == DPA_MAGIC_V3:
        print(Fore.CYAN + "📦 Binary DPA App (v3, ZIP + Encrypted)")
        separator()
        print(Fore.WHITE + "  1. " + Fore.GREEN  + "Run app")
        print(Fore.WHITE + "  2. " + Fore.YELLOW + "Extract to folder")
        print(Fore.WHITE + "  3. " + Fore.MAGENTA + "Show info / manifest")
        print(Fore.WHITE + "  0. " + Fore.CYAN   + "Cancel")
        separator()
        choice = input(Fore.YELLOW + "Choice (0-3): " + Fore.WHITE).strip()
        if choice == "1":
            run_dpa(filepath)
        elif choice == "2":
            dest = input(Fore.YELLOW + "Extract to folder (blank = auto): " + Fore.WHITE).strip() or None
            try:
                dest_folder, manifest = unpack_dpa(filepath, dest)
                print_success(f"Extracted → {Fore.YELLOW}{dest_folder}")
            except Exception as e:
                print_error(f"Extract failed: {e}")
        elif choice == "3":
            try:
                zip_bytes, manifest = _read_dpa_v3(filepath)
                print(Fore.CYAN + f"\n🧾 MANIFEST: {os.path.basename(filepath)}\n")
                separator()
                for k, v in manifest.items():
                    print(Fore.WHITE + f"  {k:<12} " + Fore.YELLOW + str(v))
                separator()
            except Exception as e:
                print_error(f"Failed to read info: {e}")
        else:
            print_info("Cancelled")
        return

    # ---- Legacy v1/v2 (single-file, text-based) ----
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first = f.readline().strip()
    except Exception as e:
        print_error(f"Cannot read file: {e}")
        return
    is_encrypted = (first == DPA_HEADER_XOR)
    print(Fore.CYAN + ("🔒 Encrypted DPA (Legacy v2 text)" if is_encrypted else "📄 Plain DPA (Legacy v1 text)"))
    separator()
    print(Fore.WHITE + "  1. " + Fore.GREEN  + "Run script")
    print(Fore.WHITE + "  2. " + Fore.YELLOW + "View source code")
    print(Fore.WHITE + "  0. " + Fore.CYAN   + "Cancel")
    separator()
    choice = input(Fore.YELLOW + "Choice (0-2): " + Fore.WHITE).strip()
    if choice == "1":
        run_dpa(filepath)
    elif choice == "2":
        try:
            source = decrypt_dpa(filepath)
        except Exception as e:
            print_error(f"Failed to decrypt: {e}")
            return
        print(Fore.CYAN + f"\n📄 SOURCE: {os.path.basename(filepath)}\n")
        separator()
        for i, line in enumerate(source.splitlines(), 1):
            print(Fore.WHITE + f"{i:>4}  " + Fore.YELLOW + line)
        separator()
    else:
        print_info("Cancelled")


def main():
    global CONFIG, THEMES, current_path
    CONFIG = load_config()
    THEMES = load_themes()
    apply_theme()
    init_base_help()
    load_history()
    load_plugins()

    os.system('cls' if os.name == 'nt' else 'clear')
    print_logo()
    print(Fore.CYAN + "Initializing DCMDS..." + Style.RESET_ALL)
    animated_separator()
    print_success("System Ready!")
    separator()
    
    print(Fore.YELLOW + Style.BRIGHT + "\n🎯 DCMDS - Danrode CMD System")
    print(Fore.WHITE + "Advanced Python Terminal with Enhanced Features")
    print(Fore.CYAN + "\nType " + Fore.GREEN + "'help'" + Fore.CYAN + " to see all available commands")
    separator()
    
    while True:
        global active_app, web_mode, current_url
        bracket_color = _color_from_name(ACTIVE_THEME.get("prompt_bracket", "YELLOW"), Fore.YELLOW)
        path_color    = _color_from_name(ACTIVE_THEME.get("prompt_path",    "GREEN"),  Fore.GREEN)
        label_color   = _color_from_name(ACTIVE_THEME.get("prompt_label",   "CYAN"),   Fore.CYAN)
        
        base_prompt = ""
        if current_path:
            base_prompt = f"{bracket_color}[{path_color}{current_path}{bracket_color}]"
            
        if web_mode:
            site_label = Fore.MAGENTA + (current_url or "google.com")
            prompt = f"{Fore.WHITE}WEB ({site_label}){Fore.WHITE} DCMDS{label_color}>{Fore.WHITE} "
        elif active_app:
            exit_label = Fore.RED + "Exit"
            prompt = f"{base_prompt} {Fore.WHITE}{active_app} ({exit_label}){Fore.WHITE} DCMDS{label_color}>{Fore.WHITE} "
        else:
            prompt = f"{base_prompt}{Fore.WHITE} DCMDS{label_color}>{Fore.WHITE} "
        
        if not base_prompt and not active_app:
             prompt = f"{Fore.WHITE}DCMDS{label_color}>{Fore.WHITE} "
    
        cmd = input(prompt).strip()
        if not cmd:
            continue

        append_history(cmd)

        # ---- ALIAS EXPANSION ----
        _alias_map = CONFIG.get("aliases", {})
        _first_word = cmd.split()[0].lower() if cmd.split() else ""
        if _first_word in _alias_map and _first_word != "alias":
            _rest_parts = cmd.split(maxsplit=1)
            _rest = _rest_parts[1] if len(_rest_parts) > 1 else ""
            cmd = (_alias_map[_first_word] + " " + _rest).strip()

        separator()
    
        # ---- EXIT ----
        if cmd.lower() in ["exit", "bsx"]:
            if active_app or web_mode:
                print_info(f"Closing {active_app or 'Web Mode'}...")
                active_app = None
                web_mode = False
                current_url = None
                continue
            print(Fore.YELLOW + "Shutting down DCMDS...")
            animated_separator()
            print_success("Goodbye! 👋")
            break
    
        # ---- HELP ----
        elif cmd.lower().startswith("help"):
            parts = cmd.split(maxsplit=1)
            topic = parts[1] if len(parts) > 1 else None
            show_help(topic)

        # ---- NEW ----
        elif cmd.lower() == "new":
            print(Fore.CYAN + Style.BRIGHT + "\n🆕 NEW COMMANDS IN DCMDS VERSION 0.0.7\n")
            separator()
            print(Fore.WHITE + "  ⬛ " + Fore.GREEN + "cmd" + Fore.WHITE + "               — run real Windows CMD commands, or a live CMD session")
            print(Fore.WHITE + "  📦 " + Fore.GREEN + "pack / unpack" + Fore.WHITE + "     — new binary ZIP-based .dpa app packages (APK-style)")
            print(Fore.WHITE + "  🧾 " + Fore.GREEN + "dpainfo" + Fore.WHITE + "           — inspect any .dpa file's format/manifest without running it")
            print(Fore.WHITE + "  🗜️  " + Fore.GREEN + "zip / unzip" + Fore.WHITE + "       — compress/extract folders and archives")
            print(Fore.WHITE + "  🔢 " + Fore.GREEN + "hash" + Fore.WHITE + "              — md5 / sha1 / sha256 file checksums")
            print(Fore.WHITE + "  📶 " + Fore.GREEN + "ping" + Fore.WHITE + "              — ping a network host")
            print(Fore.WHITE + "  🏷️  " + Fore.GREEN + "alias" + Fore.WHITE + "             — create your own custom command shortcuts")
            print(Fore.WHITE + "  ⚙️  " + Fore.GREEN + "sit" + Fore.WHITE + "               — configure settings (logo display, safe mode, history)")
            print(Fore.WHITE + "  🆕 " + Fore.GREEN + "new" + Fore.WHITE + "               — show this new commands reference screen")
            separator()

        # ---- SIT (Settings) ----
        elif cmd.lower() == "sit" or cmd.lower().startswith("sit "):
            parts = cmd.split()
            if len(parts) == 1:
                # Interactive settings dashboard
                print(Fore.CYAN + Style.BRIGHT + "\n⚙️  DCMDS SYSTEM SETTINGS (sit)\n")
                separator()
                
                logo_status = "ENABLED" if CONFIG.get("show_logo", True) else "DISABLED"
                safe_status = "ENABLED" if CONFIG.get("safe_mode", True) else "DISABLED"
                hist_status = "ENABLED" if CONFIG.get("history_enabled", True) else "DISABLED"
                
                print(f"  1. Logo Display:        {Fore.YELLOW}{logo_status}")
                print(f"  2. Safe Mode:           {Fore.YELLOW}{safe_status}")
                print(f"  3. History Logging:     {Fore.YELLOW}{hist_status}")
                print(f"  4. Current Theme:       {Fore.YELLOW}{CONFIG.get('theme', 'classic')}")
                separator()
                print(Fore.CYAN + "To change a setting, use: " + Fore.GREEN + "sit <option> <value>")
                print(Fore.WHITE + "Examples:\n  • " + Fore.GREEN + "sit logo off\n" + Fore.WHITE + "  • " + Fore.GREEN + "sit safe on\n" + Fore.WHITE + "  • " + Fore.GREEN + "sit history off")
                separator()
            elif len(parts) >= 3:
                setting = parts[1].lower()
                value = parts[2].lower()
                
                if setting == "logo":
                    if value in ["on", "true", "yes"]:
                        CONFIG["show_logo"] = True
                        save_config(CONFIG)
                        print_success("Logo display enabled.")
                    elif value in ["off", "false", "no"]:
                        CONFIG["show_logo"] = False
                        save_config(CONFIG)
                        print_success("Logo display disabled.")
                    else:
                        print_error("Invalid value. Use: on / off")
                
                elif setting in ["safe", "safemode"]:
                    if value in ["on", "true", "yes"]:
                        CONFIG["safe_mode"] = True
                        save_config(CONFIG)
                        print_success("Safe mode enabled.")
                    elif value in ["off", "false", "no"]:
                        CONFIG["safe_mode"] = False
                        save_config(CONFIG)
                        print_success("Safe mode disabled.")
                    else:
                        print_error("Invalid value. Use: on / off")
                
                elif setting in ["history", "hist"]:
                    if value in ["on", "true", "yes"]:
                        CONFIG["history_enabled"] = True
                        save_config(CONFIG)
                        print_success("History logging enabled.")
                    elif value in ["off", "false", "no"]:
                        CONFIG["history_enabled"] = False
                        save_config(CONFIG)
                        print_success("History logging disabled.")
                    else:
                        print_error("Invalid value. Use: on / off")
                
                else:
                    print_error(f"Unknown setting option: '{setting}'")
                separator()
            else:
                print_error("Usage: sit | sit logo <on/off> | sit safe <on/off> | sit history <on/off>")
                separator()

        # ---- HISTORY ----
        elif cmd.lower().startswith("history"):
            parts = cmd.split()
            if len(parts) == 1:
                count = 20
            elif len(parts) >= 2 and parts[1].lower() == "clear":
                HISTORY.clear()
                try:
                    with open(CONFIG.get("history_path", HISTORY_PATH), "w", encoding="utf-8"):
                        pass
                    print_success("History cleared")
                except Exception as e:
                    print_error(f"Failed to clear history: {e}")
                separator()
                continue
            elif len(parts) >= 3 and parts[1].lower() == "last" and parts[2].isdigit():
                count = int(parts[2])
            else:
                print_error("Usage: history | history last <n> | history clear")
                separator()
                continue

            if not HISTORY:
                print_info("No history yet")
            else:
                start_index = max(0, len(HISTORY) - count)
                print(Fore.CYAN + "\n🧾 Command History:\n")
                for i, entry in enumerate(HISTORY[start_index:], start=start_index + 1):
                    print(Fore.WHITE + f"{i}. " + Fore.YELLOW + entry)
            separator()

        # ---- THEME ----
        elif cmd.lower().startswith("theme"):
            parts = cmd.split()
            if len(parts) == 1 or (len(parts) >= 2 and parts[1].lower() == "list"):
                print(Fore.CYAN + "\n🎨 Available Themes:\n")
                for name in sorted(THEMES.keys()):
                    current = " (active)" if name == CONFIG.get("theme") else ""
                    print(Fore.WHITE + f"- {name}{current}")
                separator()
            elif len(parts) >= 3 and parts[1].lower() == "set":
                theme_name = parts[2]
                if theme_name in THEMES:
                    CONFIG["theme"] = theme_name
                    save_config(CONFIG)
                    apply_theme()
                    print_success(f"Theme set to: {theme_name}")
                else:
                    print_error("Theme not found")
                separator()
            else:
                print_error("Usage: theme | theme list | theme set <name>")
                separator()

        # ---- SAFE MODE ----
        elif cmd.lower().startswith("safe"):
            parts = cmd.split()
            if len(parts) == 1:
                state = "ON" if CONFIG.get("safe_mode", True) else "OFF"
                print(Fore.CYAN + f"Safe mode is {state}")
            elif len(parts) >= 2 and parts[1].lower() in ["on", "off"]:
                CONFIG["safe_mode"] = parts[1].lower() == "on"
                save_config(CONFIG)
                state = "ON" if CONFIG.get("safe_mode", True) else "OFF"
                print_success(f"Safe mode set to {state}")
            else:
                print_error("Usage: safe | safe on | safe off")
            separator()

        # ---- PLUGINS ----
        elif cmd.lower() == "plugins":
            print(Fore.CYAN + "\n🧩 Loaded Plugins:\n")
            if not LOADED_PLUGINS:
                print(Fore.WHITE + "No plugins loaded")
            else:
                for name in sorted(LOADED_PLUGINS):
                    print(Fore.WHITE + f"- {name}")
            separator()
            
        # ---- APPS ----
        elif cmd.lower() == "apps":
            list_apps()
            separator()
            
        # ---- EXIT INTERNAL APP / WEB ----
        elif (active_app or web_mode) and cmd.lower() == "exit":
            print_info(f"Closing {active_app or 'Web Mode'}...")
            active_app = None
            web_mode = False
            current_url = None
            continue
            
        # ---- WEB COMMAND ----
        elif cmd.lower() == "web":
            web_mode = True
            current_url = "google.com"
            print_success("Connected to Web. Site: google.com")
            print_info("Type 'm' to open embedded browser window or 'exit' to disconnect.")
            continue
            
        # ---- M TOGGLE (WEB) ----
        elif web_mode and cmd.lower() == "m":
            print_info("Opening embedded browser window...")
            embedded_browser()
            continue

        # ---- TASKS ----
        elif cmd.lower() == "tasks":
            show_tasks()
    
        elif cmd.lower() == "tasks browse":
            browse_tasks()
    
        elif cmd.lower() in ["x", "y", "tb"]:
            browse_tasks()
    
        # ---- END TASK ----
        elif cmd.lower().startswith("end "):
            if safe_mode_blocked("end"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            pid_str = cmd[4:].strip()
            if not pid_str.isdigit():
                print_error("Invalid PID. Must be a number.")
            else:
                pid = int(pid_str)
                try:
                    process = psutil.Process(pid)
                    proc_name = process.name()
    
                    print(Fore.RED + f"⚠️  End task: {proc_name} (PID: {pid})?")
                    confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
    
                    if confirm == 'yes':
                        try:
                            process.terminate()
                            time.sleep(0.5)
                            if process.is_running():
                                process.kill()
                            print_success(f"Task ended: {proc_name} (PID: {pid})")
                        except psutil.AccessDenied:
                            print_error("Access denied - cannot end this task (try running as administrator)")
                        except Exception as e:
                            print_error(f"Failed to end task: {e}")
                    else:
                        print_info("Cancelled")
    
                except psutil.NoSuchProcess:
                    print_error(f"Process with PID {pid} not found")
                except Exception as e:
                    print_error(f"Error: {e}")
    
        # ---- RESTART TASK ----
        elif cmd.lower().startswith("restart "):
            if safe_mode_blocked("restart_pid"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            pid_str = cmd[8:].strip()
            if not pid_str.isdigit():
                print_error("Invalid PID. Must be a number.")
            else:
                pid = int(pid_str)
                try:
                    process = psutil.Process(pid)
                    proc_name = process.name()
                    exe_path = process.exe()
    
                    print(Fore.YELLOW + f"🔄 Restart task: {proc_name} (PID: {pid})?")
                    confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
    
                    if confirm == 'yes':
                        try:
                            process.terminate()
                            time.sleep(0.5)
                            if process.is_running():
                                process.kill()
                            time.sleep(1)
                            subprocess.Popen([exe_path])
                            print_success(f"Task restarted: {proc_name}")
                        except psutil.AccessDenied:
                            print_error("Access denied - cannot restart this task (try running as administrator)")
                        except Exception as e:
                            print_error(f"Failed to restart task: {e}")
                    else:
                        print_info("Cancelled")
    
                except psutil.NoSuchProcess:
                    print_error(f"Process with PID {pid} not found")
                except Exception as e:
                    print_error(f"Error: {e}")
    
        # ---- CLEAR ----
        elif cmd.lower() == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_logo()
            print_success("Screen cleared!")
    
        # ---- VERSION ----
        elif cmd.lower() == "version":
            print(Fore.CYAN + Style.BRIGHT + "\n📊 DCMDS VERSION INFORMATION\n")
            separator()
            print(Fore.WHITE + "System Name:     " + Fore.YELLOW + "DCMDS (Danrode CMD System)")
            print(Fore.WHITE + "Version:         " + Fore.GREEN + "0.0.7")
            print(Fore.WHITE + "Stage:           " + Fore.RED + "Alpha (Under Development)")
            print(Fore.WHITE + "Build:           " + Fore.CYAN + "jul,  15, 2026")
            print(Fore.WHITE + "Creator:         " + Fore.MAGENTA + "Danrode")
            separator()
            print(Fore.YELLOW + Style.BRIGHT + "\n🆕 New in v0.0.7:")
            print(Fore.WHITE + "  ⬛ " + Fore.GREEN + "cmd" + Fore.WHITE + "               — run real Windows CMD commands, or a live CMD session")
            print(Fore.WHITE + "  📦 " + Fore.GREEN + "pack / unpack" + Fore.WHITE + "     — new binary ZIP-based .dpa app packages (APK-style)")
            print(Fore.WHITE + "  🧾 " + Fore.GREEN + "dpainfo" + Fore.WHITE + "           — inspect any .dpa file's format/manifest without running it")
            print(Fore.WHITE + "  🗜️  " + Fore.GREEN + "zip / unzip" + Fore.WHITE + "       — compress/extract folders and archives")
            print(Fore.WHITE + "  🔢 " + Fore.GREEN + "hash" + Fore.WHITE + "              — md5 / sha1 / sha256 file checksums")
            print(Fore.WHITE + "  📶 " + Fore.GREEN + "ping" + Fore.WHITE + "              — ping a network host")
            print(Fore.WHITE + "  🏷️  " + Fore.GREEN + "alias" + Fore.WHITE + "             — create your own custom command shortcuts")
            separator()
            print(Fore.YELLOW + "\n📝 Version Format: Alpha.Beta.Version")
            print(Fore.WHITE + "• " + Fore.RED + "0" + Fore.WHITE + ".x.x = Alpha (Under Development)")
            print(Fore.WHITE + "• x." + Fore.YELLOW + "0" + Fore.WHITE + ".x = Beta Testing")
            print(Fore.WHITE + "• x.x." + Fore.GREEN + "1" + Fore.WHITE + " = Version Number (Official Release)")
    
        # ---- DPA COMMAND (AUTO) ----
        elif cmd.lower().startswith("dpa ") and False:
            # NOTE: handled by the explicit "dpa " block further below (kept as
            # a single source of truth so v3 binary + legacy files both work).
            pass
    
        # ---- DEBUG ----
        elif cmd.lower() == "debug":
            print(Fore.RED + Style.BRIGHT + "\n🔧 DCMDS SYSTEM DIAGNOSTICS\n")
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "📦 DCMDS INFORMATION:")
            print(Fore.WHITE + "  System Name:    " + Fore.YELLOW + "DCMDS (Danrode CMD System)")
            print(Fore.WHITE + "  Version:        " + Fore.GREEN + "0.0.7 (Alpha)")
            print(Fore.WHITE + "  Build Date:     " + Fore.CYAN + "jul,  15, 2026")
            print(Fore.WHITE + "  Current Path:   " + Fore.YELLOW + (current_path if current_path else "None"))
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "🐍 PYTHON INFORMATION:")
            print(Fore.WHITE + "  Python Version: " + Fore.GREEN + sys.version.split()[0])
            print(Fore.WHITE + "  Full Version:   " + Fore.YELLOW + sys.version.replace('\n', ' '))
            print(Fore.WHITE + "  Executable:     " + Fore.CYAN + sys.executable)
            print(Fore.WHITE + "  Platform:       " + Fore.MAGENTA + sys.platform)
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "🪟 WINDOWS INFORMATION:")
            print(Fore.WHITE + "  OS:             " + Fore.YELLOW + platform.system() + " " + platform.release())
            print(Fore.WHITE + "  Version:        " + Fore.GREEN + platform.version())
            print(Fore.WHITE + "  Edition:        " + Fore.CYAN + platform.win32_edition())
            print(Fore.WHITE + "  Architecture:   " + Fore.MAGENTA + platform.machine())
            print(Fore.WHITE + "  Computer Name:  " + Fore.YELLOW + platform.node())
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "💻 PROCESSOR INFORMATION:")
            print(Fore.WHITE + "  Processor:      " + Fore.YELLOW + platform.processor())
            print(Fore.WHITE + "  Architecture:   " + Fore.GREEN + platform.architecture()[0])
            print(Fore.WHITE + "  CPU Cores:      " + Fore.CYAN + f"{psutil.cpu_count(logical=False)} Physical, {psutil.cpu_count(logical=True)} Logical")
            print(Fore.WHITE + "  CPU Usage:      " + Fore.MAGENTA + f"{psutil.cpu_percent(interval=1)}%")
    
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    print(Fore.WHITE + "  CPU Frequency:  " + Fore.YELLOW + f"{cpu_freq.current:.2f} MHz (Max: {cpu_freq.max:.2f} MHz)")
            except:
                pass
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "🧠 MEMORY INFORMATION:")
            memory = psutil.virtual_memory()
            print(Fore.WHITE + "  Total RAM:      " + Fore.GREEN + f"{memory.total / (1024**3):.2f} GB")
            print(Fore.WHITE + "  Available:      " + Fore.YELLOW + f"{memory.available / (1024**3):.2f} GB")
            print(Fore.WHITE + "  Used:           " + Fore.RED + f"{memory.used / (1024**3):.2f} GB ({memory.percent}%)")
            print(Fore.WHITE + "  Free:           " + Fore.CYAN + f"{memory.free / (1024**3):.2f} GB")
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "💾 DISK INFORMATION:")
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    print(Fore.WHITE + f"  Drive {partition.device}")
                    print(Fore.WHITE + f"    Total:        " + Fore.GREEN + f"{usage.total / (1024**3):.2f} GB")
                    print(Fore.WHITE + f"    Used:         " + Fore.RED + f"{usage.used / (1024**3):.2f} GB ({usage.percent}%)")
                    print(Fore.WHITE + f"    Free:         " + Fore.CYAN + f"{usage.free / (1024**3):.2f} GB")
                    print(Fore.WHITE + f"    File System:  " + Fore.YELLOW + partition.fstype)
                except:
                    pass
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "🌐 NETWORK INFORMATION:")
            net_if_addrs = psutil.net_if_addrs()
            for interface_name, interface_addresses in net_if_addrs.items():
                print(Fore.WHITE + f"  Interface: " + Fore.YELLOW + interface_name)
                for address in interface_addresses:
                    if str(address.family) == 'AddressFamily.AF_INET':
                        print(Fore.WHITE + f"    IP Address:   " + Fore.GREEN + address.address)
                    elif str(address.family) == 'AddressFamily.AF_LINK':
                        print(Fore.WHITE + f"    MAC Address:  " + Fore.CYAN + address.address)
    
            separator()
    
            print(Fore.CYAN + Style.BRIGHT + "📚 LOADED MODULES:")
            modules = ['colorama', 'cv2', 'psutil', 'datetime', 'subprocess', 'base64']
            for module in modules:
                if module in sys.modules:
                    print(Fore.WHITE + f"  ✓ {module:<15} " + Fore.GREEN + "Loaded")
                else:
                    print(Fore.WHITE + f"  ✗ {module:<15} " + Fore.RED + "Not Loaded")
    
            separator()
    
            print(Fore.YELLOW + Style.BRIGHT + "\n⚙️  ACCESS OPTIONS:")
            print(Fore.WHITE + "  1. " + Fore.GREEN + "Export Debug Log to File")
            print(Fore.WHITE + "  2. " + Fore.GREEN + "Show Environment Variables")
            print(Fore.WHITE + "  3. " + Fore.GREEN + "Show Running Processes")
            print(Fore.WHITE + "  4. " + Fore.GREEN + "Network Statistics")
            print(Fore.WHITE + "  5. " + Fore.GREEN + "Battery Information")
            print(Fore.WHITE + "  0. " + Fore.CYAN + "Exit Debug Mode")
    
            while True:
                choice = input(Fore.YELLOW + "\nSelect option (0-5): " + Fore.WHITE).strip()
    
                if choice == "0":
                    print_info("Exited debug mode")
                    break
    
                elif choice == "1":
                    try:
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"dcmds_debug_{timestamp}.txt"
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write("DCMDS DEBUG LOG\n")
                            f.write("=" * 50 + "\n\n")
                            f.write(f"Generated: {datetime.datetime.now()}\n\n")
                            f.write(f"DCMDS Version: 0.0.7 (Alpha)\n")
                            f.write(f"Build Date: jul,  15, 2026\n")
                            f.write(f"Python Version: {sys.version}\n")
                            f.write(f"OS: {platform.system()} {platform.release()}\n")
                            f.write(f"Processor: {platform.processor()}\n")
                            f.write(f"RAM: {psutil.virtual_memory().total / (1024**3):.2f} GB\n")
                        print_success(f"Debug log saved: {Fore.YELLOW}{filename}")
                    except Exception as e:
                        print_error(f"Failed to save log: {e}")
    
                elif choice == "2":
                    print(Fore.CYAN + "\n📝 ENVIRONMENT VARIABLES:")
                    separator()
                    for key, value in sorted(os.environ.items())[:10]:
                        print(Fore.WHITE + f"  {key:<20} " + Fore.YELLOW + f"{value[:50]}...")
                    print(Fore.CYAN + f"\n  ... and {len(os.environ) - 10} more")
    
                elif choice == "3":
                    print(Fore.CYAN + "\n⚙️  TOP 10 PROCESSES:")
                    separator()
                    processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                        try:
                            processes.append(proc.info)
                        except:
                            pass
                    processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]
                    for proc in processes:
                        print(Fore.WHITE + f"  {proc['name']:<25} " + 
                              Fore.CYAN + f"PID: {proc['pid']:<8} " + 
                              Fore.YELLOW + f"CPU: {proc['cpu_percent']:.1f}% " + 
                              Fore.GREEN + f"RAM: {proc['memory_percent']:.1f}%")
    
                elif choice == "4":
                    print(Fore.CYAN + "\n🌐 NETWORK STATISTICS:")
                    separator()
                    net_io = psutil.net_io_counters()
                    print(Fore.WHITE + f"  Bytes Sent:     " + Fore.GREEN + f"{net_io.bytes_sent / (1024**2):.2f} MB")
                    print(Fore.WHITE + f"  Bytes Received: " + Fore.YELLOW + f"{net_io.bytes_recv / (1024**2):.2f} MB")
                    print(Fore.WHITE + f"  Packets Sent:   " + Fore.CYAN + f"{net_io.packets_sent}")
                    print(Fore.WHITE + f"  Packets Recv:   " + Fore.MAGENTA + f"{net_io.packets_recv}")
    
                elif choice == "5":
                    try:
                        battery = psutil.sensors_battery()
                        if battery:
                            print(Fore.CYAN + "\n🔋 BATTERY INFORMATION:")
                            separator()
                            print(Fore.WHITE + f"  Charge:         " + Fore.GREEN + f"{battery.percent}%")
                            print(Fore.WHITE + f"  Plugged In:     " + (Fore.GREEN + "Yes" if battery.power_plugged else Fore.RED + "No"))
                            if battery.secsleft != -1:
                                hours = battery.secsleft // 3600
                                minutes = (battery.secsleft % 3600) // 60
                                print(Fore.WHITE + f"  Time Left:      " + Fore.YELLOW + f"{hours}h {minutes}m")
                        else:
                            print_info("No battery detected (Desktop PC)")
                    except:
                        print_error("Battery information not available")
    
                else:
                    print_error("Invalid option")
    
        # ---- BC (List Drives) ----
        elif cmd.lower() == "bc":
            drives = list_drives()
            if not drives:
                print_error("No drives found!")
            else:
                selected = 0
                browsing = True
    
                while browsing:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print_logo()
                    print(Fore.CYAN + Style.BRIGHT + "\n💾 AVAILABLE DRIVES")
                    print(Fore.WHITE + "Use ↑↓ arrows, Enter to select, ESC to cancel\n")
                    separator()
    
                    for i, drive in enumerate(drives):
                        if i == selected:
                            print(Back.GREEN + Fore.BLACK + "► " + drive + " " * 20)
                        else:
                            print(Fore.YELLOW + "  " + drive)
    
                    separator()
                    print(Fore.GREEN + f"\nSelected: " + Fore.YELLOW + drives[selected])
                    print(Fore.CYAN + "\n↑↓ Navigate | Enter Select | ESC Cancel")
    
                    key = msvcrt.getch()
    
                    if key == b'\xe0':
                        key = msvcrt.getch()
                        if key == b'H':
                            selected = (selected - 1) % len(drives)
                        elif key == b'P':
                            selected = (selected + 1) % len(drives)
    
                    elif key == b'\r':
                        current_path = drives[selected]
                        print_success(f"\nCurrent path set to: {Fore.YELLOW}{current_path}")
                        browsing = False
    
                    elif key == b'\x1b':
                        print_info("\nSelection cancelled")
                        browsing = False
    
                    elif key.lower() == b'c':
                        current_path = drives[selected]
                        print_success(f"\nCurrent path set to: {Fore.YELLOW}{current_path}")
                        browsing = False
    
        # ---- Drive Shortcut ----
        elif len(cmd) == 1 and cmd.upper() + ":\\" in list_drives():
            current_path = cmd.upper() + ":\\"
            print_success(f"Current path set to: {Fore.YELLOW}{current_path}")
    
        # ---- Quick CD with >> ----
        elif cmd.startswith(">> "):
            target = cmd[3:].strip()
            if not current_path:
                print_error("No current path. Choose drive first.")
            else:
                new_path = os.path.join(current_path, target)
                if os.path.isdir(new_path):
                    current_path = new_path
                    print_success(f"Entered folder: {Fore.YELLOW}{current_path}")
                else:
                    print_error("Folder not found")
    
        # ---- Go Back (..) ----
        elif cmd == "..":
            if not current_path:
                print_error("No current path selected")
            else:
                if len(current_path) <= 3:
                    print_info(f"Exiting from {Fore.YELLOW}{current_path}")
                    current_path = None
                    print_success("Returned to drive selection. Use " + Fore.GREEN + "'bc'" + Fore.CYAN + " to choose a drive")
                else:
                    parent = os.path.dirname(current_path.rstrip("\\"))
                    if parent and len(parent) > 2:
                        current_path = parent
                        print_success(f"Moved to: {Fore.YELLOW}{current_path}")
                    else:
                        current_path = parent + "\\"
                        print_success(f"Moved to root: {Fore.YELLOW}{current_path}")
    
        # ---- CD ----
        elif cmd.lower().startswith("cd "):
            target = cmd[3:].strip()
            if not current_path:
                print_error("No current path. Choose drive first.")
            else:
                new_path = os.path.join(current_path, target)
                if os.path.isdir(new_path):
                    current_path = new_path
                    print_success(f"Entered folder: {Fore.YELLOW}{current_path}")
                else:
                    print_error("Folder not found")
    
        # ---- CDT ----
        elif cmd.lower() == "cdt":
            if current_path:
                print_info(f"Current path: {Fore.YELLOW}{current_path}")
            else:
                print_error("No path selected")
    
        # ---- LS ----
        elif cmd.lower() == "ls":
            show_items()
    
        # ---- BROWSE ----
        elif cmd.lower() == "browse":
            selected_file = browse_files()
            if selected_file:
                separator()
                print_success(f"Selected: {Fore.YELLOW}{selected_file}")
                print(Fore.CYAN + "What do you want to do?")
                print(Fore.WHITE + "1. " + Fore.GREEN + "Open file")
                print(Fore.WHITE + "2. " + Fore.GREEN + "Enter folder")
                print(Fore.WHITE + "3. " + Fore.GREEN + "Copy name to clipboard")
                print(Fore.WHITE + "4. " + Fore.GREEN + "Use in command (type command)")
    
                action = input(Fore.YELLOW + "\nChoice (1-4): ").strip()
    
                if action == "1":
                    full_path = os.path.join(current_path, selected_file)
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(full_path)[1].lower()
                        if ext == ".dpa":
                            open_dpa_file(full_path)
                        else:
                            print_output(f"Opening {Fore.YELLOW}{selected_file}")
                            os.startfile(full_path)
                    else:
                        print_error("Cannot open folder, use option 2")
    
                elif action == "2":
                    full_path = os.path.join(current_path, selected_file)
                    if os.path.isdir(full_path):
                        current_path = full_path
                        print_success(f"Entered: {Fore.YELLOW}{current_path}")
                    else:
                        print_error("Not a folder!")
    
                elif action == "3":
                    try:
                        os.system(f'echo {selected_file}| clip')
                        print_success(f"Copied to clipboard: {Fore.YELLOW}{selected_file}")
                    except:
                        print_error("Failed to copy to clipboard")
    
                elif action == "4":
                    user_cmd = input(Fore.GREEN + f"Command for '{selected_file}': " + Fore.WHITE).strip()
                    if user_cmd:
                        full_cmd = f"{user_cmd} {selected_file}"
                        print_info(f"Executing: {Fore.YELLOW}{full_cmd}")

        # ---- DPA (explicit command, handles both v3 binary & legacy) ----
        elif cmd.lower().startswith("dpa "):
            # dpa <file> [key]  → run binary v3 app OR legacy text dpa
            parts = cmd.split(maxsplit=2)
            name = parts[1] if len(parts) > 1 else ""
            key  = parts[2] if len(parts) > 2 else None
            if not name:
                print_error("Usage: dpa <file.dpa> [key]")
            else:
                if os.path.isabs(name):
                    path = name
                elif current_path:
                    path = os.path.join(current_path, name)
                else:
                    path = name
                if not os.path.exists(path) and not name.lower().endswith(".dpa"):
                    alt = path + ".dpa"
                    if os.path.exists(alt):
                        path = alt
                if os.path.exists(path):
                    run_dpa(path, key)
                else:
                    print_error(f"File not found: {name}")

        # ---- PACK (folder → binary encrypted .dpa v3 app package) ----
        elif cmd.lower().startswith("pack "):
            parts = cmd.split(maxsplit=3)
            if len(parts) < 2:
                print_error("Usage: pack <folder> [output.dpa] [key]")
            else:
                folder = parts[1]
                out = parts[2] if len(parts) > 2 else None
                key = parts[3] if len(parts) > 3 else None
                if not os.path.isabs(folder) and current_path:
                    folder = os.path.join(current_path, folder)
                if out and not os.path.isabs(out) and current_path:
                    out = os.path.join(current_path, out)
                if not os.path.isdir(folder):
                    print_error(f"Folder not found: {folder}")
                else:
                    try:
                        result_path = pack_to_dpa(folder, out, key)
                        print_success(f"Packed → {Fore.YELLOW}{result_path}")
                        used_key = key or CONFIG.get("dpa_key", DEFAULT_DPA_KEY)
                        print_info(f"Key used: {used_key}")
                        print_info("Tip: use 'dpainfo' or 'unpack' to inspect the package, 'dpa' to run it.")
                    except Exception as e:
                        print_error(f"Packing failed: {e}")

        # ---- UNPACK (extract .dpa v3 without running it) ----
        elif cmd.lower().startswith("unpack "):
            parts = cmd.split(maxsplit=3)
            if len(parts) < 2:
                print_error("Usage: unpack <file.dpa> [dest] [key]")
            else:
                name = parts[1]
                dest = parts[2] if len(parts) > 2 else None
                key = parts[3] if len(parts) > 3 else None
                path = name if os.path.isabs(name) else (os.path.join(current_path, name) if current_path else name)
                if dest and not os.path.isabs(dest) and current_path:
                    dest = os.path.join(current_path, dest)
                if not os.path.exists(path):
                    print_error(f"File not found: {name}")
                else:
                    try:
                        dest_folder, manifest = unpack_dpa(path, dest, key)
                        print_success(f"Extracted → {Fore.YELLOW}{dest_folder}")
                        print_info(f"App: {manifest.get('name')}   Entry: {manifest.get('entry')}")
                    except Exception as e:
                        print_error(f"Unpack failed: {e}")

        # ---- DPAINFO (inspect any .dpa without running it) ----
        elif cmd.lower().startswith("dpainfo "):
            name = cmd[8:].strip()
            path = name if os.path.isabs(name) else (os.path.join(current_path, name) if current_path else name)
            if not os.path.exists(path):
                print_error(f"File not found: {name}")
            else:
                try:
                    with open(path, "rb") as f:
                        head = f.read(len(DPA_MAGIC_V3))
                    print(Fore.CYAN + Style.BRIGHT + f"\n🧾 DPA INFO: {os.path.basename(path)}\n")
                    separator()
                    if head == DPA_MAGIC_V3:
                        zip_bytes, manifest = _read_dpa_v3(path)
                        print(Fore.WHITE + "Format:       " + Fore.GREEN + "v3 (Binary ZIP, encrypted)")
                        print(Fore.WHITE + "App Name:     " + Fore.YELLOW + str(manifest.get("name", "?")))
                        print(Fore.WHITE + "Entry Point:  " + Fore.YELLOW + str(manifest.get("entry")))
                        print(Fore.WHITE + "Created:      " + Fore.CYAN + str(manifest.get("created", "?")))
                        print(Fore.WHITE + "File Size:    " + Fore.MAGENTA + f"{os.path.getsize(path):,} bytes")
                        import zipfile, io as _io
                        with zipfile.ZipFile(_io.BytesIO(zip_bytes)) as zf:
                            names = zf.namelist()
                        print(Fore.WHITE + f"\nContents ({len(names)} files):")
                        for n in names[:20]:
                            print(Fore.YELLOW + f"  - {n}")
                        if len(names) > 20:
                            print(Fore.WHITE + f"  ... and {len(names) - 20} more")
                    else:
                        with open(path, "r", encoding="utf-8", errors="replace") as f:
                            first = f.readline().strip()
                        if first.startswith("#DPA-XOR"):
                            fmt = "v2 (Legacy XOR+Base64 text)"
                        elif first == DPA_HEADER_PLAIN:
                            fmt = "v1 (Legacy plain text)"
                        else:
                            fmt = "Legacy / Unknown"
                        print(Fore.WHITE + "Format:       " + Fore.GREEN + fmt)
                        print(Fore.WHITE + "File Size:    " + Fore.MAGENTA + f"{os.path.getsize(path):,} bytes")
                    separator()
                except Exception as e:
                    print_error(f"Failed to read dpa info: {e}")

        # ---- ZIP (folder → .zip) ----
        elif cmd.lower().startswith("zip "):
            parts = cmd[4:].strip().split()
            if not parts:
                print_error("Usage: zip <folder> [output.zip]")
            else:
                folder = parts[0]
                out = parts[1] if len(parts) > 1 else None
                if not os.path.isabs(folder) and current_path:
                    folder = os.path.join(current_path, folder)
                if not os.path.isdir(folder):
                    print_error("Folder not found")
                else:
                    if out is None:
                        out = folder.rstrip("\\/") + ".zip"
                    elif not os.path.isabs(out) and current_path:
                        out = os.path.join(current_path, out)
                    try:
                        import zipfile as _zf
                        with _zf.ZipFile(out, "w", _zf.ZIP_DEFLATED) as z:
                            for root, dirs, files in os.walk(folder):
                                for f in files:
                                    full = os.path.join(root, f)
                                    rel = os.path.relpath(full, folder)
                                    z.write(full, rel)
                        print_success(f"Zipped → {Fore.YELLOW}{out}")
                    except Exception as e:
                        print_error(f"Zip failed: {e}")

        # ---- UNZIP (.zip → folder) ----
        elif cmd.lower().startswith("unzip "):
            parts = cmd[6:].strip().split()
            if not parts:
                print_error("Usage: unzip <file.zip> [dest]")
            else:
                src = parts[0]
                dest = parts[1] if len(parts) > 1 else None
                if not os.path.isabs(src) and current_path:
                    src = os.path.join(current_path, src)
                if not os.path.exists(src):
                    print_error("Zip file not found")
                else:
                    if dest is None:
                        dest = os.path.splitext(src)[0] + "_extracted"
                    elif not os.path.isabs(dest) and current_path:
                        dest = os.path.join(current_path, dest)
                    try:
                        import zipfile as _zf
                        with _zf.ZipFile(src) as z:
                            z.extractall(dest)
                        print_success(f"Extracted → {Fore.YELLOW}{dest}")
                    except Exception as e:
                        print_error(f"Unzip failed: {e}")

        # ---- HASH ----
        elif cmd.lower().startswith("hash "):
            parts = cmd[5:].strip().split()
            if not parts:
                print_error("Usage: hash <file> [md5|sha1|sha256]")
            else:
                fname = parts[0]
                algo = parts[1].lower() if len(parts) > 1 else "sha256"
                path = fname if os.path.isabs(fname) else (os.path.join(current_path, fname) if current_path else fname)
                if not os.path.exists(path):
                    print_error("File not found")
                elif algo not in ("md5", "sha1", "sha256", "sha512"):
                    print_error("Supported algorithms: md5, sha1, sha256, sha512")
                else:
                    try:
                        import hashlib
                        h = hashlib.new(algo)
                        with open(path, "rb") as f:
                            for chunk in iter(lambda: f.read(8192), b""):
                                h.update(chunk)
                        print(Fore.CYAN + f"\n🔢 {algo.upper()} Hash of {os.path.basename(path)}:\n")
                        separator()
                        print(Fore.GREEN + h.hexdigest())
                        separator()
                    except Exception as e:
                        print_error(f"Hash failed: {e}")

        # ---- PING ----
        elif cmd.lower().startswith("ping "):
            host = cmd[5:].strip()
            if not host:
                print_error("Usage: ping <host>")
            else:
                print_output(f"Pinging {Fore.YELLOW}{host}{Fore.MAGENTA}...")
                try:
                    result = subprocess.run(["ping", "-n", "4", host], capture_output=True, text=True, encoding="cp1256")
                    print(Fore.WHITE + result.stdout)
                    if result.stderr:
                        print(Fore.RED + result.stderr)
                except Exception as e:
                    print_error(f"Ping failed: {e}")

        # ---- CMD (real Windows CMD passthrough) ----
        elif cmd.lower() == "cmd":
            print(Fore.CYAN + Style.BRIGHT + "\n⬛ WINDOWS CMD SESSION")
            print(Fore.WHITE + "Type real cmd.exe commands. Type 'exit' to return to DCMDS.\n")
            separator()
            while True:
                cmd_line = input(Fore.WHITE + "CMD> " + Fore.WHITE).strip()
                if cmd_line.lower() == "exit":
                    print_info("Returned to DCMDS")
                    break
                if not cmd_line:
                    continue
                try:
                    result = subprocess.run(
                        cmd_line, shell=True, cwd=(current_path or None),
                        capture_output=True, text=True, encoding="cp1256", errors="replace"
                    )
                    if result.stdout:
                        print(Fore.WHITE + result.stdout)
                    if result.stderr:
                        print(Fore.RED + result.stderr)
                except Exception as e:
                    print_error(f"Command failed: {e}")

        elif cmd.lower().startswith("cmd "):
            raw = cmd[4:].strip()
            if not raw:
                print_error("Usage: cmd <command>  (or just 'cmd' to enter a live session)")
            else:
                try:
                    result = subprocess.run(
                        raw, shell=True, cwd=(current_path or None),
                        capture_output=True, text=True, encoding="cp1256", errors="replace"
                    )
                    if result.stdout:
                        print(Fore.WHITE + result.stdout)
                    if result.stderr:
                        print(Fore.RED + result.stderr)
                    print_success("Command executed")
                except Exception as e:
                    print_error(f"Command failed: {e}")

        # ---- ALIAS ----
        elif cmd.lower() == "alias" or cmd.lower().startswith("alias "):
            rest = cmd[5:].strip()
            aliases = CONFIG.get("aliases", {})
            if not rest or rest.lower() == "list":
                if not aliases:
                    print_info("No aliases defined. Usage: alias <name> <command>")
                else:
                    print(Fore.CYAN + "\n🏷️  Aliases:\n")
                    for name, target in aliases.items():
                        print(Fore.WHITE + f"  {name:<15} → " + Fore.YELLOW + target)
            elif rest.lower().startswith("remove "):
                name = rest[7:].strip().lower()
                if name in aliases:
                    del aliases[name]
                    CONFIG["aliases"] = aliases
                    save_config(CONFIG)
                    print_success(f"Alias removed: {name}")
                else:
                    print_error("Alias not found")
            else:
                sub = rest.split(maxsplit=1)
                if len(sub) < 2:
                    print_error("Usage: alias <name> <command> | alias list | alias remove <name>")
                else:
                    name, target = sub[0].lower(), sub[1]
                    aliases[name] = target
                    CONFIG["aliases"] = aliases
                    save_config(CONFIG)
                    print_success(f"Alias registered: {name} → {target}")

        # ════════════════════════════════════════════════════════════════
        #  IMPLEMENTATION OF THE NEW DEMANDED COMMANDS
        # ════════════════════════════════════════════════════════════════
        
        # ---- CAMERA ----
        elif cmd.lower() == "camera":
            handle_camera()
            
        # ---- TAKE PHOTO ----
        elif cmd.lower() == "take":
            handle_camera_take()
            
        # ---- START VIDEO RECORDING ----
        elif cmd.lower() == "vid":
            handle_video_record()
            
        # ---- STOP VIDEO RECORDING ----
        elif cmd.lower() == "endvid":
            if video_recording:
                video_recording = False
                print_info("Stopping recording process...")
            else:
                print_error("No video is currently being recorded.")
                
        # ---- ADVANCED CALCULATOR ----
        elif cmd.lower() == "calc":
            handle_advanced_calculator()
            
        # ---- PYTHON INTERACTIVE (ACODE) ----
        elif cmd.lower() == "acode":
            handle_python_interactive()
            
        # ---- OPEN FILE IN VS CODE ----
        elif cmd.lower().startswith("code "):
            target = cmd[5:].strip()
            path = target if os.path.isabs(target) else (os.path.join(current_path, target) if current_path else target)
            if os.path.exists(path):
                try:
                    subprocess.Popen(["code", path], shell=True)
                    print_success(f"Opened {target} in VS Code.")
                except Exception as e:
                    print_error(f"Could not open VS Code: {e}. Is it added to system PATH?")
            else:
                print_error("File not found.")
                
        # ---- DIRECTORY TREE ----
        elif cmd.lower() == "tree":
            if current_path:
                print_info(f"Directory Tree for {current_path}:")
                handle_tree_view(current_path)
            else:
                print_error("No current path. Please choose a drive/path first.")
                
        # ---- LOCAL HTTP SERVER ----
        elif cmd.lower().startswith("server"):
            parts = cmd.split()
            port = 8000
            if len(parts) >= 3 and parts[1].lower() == "port" and parts[2].isdigit():
                port = int(parts[2])
            handle_local_web_server(port)
            
        # ---- CREATE FILE ----
        elif cmd.lower().startswith("create "):
            target = cmd[7:].strip()
            path = target if os.path.isabs(target) else (os.path.join(current_path, target) if current_path else target)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
                print_success(f"File created successfully: {target}")
            except Exception as e:
                print_error(f"Failed to create file: {e}")
                
        # ---- DELETE FILE ----
        elif cmd.lower().startswith("delete "):
            if safe_mode_blocked("delete"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            target = cmd[7:].strip()
            path = target if os.path.isabs(target) else (os.path.join(current_path, target) if current_path else target)
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                    print_success(f"Removed: {target}")
                except Exception as e:
                    print_error(f"Failed to delete: {e}")
            else:
                print_error("Target path not found.")
                
        # ---- OPEN FILE (DEFAULT APP) ----
        elif cmd.lower().startswith("open "):
            target = cmd[5:].strip()
            path = target if os.path.isabs(target) else (os.path.join(current_path, target) if current_path else target)
            if os.path.exists(path):
                try:
                    os.startfile(path)
                    print_success(f"Opened {target} with default program.")
                except Exception as e:
                    print_error(f"Failed to open file: {e}")
            else:
                print_error("File not found.")

        # ---- ENCRYPT ----
        elif cmd.lower().startswith("encrypt "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 2:
                print_error("Usage: encrypt <file.py> [key]")
            else:
                src = parts[1]
                key = parts[2] if len(parts) > 2 else None
                if not os.path.isabs(src) and current_path:
                    src = os.path.join(current_path, src)
                if not os.path.exists(src):
                    print_error("Source file not found")
                else:
                    try:
                        out_path = encrypt_to_dpa(src, None, key)
                        print_success(f"Encrypted legacy DPA script → {Fore.YELLOW}{out_path}")
                    except Exception as e:
                        print_error(f"Encryption failed: {e}")

        # ---- DECRYPT ----
        elif cmd.lower().startswith("decrypt "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 2:
                print_error("Usage: decrypt <file.dpa> [key]")
            else:
                src = parts[1]
                key = parts[2] if len(parts) > 2 else None
                if not os.path.isabs(src) and current_path:
                    src = os.path.join(current_path, src)
                if not os.path.exists(src):
                    print_error("Source file not found")
                else:
                    try:
                        source = decrypt_dpa(src, key)
                        print(Fore.CYAN + f"\n🔓 Decrypted text-source of {os.path.basename(src)}:\n")
                        separator()
                        print(Fore.YELLOW + source)
                        separator()
                    except Exception as e:
                        print_error(f"Decryption failed: {e}")

        # ---- RUN ----
        elif cmd.lower().startswith("run "):
            target = cmd[4:].strip()
            path = target if os.path.isabs(target) else (os.path.join(current_path, target) if current_path else target)
            if os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                if ext == ".html":
                    try:
                        subprocess.Popen(["start", "chrome", path], shell=True)
                        print_success("Opened HTML file in browser.")
                    except:
                        os.startfile(path)
                elif ext == ".py":
                    subprocess.run([sys.executable, path])
                else:
                    os.startfile(path)
            else:
                print_error("File not found.")

        # ---- CLEANUP ----
        elif cmd.lower() == "cleanup":
            if safe_mode_blocked("cleanup"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
            else:
                system_cleanup()

        # ---- INFO ----
        elif cmd.lower().startswith("info "):
            show_file_info(cmd[5:].strip())

        # ---- NOTE ----
        elif cmd.lower() == "note":
            quick_note()

        # ---- WIFI / IP ----
        elif cmd.lower() == "wifi":
            show_wifi_networks()
        elif cmd.lower().startswith("wifipass "):
            show_wifi_password(cmd[9:].strip())
        elif cmd.lower() == "ip":
            show_ip_info()

        # ---- COPY / MOVE / RENAME ----
        elif cmd.lower().startswith("copy "):
            parts = cmd[5:].strip().split(maxsplit=1)
            if len(parts) == 2:
                copy_file(parts[0], parts[1])
            else:
                print_error("Usage: copy <src> <dst>")
        elif cmd.lower().startswith("move "):
            parts = cmd[5:].strip().split(maxsplit=1)
            if len(parts) == 2:
                move_file(parts[0], parts[1])
            else:
                print_error("Usage: move <src> <dst>")
        elif cmd.lower().startswith("rename "):
            parts = cmd[7:].strip().split(maxsplit=1)
            if len(parts) == 2:
                rename_file(parts[0], parts[1])
            else:
                print_error("Usage: rename <old> <new>")

        # ---- SEARCH ----
        elif cmd.lower().startswith("search "):
            search_files(cmd[7:].strip())

        # ---- SYSTEM POWER COMMANDS ----
        elif cmd.lower() == "shutdown":
            if safe_mode_blocked("shutdown"):
                print_error("Safe mode is ON. Toggle off to shutdown system.")
            else:
                print_info("Shutting down machine...")
                os.system("shutdown /s /t 1")
        elif cmd.lower() == "restartsys":
            if safe_mode_blocked("restart"):
                print_error("Safe mode is ON. Toggle off to restart system.")
            else:
                print_info("Restarting machine...")
                os.system("shutdown /r /t 1")
        elif cmd.lower() == "sleep":
            if safe_mode_blocked("sleep"):
                print_error("Safe mode is ON. Toggle off to trigger sleep.")
            else:
                print_info("System putting to sleep...")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

        else:
            print_error(f"Unknown command: '{cmd.split()[0]}'. Type 'help' for support.")
            separator()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + Fore.RED + "System forcefully interrupted. Goodbye!")