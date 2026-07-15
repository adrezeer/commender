"""
commands/system_info.py
System diagnostics, process management, and network info.
Ported from the original DCMDS debug/tasks/wifi/ip commands.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import time
from typing import List

import psutil

from core.result import CommandResult


def get_debug_info() -> CommandResult:
    memory = psutil.virtual_memory()
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "total_gb": usage.total / (1024 ** 3),
                "used_gb": usage.used / (1024 ** 3),
                "free_gb": usage.free / (1024 ** 3),
                "percent": usage.percent,
                "fstype": partition.fstype,
            })
        except Exception:
            pass

    return CommandResult.output(
        "System diagnostics",
        python_version=sys.version.split()[0],
        executable=sys.executable,
        platform=sys.platform,
        os=f"{platform.system()} {platform.release()}",
        os_version=platform.version(),
        architecture=platform.machine(),
        computer_name=platform.node(),
        processor=platform.processor(),
        cpu_cores_physical=psutil.cpu_count(logical=False),
        cpu_cores_logical=psutil.cpu_count(logical=True),
        cpu_percent=psutil.cpu_percent(interval=0.3),
        ram_total_gb=memory.total / (1024 ** 3),
        ram_available_gb=memory.available / (1024 ** 3),
        ram_used_gb=memory.used / (1024 ** 3),
        ram_percent=memory.percent,
        disks=disks,
    )


def get_tasks(limit: int = 50) -> CommandResult:
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    processes.sort(key=lambda x: x["memory_percent"] or 0, reverse=True)
    return CommandResult.output("Running tasks", processes=processes[:limit], total=len(processes))


def end_task(pid: int) -> CommandResult:
    try:
        process = psutil.Process(pid)
        name = process.name()
        process.terminate()
        time.sleep(0.5)
        if process.is_running():
            process.kill()
        return CommandResult.success(f"Task ended: {name} (PID: {pid})")
    except psutil.NoSuchProcess:
        return CommandResult.error(f"Process with PID {pid} not found")
    except psutil.AccessDenied:
        return CommandResult.error("Access denied — try running as administrator")
    except Exception as e:
        return CommandResult.error(f"Failed to end task: {e}")


def restart_task(pid: int) -> CommandResult:
    try:
        process = psutil.Process(pid)
        name = process.name()
        exe_path = process.exe()
        process.terminate()
        time.sleep(0.5)
        if process.is_running():
            process.kill()
        time.sleep(1)
        subprocess.Popen([exe_path])
        return CommandResult.success(f"Task restarted: {name}")
    except psutil.NoSuchProcess:
        return CommandResult.error(f"Process with PID {pid} not found")
    except psutil.AccessDenied:
        return CommandResult.error("Access denied — try running as administrator")
    except Exception as e:
        return CommandResult.error(f"Failed to restart task: {e}")


def scan_wifi() -> CommandResult:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks"],
            capture_output=True, text=True, encoding="cp1256",
        )
        if result.returncode == 0:
            return CommandResult.output("WiFi networks", raw=result.stdout)
        return CommandResult.error("Failed to scan WiFi networks")
    except Exception as e:
        return CommandResult.error(f"Error scanning WiFi: {e}")


def wifi_password(network_name: str) -> CommandResult:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "profile", network_name, "key=clear"],
            capture_output=True, text=True, encoding="cp1256",
        )
        if result.returncode != 0:
            return CommandResult.error(f"Network '{network_name}' not found in saved networks")
        for line in result.stdout.split("\n"):
            if "Key Content" in line or "محتوى المفتاح" in line:
                password = line.split(":")[-1].strip()
                return CommandResult.output(
                    "WiFi password", network=network_name, password=password
                )
        return CommandResult.warning("Password not found or network not saved")
    except Exception as e:
        return CommandResult.error(f"Error retrieving password: {e}")


def get_ip_info() -> CommandResult:
    try:
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        active: List[dict] = []
        for name, addresses in interfaces.items():
            if name not in stats or not stats[name].isup:
                continue
            entry = {"interface": name, "speed_mbps": stats[name].speed, "addresses": []}
            for addr in addresses:
                fam = str(addr.family)
                if fam == "AddressFamily.AF_INET":
                    entry["addresses"].append({"type": "IPv4", "value": addr.address})
                elif fam == "AddressFamily.AF_INET6":
                    entry["addresses"].append({"type": "IPv6", "value": addr.address})
                elif fam == "AddressFamily.AF_LINK":
                    entry["addresses"].append({"type": "MAC", "value": addr.address})
            active.append(entry)
        return CommandResult.output("Network information", interfaces=active)
    except Exception as e:
        return CommandResult.error(f"Error getting IP info: {e}")
