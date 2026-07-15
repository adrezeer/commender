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

COMMANDS = {}
COMMAND_HELP = {}
CONFIG = {}
THEMES = {}
ACTIVE_THEME = {}
HISTORY = []
LOADED_PLUGINS = []

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
    # Normalize special help topics
    if key in ["c", "d", "e"]:
        key = "c"
    if key == "restart":
        # Could be task restart or system restart
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
║                 {Fore.RED}Alpha {Fore.GREEN}Version 0.0.3{Fore.CYAN}                           ║
║              {Fore.CYAN}Build: {Fore.YELLOW}February 3, 2026{Fore.CYAN}                          ║
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
        
        # Display folders first
        for folder in sorted(folders):
            print(Fore.CYAN + Style.BRIGHT + "📁 [DIR]  " + Fore.YELLOW + folder)
        
        # Display files
        for file in sorted(files):
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.py', '.js', '.java', '.cpp', '.c']:
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
        
        # Collect all items with icons
        for item in sorted(items):
            full = os.path.join(current_path, item)
            if os.path.isdir(full):
                all_items.append(("📁 [DIR]  " + item, item, "folder"))
            else:
                ext = os.path.splitext(item)[1].lower()
                if ext in ['.py', '.js', '.java', '.cpp', '.c']:
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
            # Clear and redraw
            os.system('cls' if os.name == 'nt' else 'clear')
            print_logo()
            print(Fore.CYAN + Style.BRIGHT + f"\n📂 Browsing: {current_path}")
            print(Fore.WHITE + "Use ↑↓ arrows, Enter to select, ESC to cancel\n")
            separator()
            
            # Display items with selection
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
            
            # Get key input - blocking wait (no infinite loop!)
            key = msvcrt.getch()
            
            # Arrow keys return two bytes
            if key == b'\xe0':  # Arrow key prefix
                key = msvcrt.getch()
                if key == b'H':  # Up arrow
                    selected = (selected - 1) % len(all_items)
                elif key == b'P':  # Down arrow
                    selected = (selected + 1) % len(all_items)
            
            # Enter key
            elif key == b'\r':
                return all_items[selected][1]
            
            # ESC key
            elif key == b'\x1b':
                print_info("\nBrowse cancelled")
                return None
            
            # 'c' or 'C' key for copy
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
        
        # Sort by memory usage
        processes = sorted(processes, key=lambda x: x['memory_percent'] if x['memory_percent'] else 0, reverse=True)
        
        # Display header
        print(f"{Fore.YELLOW}{'PID':<8} {'Name':<30} {'CPU %':<8} {'RAM %':<8} {'Status':<12}")
        separator()
        
        # Display top 30 processes
        for proc in processes[:30]:
            pid = proc['pid']
            name = proc['name'][:28] if len(proc['name']) > 28 else proc['name']
            cpu = f"{proc['cpu_percent']:.1f}%" if proc['cpu_percent'] else "0.0%"
            ram = f"{proc['memory_percent']:.1f}%" if proc['memory_percent'] else "0.0%"
            status = proc['status'][:10] if proc['status'] else "unknown"
            
            # Color based on resource usage
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

def browse_tasks():
    """Interactive task browser with options to end or restart tasks"""
    try:
        selected = 0
        
        while True:
            # Get fresh process list
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory usage
            processes = sorted(processes, key=lambda x: x['memory_percent'] if x['memory_percent'] else 0, reverse=True)
            
            if not processes:
                print_error("No processes found")
                return
            
            # Make sure selected is within bounds
            if selected >= len(processes):
                selected = len(processes) - 1
            
            # Clear and redraw
            os.system('cls' if os.name == 'nt' else 'clear')
            print_logo()
            print(Fore.CYAN + Style.BRIGHT + "\n⚙️  TASK MANAGER - INTERACTIVE MODE")
            print(Fore.WHITE + "Use ↑↓ arrows | " + Fore.RED + "E" + Fore.WHITE + " to End Task | " + Fore.GREEN + "R" + Fore.WHITE + " to Restart | ESC to exit\n")
            separator()
            
            # Display header
            print(f"{Fore.YELLOW}{'PID':<8} {'Name':<35} {'CPU %':<8} {'RAM %':<8}")
            separator()
            
            # Display window (show 20 processes at a time)
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
                    # Color based on resource usage
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
            
            # Get key input
            key = msvcrt.getch()
            
            # Arrow keys
            if key == b'\xe0':
                key = msvcrt.getch()
                if key == b'H':  # Up arrow
                    selected = max(0, selected - 1)
                elif key == b'P':  # Down arrow
                    selected = min(len(processes) - 1, selected + 1)
            
            # ESC key
            elif key == b'\x1b':
                print_info("\nExited task browser")
                return
            
            # 'E' key - End task
            elif key.lower() == b'e':
                proc_to_end = processes[selected]
                print(Fore.RED + f"\n⚠️  End task: {proc_to_end['name']} (PID: {proc_to_end['pid']})?")
                confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
                
                if confirm == 'yes':
                    try:
                        process = psutil.Process(proc_to_end['pid'])
                        process.terminate()  # Try graceful termination first
                        time.sleep(0.5)
                        
                        # Check if still running
                        if process.is_running():
                            process.kill()  # Force kill
                        
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
            
            # 'R' key - Restart task
            elif key.lower() == b'r':
                proc_to_restart = processes[selected]
                print(Fore.YELLOW + f"\n🔄 Restart task: {proc_to_restart['name']} (PID: {proc_to_restart['pid']})?")
                confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
                
                if confirm == 'yes':
                    try:
                        # Get process executable path
                        process = psutil.Process(proc_to_restart['pid'])
                        exe_path = process.exe()
                        
                        # Terminate the process
                        process.terminate()
                        time.sleep(0.5)
                        
                        if process.is_running():
                            process.kill()
                        
                        # Wait a bit
                        time.sleep(1)
                        
                        # Restart the process
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
    """Display available WiFi networks"""
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
    """Show password for a saved WiFi network"""
    try:
        print(Fore.CYAN + f"\n🔑 Retrieving password for: {Fore.YELLOW}{network_name}\n")
        separator()
        result = subprocess.run(['netsh', 'wlan', 'show', 'profile', network_name, 'key=clear'], 
                              capture_output=True, text=True, encoding='cp1256')
        if result.returncode == 0:
            output = result.stdout
            # Extract password
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
    """Show detailed IP and network information"""
    try:
        print(Fore.CYAN + Style.BRIGHT + "\n🌐 NETWORK INFORMATION\n")
        separator()
        
        # Get all network interfaces
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
    """Copy file from source to destination"""
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
    """Move file from source to destination"""
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
    """Rename a file"""
    try:
        if os.path.exists(old_name):
            os.rename(old_name, new_name)
            print_success(f"File renamed: {Fore.YELLOW}{old_name} {Fore.WHITE}→ {Fore.CYAN}{new_name}")
        else:
            print_error("File not found")
    except Exception as e:
        print_error(f"Failed to rename file: {e}")

def search_files(pattern):
    """Search for files matching pattern in current directory"""
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
            for i, file in enumerate(found_files[:50], 1):  # Limit to 50 results
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
    """Show detailed information about a file"""
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
        
        # Creation time
        creation_time = datetime.datetime.fromtimestamp(stat_info.st_ctime)
        print(Fore.WHITE + "Created:      " + Fore.YELLOW + creation_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Modified time
        modified_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
        print(Fore.WHITE + "Modified:     " + Fore.YELLOW + modified_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Extension
        if not os.path.isdir(filepath):
            ext = os.path.splitext(filename)[1]
            print(Fore.WHITE + "Extension:    " + Fore.CYAN + (ext if ext else "No extension"))
        
        separator()
    except Exception as e:
        print_error(f"Error getting file info: {e}")

def quick_note():
    """Quick note taking system"""
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
    """Clean temporary files and show disk space saved"""
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
        
        # Clean Windows Temp
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
                        pass  # Skip files that can't be deleted
        
        separator()
        print(Fore.GREEN + f"✓ Cleanup complete!")
        print(Fore.WHITE + f"  Files deleted: " + Fore.YELLOW + f"{deleted_count}")
        print(Fore.WHITE + f"  Space freed:   " + Fore.GREEN + f"{deleted_size / (1024**2):.2f} MB")
        separator()
        
    except Exception as e:
        print_error(f"Cleanup error: {e}")


def main():
    global CONFIG, THEMES, current_path
    CONFIG = load_config()
    THEMES = load_themes()
    apply_theme()
    init_base_help()
    load_history()
    load_plugins()

    # System Startup Animation
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
        # Custom prompt with current path
        bracket_color = _color_from_name(ACTIVE_THEME.get("prompt_bracket", "YELLOW"), Fore.YELLOW)
        path_color = _color_from_name(ACTIVE_THEME.get("prompt_path", "GREEN"), Fore.GREEN)
        label_color = _color_from_name(ACTIVE_THEME.get("prompt_label", "CYAN"), Fore.CYAN)
        if current_path:
            prompt = f"{bracket_color}[{path_color}{current_path}{bracket_color}]{Fore.WHITE} DCMDS{label_color}>{Fore.WHITE} "
        else:
            prompt = f"{Fore.WHITE}DCMDS{label_color}>{Fore.WHITE} "
    
        cmd = input(prompt).strip()
        if not cmd:
            continue
    
        append_history(cmd)
    
        separator()
    
        # ---- EXIT ----
        if cmd.lower() == "exit" or cmd.lower() == "bsx":
            print(Fore.YELLOW + "Shutting down DCMDS...")
            animated_separator()
            print_success("Goodbye! 👋")
            break
    
                # ---- HELP ----
        elif cmd.lower().startswith("help"):
            parts = cmd.split(maxsplit=1)
            topic = parts[1] if len(parts) > 1 else None
            show_help(topic)

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

        # ---- TASKS ----
        elif cmd.lower() == "tasks":
            show_tasks()
    
        # ---- TASKS BROWSE ----
        elif cmd.lower() == "tasks browse":
            browse_tasks()
    
        # ---- TASK BROWSER SHORTCUTS ----
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
                    # Check if process exists
                    process = psutil.Process(pid)
                    proc_name = process.name()
    
                    print(Fore.RED + f"⚠️  End task: {proc_name} (PID: {pid})?")
                    confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
    
                    if confirm == 'yes':
                        try:
                            process.terminate()  # Try graceful termination
                            time.sleep(0.5)
    
                            # Check if still running
                            if process.is_running():
                                process.kill()  # Force kill
    
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
                    # Check if process exists
                    process = psutil.Process(pid)
                    proc_name = process.name()
                    exe_path = process.exe()
    
                    print(Fore.YELLOW + f"🔄 Restart task: {proc_name} (PID: {pid})?")
                    confirm = input(Fore.YELLOW + "Type 'yes' to confirm: " + Fore.WHITE).strip().lower()
    
                    if confirm == 'yes':
                        try:
                            # Terminate the process
                            process.terminate()
                            time.sleep(0.5)
    
                            if process.is_running():
                                process.kill()
    
                            # Wait a bit
                            time.sleep(1)
    
                            # Restart the process
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
            print(Fore.WHITE + "Version:         " + Fore.GREEN + "0.0.2")
            print(Fore.WHITE + "Stage:           " + Fore.RED + "Alpha (Under Development)")
            print(Fore.WHITE + "Build:           " + Fore.CYAN + "January 29, 2026")
            print(Fore.WHITE + "Creator:         " + Fore.MAGENTA + "Danrode")
            separator()
            print(Fore.YELLOW + "\n📝 Version Format: Alpha.Beta.Version")
            print(Fore.WHITE + "• " + Fore.RED + "0" + Fore.WHITE + ".x.x = Alpha (Under Development)")
            print(Fore.WHITE + "• x." + Fore.YELLOW + "0" + Fore.WHITE + ".x = Beta Testing")
            print(Fore.WHITE + "• x.x." + Fore.GREEN + "1" + Fore.WHITE + " = Version Number (Official Release)")
    
        # ---- DEBUG ----
        elif cmd.lower() == "debug":
            print(Fore.RED + Style.BRIGHT + "\n🔧 DCMDS SYSTEM DIAGNOSTICS\n")
            separator()
    
            # DCMDS Info
            print(Fore.CYAN + Style.BRIGHT + "📦 DCMDS INFORMATION:")
            print(Fore.WHITE + "  System Name:    " + Fore.YELLOW + "DCMDS (Danrode CMD System)")
            print(Fore.WHITE + "  Version:        " + Fore.GREEN + "0.0.2 (Alpha)")
            print(Fore.WHITE + "  Build Date:     " + Fore.CYAN + "January 29, 2026")
            print(Fore.WHITE + "  Current Path:   " + Fore.YELLOW + (current_path if current_path else "None"))
    
            separator()
    
            # Python Info
            print(Fore.CYAN + Style.BRIGHT + "🐍 PYTHON INFORMATION:")
            print(Fore.WHITE + "  Python Version: " + Fore.GREEN + sys.version.split()[0])
            print(Fore.WHITE + "  Full Version:   " + Fore.YELLOW + sys.version.replace('\n', ' '))
            print(Fore.WHITE + "  Executable:     " + Fore.CYAN + sys.executable)
            print(Fore.WHITE + "  Platform:       " + Fore.MAGENTA + sys.platform)
    
            separator()
    
            # Windows Info
            print(Fore.CYAN + Style.BRIGHT + "🪟 WINDOWS INFORMATION:")
            print(Fore.WHITE + "  OS:             " + Fore.YELLOW + platform.system() + " " + platform.release())
            print(Fore.WHITE + "  Version:        " + Fore.GREEN + platform.version())
            print(Fore.WHITE + "  Edition:        " + Fore.CYAN + platform.win32_edition())
            print(Fore.WHITE + "  Architecture:   " + Fore.MAGENTA + platform.machine())
            print(Fore.WHITE + "  Computer Name:  " + Fore.YELLOW + platform.node())
    
            separator()
    
            # Processor Info
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
    
            # Memory Info
            print(Fore.CYAN + Style.BRIGHT + "🧠 MEMORY INFORMATION:")
            memory = psutil.virtual_memory()
            print(Fore.WHITE + "  Total RAM:      " + Fore.GREEN + f"{memory.total / (1024**3):.2f} GB")
            print(Fore.WHITE + "  Available:      " + Fore.YELLOW + f"{memory.available / (1024**3):.2f} GB")
            print(Fore.WHITE + "  Used:           " + Fore.RED + f"{memory.used / (1024**3):.2f} GB ({memory.percent}%)")
            print(Fore.WHITE + "  Free:           " + Fore.CYAN + f"{memory.free / (1024**3):.2f} GB")
    
            separator()
    
            # Disk Info
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
    
            # Network Info
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
    
            # Loaded Modules
            print(Fore.CYAN + Style.BRIGHT + "📚 LOADED MODULES:")
            modules = ['colorama', 'cv2', 'psutil', 'datetime', 'subprocess']
            for module in modules:
                if module in sys.modules:
                    print(Fore.WHITE + f"  ✓ {module:<15} " + Fore.GREEN + "Loaded")
                else:
                    print(Fore.WHITE + f"  ✗ {module:<15} " + Fore.RED + "Not Loaded")
    
            separator()
    
            # Access Options
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
                            f.write(f"DCMDS Version: 0.0.2 (Alpha)\n")
                            f.write(f"Build Date: January 29, 2026\n")
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
                    for key, value in sorted(os.environ.items())[:10]:  # Show first 10
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
                    # Clear and redraw
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print_logo()
                    print(Fore.CYAN + Style.BRIGHT + "\n💾 AVAILABLE DRIVES")
                    print(Fore.WHITE + "Use ↑↓ arrows, Enter to select, ESC to cancel\n")
                    separator()
    
                    # Display drives with selection
                    for i, drive in enumerate(drives):
                        if i == selected:
                            print(Back.GREEN + Fore.BLACK + "► " + drive + " " * 20)
                        else:
                            print(Fore.YELLOW + "  " + drive)
    
                    separator()
                    print(Fore.GREEN + f"\nSelected: " + Fore.YELLOW + drives[selected])
                    print(Fore.CYAN + "\n↑↓ Navigate | Enter Select | ESC Cancel")
    
                    # Get key input - blocking wait
                    key = msvcrt.getch()
    
                    # Arrow keys
                    if key == b'\xe0':
                        key = msvcrt.getch()
                        if key == b'H':  # Up arrow
                            selected = (selected - 1) % len(drives)
                        elif key == b'P':  # Down arrow
                            selected = (selected + 1) % len(drives)
    
                    # Enter key
                    elif key == b'\r':
                        current_path = drives[selected]
                        print_success(f"\nCurrent path set to: {Fore.YELLOW}{current_path}")
                        browsing = False
    
                    # ESC key
                    elif key == b'\x1b':
                        print_info("\nSelection cancelled")
                        browsing = False
    
                    # C key
                    elif key.lower() == b'c':
                        current_path = drives[selected]
                        print_success(f"\nCurrent path set to: {Fore.YELLOW}{current_path}")
                        browsing = False
    
        # ---- Drive Shortcut (C / D / E) ----
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
                # Check if at drive root (e.g., C:\)
                if len(current_path) <= 3:  # At root like "C:\"
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
    
        # ---- OPEN ----
        elif cmd.lower().startswith("open "):
            if not current_path:
                print_error("No path selected")
            else:
                name = cmd[5:].strip()
                path = os.path.join(current_path, name)
                if os.path.exists(path):
                    print_success(f"Opening file: {Fore.YELLOW}{path}")
                    os.startfile(path)
                else:
                    print_error("File not found")
    
        # ---- CREATE ----
        elif cmd.lower().startswith("create "):
            if not current_path:
                print_error("No path selected")
            else:
                name = cmd[7:].strip()
                path = os.path.join(current_path, name)
                if not os.path.exists(path):
                    open(path, "w").close()
                    print_success(f"File created: {Fore.YELLOW}{path}")
                else:
                    print_error("File already exists")
    
        # ---- DELETE ----
        elif cmd.lower().startswith("delete "):
            if safe_mode_blocked("delete"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            if not current_path:
                print_error("No path selected")
            else:
                name = cmd[7:].strip()
                path = os.path.join(current_path, name)
                if os.path.isfile(path):
                    confirm = input(Fore.RED + f"⚠ Delete {name}? (y/n): ")
                    if confirm.lower() == 'y':
                        os.remove(path)
                        print_success(f"File deleted: {Fore.YELLOW}{path}")
                    else:
                        print_info("Deletion cancelled")
                else:
                    print_error("File not found")
    
        # ---- RUN ----
        elif cmd.lower().startswith("run "):
            if not current_path:
                print_error("No path selected")
            else:
                name = cmd[4:].strip()
                path = os.path.join(current_path, name)
                if not os.path.exists(path):
                    print_error("File not found")
                else:
                    ext = os.path.splitext(path)[1].lower()
                    if ext == ".html":
                        print_output(f"Opening {Fore.YELLOW}{path}{Fore.MAGENTA} in Google Chrome...")
                        chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                        if os.path.exists(chrome_path):
                            subprocess.run([chrome_path, path])
                            print_success("Launched successfully!")
                        else:
                            print_error("Chrome not found! Edit path if needed.")
                    elif ext in [".py", ".js", ".java", ".cpp", ".c", ".cs"]:
                        print_output(f"Opening {Fore.YELLOW}{path}{Fore.MAGENTA} in VS Code...")
                        os.system(f'code "{path}"')
                        print_success("Launched successfully!")
                    else:
                        print_error("Cannot run this file type")
    
        # ---- CODE ----
        elif cmd.lower().startswith("code "):
            if not current_path:
                print_error("No path selected")
            else:
                name = cmd[5:].strip()
                path = os.path.join(current_path, name)
                if os.path.exists(path):
                    print_output(f"Opening {Fore.YELLOW}{path}{Fore.MAGENTA} in VS Code...")
                    os.system(f'code "{path}"')
                    print_success("Launched successfully!")
                else:
                    print_error("File not found")
    
        # ---- ACODE ----
        elif cmd.lower() == "acode":
            if not current_path:
                print_error("No path selected")
            else:
                print(Fore.CYAN + Style.BRIGHT + "\n🐍 Python Interactive Mode")
                print(Fore.WHITE + "Type 'xcode' to exit\n")
                separator()
                while True:
                    py_line = input(Fore.GREEN + "PY>> " + Fore.WHITE).strip()
                    if py_line.lower() == "xcode":
                        print_success("Exited acode mode")
                        break
                    try:
                        result = eval(py_line)
                        if result is not None:
                            print(Fore.MAGENTA + "➤ " + str(result))
                    except SyntaxError:
                        try:
                            exec(py_line)
                        except Exception as e:
                            print_error(f"Error: {e}")
                    except Exception as e:
                        print_error(f"Error: {e}")
    
        # ---- CALCULATOR ----
        elif cmd.lower() == "calc":
            print(Fore.CYAN + Style.BRIGHT + "\n🧮 DCMDS ADVANCED CALCULATOR")
            print(Fore.WHITE + "Type 'exit' to quit calculator\n")
            separator()
            print(Fore.YELLOW + "Supported operations:")
            print(Fore.WHITE + "• Basic: " + Fore.GREEN + "+ - * / % **")
            print(Fore.WHITE + "• Functions: " + Fore.GREEN + "sqrt(), sin(), cos(), tan(), log(), abs()")
            print(Fore.WHITE + "• Constants: " + Fore.GREEN + "pi, e")
            print(Fore.WHITE + "• Examples: " + Fore.CYAN + "2+2, sqrt(16), sin(pi/2), 2**8")
            separator()
    
            calc_history = []
    
            while True:
                calc_input = input(Fore.GREEN + "CALC>> " + Fore.WHITE).strip()
    
                if calc_input.lower() == "exit":
                    print_success("Exited calculator")
                    break
    
                if calc_input.lower() == "history":
                    if calc_history:
                        print(Fore.CYAN + "\n📝 Calculation History:")
                        for i, (expr, res) in enumerate(calc_history, 1):
                            print(Fore.WHITE + f"{i}. " + Fore.YELLOW + f"{expr}" + Fore.WHITE + " = " + Fore.GREEN + f"{res}")
                    else:
                        print_info("No history yet")
                    continue
    
                if calc_input.lower() == "clear":
                    calc_history.clear()
                    print_success("History cleared")
                    continue
    
                if not calc_input:
                    continue
    
                try:
                    # Replace common math functions
                    calc_input_eval = calc_input.replace("^", "**")
    
                    # Safe evaluation with math functions
                    safe_dict = {
                        "sqrt": math.sqrt,
                        "sin": math.sin,
                        "cos": math.cos,
                        "tan": math.tan,
                        "log": math.log,
                        "log10": math.log10,
                        "abs": abs,
                        "pi": math.pi,
                        "e": math.e,
                        "pow": pow,
                        "round": round,
                        "floor": math.floor,
                        "ceil": math.ceil,
                    }
    
                    result = eval(calc_input_eval, {"__builtins__": {}}, safe_dict)
                    print(Fore.MAGENTA + Style.BRIGHT + "➤ " + Fore.GREEN + str(result))
                    calc_history.append((calc_input, result))
    
                except Exception as e:
                    print_error(f"Error: {e}")
    
        # ---- SERVER ----
        elif cmd.lower().startswith("server port "):
            port_str = cmd[12:].strip()
            if not port_str.isdigit():
                print_error("Invalid port number")
            else:
                port = int(port_str)
                if not current_path:
                    print_error("No path selected. Choose a folder first.")
                else:
                    print_output(f"Starting HTTP server at {Fore.YELLOW}http://localhost:{port}/{Fore.MAGENTA}")
                    print_output(f"Serving: {Fore.YELLOW}{current_path}")
                    print(Fore.RED + "\n⚠ Press Ctrl+C to stop the server\n")
                    try:
                        import http.server
                        import socketserver
    
                        os.chdir(current_path)
                        handler = http.server.SimpleHTTPRequestHandler
                        with socketserver.TCPServer(("", port), handler) as httpd:
                            print_success(f"Server running on port {port}")
                            httpd.serve_forever()
                    except KeyboardInterrupt:
                        print_output("\nServer stopped")
                    except OSError as e:
                        print_error(f"Failed to start server: {e}")
    
        # ---- CAMERA ----
        elif cmd.lower() == "camera":
            if camera_active:
                print_error("Camera already active!")
            else:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    print_error("Cannot open camera")
                else:
                    camera_active = True
                    print_success("Camera active. Press 'q' to close preview")
                    while camera_active and not video_recording:
                        ret, frame = cap.read()
                        if not ret:
                            print_error("Failed to grab frame")
                            break
                        cv2.imshow("DCMDS Camera", frame)
                        key = cv2.waitKey(1)
                        if key == ord('q'):
                            camera_active = False
                            break
                    cap.release()
                    cv2.destroyAllWindows()
                    print_success("Camera closed")
    
        # ---- TAKE PHOTO ----
        elif cmd.lower() == "take":
            if camera_active and cap is not None:
                ret, frame = cap.read()
                if ret:
                    filename = f"photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    cv2.imwrite(filename, frame)
                    print_success(f"Photo saved: {Fore.YELLOW}{filename}")
                else:
                    print_error("Failed to capture photo")
            else:
                print_error("Camera not active. Use 'camera' command first")
    
        # ---- START VIDEO ----
        elif cmd.lower() == "vid":
            if camera_active and cap is not None:
                if video_recording:
                    print_error("Video already recording!")
                else:
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    filename = f"video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
                    frame_width = int(cap.get(3))
                    frame_height = int(cap.get(4))
                    video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (frame_width, frame_height))
                    video_recording = True
                    print_success(f"Recording video... Use 'endvid' to stop")
                    print_info(f"Output: {Fore.YELLOW}{filename}")
            else:
                print_error("Camera not active. Use 'camera' command first")
    
        # ---- END VIDEO ----
        elif cmd.lower() == "endvid":
            if video_recording:
                video_recording = False
                if video_writer is not None:
                    video_writer.release()
                cv2.destroyAllWindows()
                print_success("Video recording stopped and saved")
            else:
                print_error("No video is being recorded")
    
        # ---- SHUTDOWN ----
        elif cmd.lower() == "shutdown":
            if safe_mode_blocked("shutdown"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            print(Fore.RED + Style.BRIGHT + "⚠️  WARNING: This will shutdown your computer!")
            confirm = input(Fore.YELLOW + "Are you sure? (yes/no): ").strip().lower()
            if confirm in ["yes", "y"]:
                print_output("Shutting down computer in 10 seconds...")
                print(Fore.RED + "Press Ctrl+C to cancel")
                try:
                    time.sleep(2)
                    os.system("shutdown /s /t 10")
                    print_success("Shutdown initiated!")
                except KeyboardInterrupt:
                    print_info("Shutdown cancelled")
            else:
                print_info("Shutdown cancelled")
    
        # ---- SLEEP ----
        elif cmd.lower() == "sleep":
            if safe_mode_blocked("sleep"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            print(Fore.YELLOW + Style.BRIGHT + "💤 Putting computer to sleep...")
            confirm = input(Fore.YELLOW + "Continue? (yes/no): ").strip().lower()
            if confirm in ["yes", "y"]:
                print_success("Going to sleep mode...")
                time.sleep(1)
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            else:
                print_info("Sleep cancelled")
    
        # ---- RESTART ----
        elif cmd.lower() == "restart":
            if safe_mode_blocked("restart"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
                separator()
                continue
            print(Fore.RED + Style.BRIGHT + "⚠️  WARNING: This will restart your computer!")
            confirm = input(Fore.YELLOW + "Are you sure? (yes/no): ").strip().lower()
            if confirm in ["yes", "y"]:
                print_output("Restarting computer in 10 seconds...")
                print(Fore.RED + "Press Ctrl+C to cancel")
                try:
                    time.sleep(2)
                    os.system("shutdown /r /t 10")
                    print_success("Restart initiated!")
                except KeyboardInterrupt:
                    print_info("Restart cancelled")
            else:
                print_info("Restart cancelled")
    
        # ---- WIFI SCAN ----
        elif cmd.lower() == "wifi":
            show_wifi_networks()
    
        # ---- WIFI PASSWORD ----
        elif cmd.lower().startswith("wifipass "):
            network_name = cmd[9:].strip()
            if network_name:
                show_wifi_password(network_name)
            else:
                print_error("Please specify network name: wifipass <network_name>")
    
        # ---- IP INFO ----
        elif cmd.lower() == "ip":
            show_ip_info()
    
        # ---- COPY FILE ----
        elif cmd.lower().startswith("copy "):
            parts = cmd[5:].strip().split()
            if len(parts) >= 2:
                source = parts[0]
                destination = ' '.join(parts[1:])
    
                # Handle relative paths
                if not os.path.isabs(source) and current_path:
                    source = os.path.join(current_path, source)
                if not os.path.isabs(destination) and current_path:
                    destination = os.path.join(current_path, destination)
    
                copy_file(source, destination)
            else:
                print_error("Usage: copy <source> <destination>")
    
        # ---- MOVE FILE ----
        elif cmd.lower().startswith("move "):
            parts = cmd[5:].strip().split()
            if len(parts) >= 2:
                source = parts[0]
                destination = ' '.join(parts[1:])
    
                # Handle relative paths
                if not os.path.isabs(source) and current_path:
                    source = os.path.join(current_path, source)
                if not os.path.isabs(destination) and current_path:
                    destination = os.path.join(current_path, destination)
    
                move_file(source, destination)
            else:
                print_error("Usage: move <source> <destination>")
    
        # ---- RENAME FILE ----
        elif cmd.lower().startswith("rename "):
            parts = cmd[7:].strip().split()
            if len(parts) >= 2:
                old_name = parts[0]
                new_name = ' '.join(parts[1:])
    
                # Handle relative paths
                if not os.path.isabs(old_name) and current_path:
                    old_name = os.path.join(current_path, old_name)
                if not os.path.isabs(new_name) and current_path:
                    new_name = os.path.join(current_path, new_name)
    
                rename_file(old_name, new_name)
            else:
                print_error("Usage: rename <old_name> <new_name>")
    
        # ---- SEARCH FILES ----
        elif cmd.lower().startswith("search "):
            pattern = cmd[7:].strip()
            if pattern:
                search_files(pattern)
            else:
                print_error("Usage: search <pattern> (e.g., search *.txt)")
    
        # ---- FILE INFO ----
        elif cmd.lower().startswith("info "):
            filename = cmd[5:].strip()
            if filename:
                show_file_info(filename)
            else:
                print_error("Usage: info <filename>")
    
        # ---- QUICK NOTE ----
        elif cmd.lower() == "note":
            quick_note()
    
        # ---- CLEANUP ----
        elif cmd.lower() == "cleanup":
            if safe_mode_blocked("cleanup"):
                print_error("Safe mode is ON. Use 'safe off' to enable this command.")
            else:
                system_cleanup()
    
        # ---- TREE ----
        elif cmd.lower() == "tree":
            if not current_path:
                print_error("No path selected")
            else:
                print(Fore.CYAN + Style.BRIGHT + f"\n🌳 DIRECTORY TREE: {current_path}\n")
                separator()
                try:
                    for root, dirs, files in os.walk(current_path):
                        level = root.replace(current_path, '').count(os.sep)
                        indent = '  ' * level
                        folder_name = os.path.basename(root)
                        if level == 0:
                            print(Fore.CYAN + f"{current_path}")
                        else:
                            print(Fore.CYAN + f'{indent}📁 {folder_name}')
    
                        sub_indent = '  ' * (level + 1)
                        for file in files[:5]:  # Limit files per folder
                            print(Fore.YELLOW + f'{sub_indent}📄 {file}')
    
                        if len(files) > 5:
                            print(Fore.WHITE + f'{sub_indent}... and {len(files) - 5} more files')
    
                        # Limit depth
                        if level >= 2:
                            dirs[:] = []  # Don't go deeper
    
                    separator()
                except Exception as e:
                    print_error(f"Error displaying tree: {e}")

        # ---- PLUGIN COMMANDS ----
        elif cmd.split()[0].lower() in COMMANDS:
            try:
                args = cmd.split()[1:]
                COMMANDS[cmd.split()[0].lower()](args, cmd)
            except Exception as e:
                print_error(f"Plugin error: {e}")

        else:
            # ---- .FOLDER and .FILE shortcuts ----
            if current_path and cmd.endswith('.folder'):
                folder_name = cmd[:-7]  # Remove '.folder'
                if folder_name:
                    new_folder = os.path.join(current_path, folder_name)
                    try:
                        os.makedirs(new_folder)
                        print_success(f"Folder created: {Fore.YELLOW}{folder_name}")
                    except FileExistsError:
                        print_error(f"Folder '{folder_name}' already exists")
                    except Exception as e:
                        print_error(f"Failed to create folder: {e}")
                else:
                    print_error("Invalid folder name")
    
            elif current_path and cmd.endswith('.file'):
                file_name = cmd[:-5]  # Remove '.file'
                if file_name:
                    new_file = os.path.join(current_path, file_name)
                    try:
                        open(new_file, "w").close()
                        print_success(f"File created: {Fore.YELLOW}{file_name}")
                    except Exception as e:
                        print_error(f"Failed to create file: {e}")
                else:
                    print_error("Invalid file name")
    
            # ---- AUTO-DETECT: Try to find and run the file ----
            elif current_path and not cmd.startswith(" "):
                # Check if it's a file in current directory
                potential_file = os.path.join(current_path, cmd)
    
                # First check if file exists
                if os.path.exists(potential_file):
                    # It's a file
                    if os.path.isfile(potential_file):
                        ext = os.path.splitext(potential_file)[1].lower()
    
                        # Auto-run HTML files in Chrome
                        if ext == ".html":
                            print_output(f"🌐 Detected HTML file. Opening in Chrome...")
                            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                            if os.path.exists(chrome_path):
                                subprocess.run([chrome_path, potential_file])
                                print_success("Launched successfully!")
                            else:
                                print_error("Chrome not found!")
    
                        # Auto-open code files in VS Code
                        elif ext in [".py", ".js", ".java", ".cpp", ".c", ".cs", ".css", ".jsx"]:
                            print_output(f"💻 Detected code file. Opening in VS Code...")
                            os.system(f'code "{potential_file}"')
                            print_success("Launched successfully!")
    
                        # Auto-open with default program
                        else:
                            print_output(f"📂 Opening with default program...")
                            os.startfile(potential_file)
                            print_success("Launched successfully!")
    
                    # It's a folder
                    elif os.path.isdir(potential_file):
                        current_path = potential_file
                        print_success(f"Entered folder: {Fore.YELLOW}{current_path}")
    
                # File/folder doesn't exist
                else:
                    print_error(f"❌ File or folder '{cmd}' not found!")
                    print_info(f"💡 Tip: Type 'ls' to see available files and folders")
            else:
                print_error(f"Unknown command: '{cmd}'. Type 'help' for available commands")
    
        separator()

if __name__ == "__main__":
    main()
