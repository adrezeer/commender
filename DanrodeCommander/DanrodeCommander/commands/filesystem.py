"""
commands/filesystem.py
File and directory operations — ported from the original DCMDS command set.
Each function is pure: it takes explicit arguments and returns a CommandResult
(or raises), with no console I/O or global state.
"""

from __future__ import annotations

import datetime
import fnmatch
import os
import shutil
import string
from typing import List

from core.result import CommandResult


def list_drives() -> List[str]:
    return [f"{l}:\\" for l in string.ascii_uppercase if os.path.exists(f"{l}:\\")]


def list_items(current_path: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No path selected. Choose a drive first.")
    try:
        items = os.listdir(current_path)
        folders = sorted(i for i in items if os.path.isdir(os.path.join(current_path, i)))
        files = sorted(i for i in items if not os.path.isdir(os.path.join(current_path, i)))
        return CommandResult.output(
            f"Contents of {current_path}",
            folders=folders,
            files=files,
            total_folders=len(folders),
            total_files=len(files),
        )
    except Exception as e:
        return CommandResult.error(f"Cannot access this folder: {e}")


def change_directory(current_path: str, target: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No current path. Choose a drive first.")
    new_path = os.path.join(current_path, target)
    if os.path.isdir(new_path):
        return CommandResult.success(f"Entered folder: {new_path}", new_path=new_path)
    return CommandResult.error("Folder not found")


def go_back(current_path: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No current path selected")
    if len(current_path) <= 3:
        return CommandResult.success("Returned to drive selection.", new_path=None)
    parent = os.path.dirname(current_path.rstrip("\\"))
    if parent and len(parent) > 2:
        return CommandResult.success(f"Moved to: {parent}", new_path=parent)
    new_path = parent + "\\"
    return CommandResult.success(f"Moved to root: {new_path}", new_path=new_path)


def copy_file(source: str, destination: str) -> CommandResult:
    try:
        if os.path.isfile(source):
            shutil.copy2(source, destination)
            return CommandResult.success(f"File copied: {source} → {destination}")
        return CommandResult.error("Source file not found")
    except Exception as e:
        return CommandResult.error(f"Failed to copy file: {e}")


def move_file(source: str, destination: str) -> CommandResult:
    try:
        if os.path.isfile(source):
            shutil.move(source, destination)
            return CommandResult.success(f"File moved: {source} → {destination}")
        return CommandResult.error("Source file not found")
    except Exception as e:
        return CommandResult.error(f"Failed to move file: {e}")


def rename_file(old_name: str, new_name: str) -> CommandResult:
    try:
        if os.path.exists(old_name):
            os.rename(old_name, new_name)
            return CommandResult.success(f"File renamed: {old_name} → {new_name}")
        return CommandResult.error("File not found")
    except Exception as e:
        return CommandResult.error(f"Failed to rename file: {e}")


def search_files(current_path: str, pattern: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No path selected")
    try:
        found = []
        for root, _dirs, files in os.walk(current_path):
            for filename in files:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    full_path = os.path.join(root, filename)
                    found.append(os.path.relpath(full_path, current_path))
        return CommandResult.output(f"Found {len(found)} file(s)", files=found)
    except Exception as e:
        return CommandResult.error(f"Search error: {e}")


def file_info(current_path: str, filename: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No path selected")
    filepath = os.path.join(current_path, filename)
    if not os.path.exists(filepath):
        return CommandResult.error("File not found")
    try:
        stat_info = os.stat(filepath)
        info = {
            "name": filename,
            "path": filepath,
            "size_bytes": stat_info.st_size,
            "is_dir": os.path.isdir(filepath),
            "created": datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "extension": os.path.splitext(filename)[1] or "No extension",
        }
        return CommandResult.output(f"File info for {filename}", **info)
    except Exception as e:
        return CommandResult.error(f"Error getting file info: {e}")


def create_file(current_path: str, name: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No path selected")
    path = os.path.join(current_path, name)
    if os.path.exists(path):
        return CommandResult.error("File already exists")
    try:
        open(path, "w").close()
        return CommandResult.success(f"File created: {path}")
    except Exception as e:
        return CommandResult.error(f"Failed to create file: {e}")


def delete_file(current_path: str, name: str) -> CommandResult:
    """Caller (GUI) is responsible for confirming with the user first."""
    if not current_path:
        return CommandResult.error("No path selected")
    path = os.path.join(current_path, name)
    if not os.path.isfile(path):
        return CommandResult.error("File not found")
    try:
        os.remove(path)
        return CommandResult.success(f"File deleted: {path}")
    except Exception as e:
        return CommandResult.error(f"Failed to delete file: {e}")


def directory_tree(current_path: str, max_files_per_dir: int = 5, max_depth: int = 2) -> CommandResult:
    if not current_path:
        return CommandResult.error("No path selected")
    lines: List[str] = []
    try:
        for root, dirs, files in os.walk(current_path):
            level = root.replace(current_path, "").count(os.sep)
            indent = "  " * level
            folder_name = os.path.basename(root)
            lines.append(current_path if level == 0 else f"{indent}[DIR] {folder_name}")
            sub_indent = "  " * (level + 1)
            for f in files[:max_files_per_dir]:
                lines.append(f"{sub_indent}{f}")
            if len(files) > max_files_per_dir:
                lines.append(f"{sub_indent}... and {len(files) - max_files_per_dir} more files")
            if level >= max_depth:
                dirs[:] = []
        return CommandResult.output("Directory tree", lines=lines)
    except Exception as e:
        return CommandResult.error(f"Error displaying tree: {e}")


def make_folder(current_path: str, name: str) -> CommandResult:
    if not current_path:
        return CommandResult.error("No path selected")
    new_folder = os.path.join(current_path, name)
    try:
        os.makedirs(new_folder)
        return CommandResult.success(f"Folder created: {name}")
    except FileExistsError:
        return CommandResult.error(f"Folder '{name}' already exists")
    except Exception as e:
        return CommandResult.error(f"Failed to create folder: {e}")


def system_cleanup() -> CommandResult:
    """Caller (GUI) must confirm with the user before invoking this."""
    deleted_size = 0
    deleted_count = 0
    temp_paths = [os.environ.get("TEMP", ""), os.environ.get("TMP", ""), "C:\\Windows\\Temp"]

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
                        size = sum(
                            os.path.getsize(os.path.join(dp, fn))
                            for dp, _dn, fns in os.walk(item_path)
                            for fn in fns
                        )
                        shutil.rmtree(item_path)
                        deleted_size += size
                        deleted_count += 1
                except Exception:
                    pass

    return CommandResult.success(
        "Cleanup complete!",
        deleted_count=deleted_count,
        space_freed_mb=deleted_size / (1024 ** 2),
    )
