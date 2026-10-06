"""
modules/laptop_automation.py
─────────────────────────────
Comprehensive laptop and OS automation tools for JARVIS.
These tools are directly exposed to Google Gemini via function calling,
allowing JARVIS to perform virtually ANY manual task on Windows.
"""

import os
import sys
import subprocess
import webbrowser
import datetime
import time
import shutil
import glob
import re
import urllib.parse
import ctypes

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ─── Path Resolution Helper ──────────────────────────────────────────────────
def resolve_path(path_str: str) -> str:
    """Expand ~, desktop, downloads, documents shortcuts to absolute paths."""
    p = path_str.strip().strip('"').strip("'")
    p_lower = p.lower()

    user_home = os.path.expanduser("~")
    desktop = os.path.join(user_home, "Desktop")
    downloads = os.path.join(user_home, "Downloads")
    documents = os.path.join(user_home, "Documents")

    if p_lower in ["desktop", "on desktop", "my desktop"]:
        return desktop
    if p_lower in ["downloads", "downloads folder", "my downloads"]:
        return downloads
    if p_lower in ["documents", "documents folder", "my documents"]:
        return documents

    if p_lower.startswith(("desktop\\", "desktop/")):
        return os.path.join(desktop, p[8:])
    if p_lower.startswith(("downloads\\", "downloads/")):
        return os.path.join(downloads, p[10:])
    if p_lower.startswith(("documents\\", "documents/")):
        return os.path.join(documents, p[10:])

    return os.path.abspath(os.path.expanduser(p))


# ─── Window Helpers ──────────────────────────────────────────────────────────
def get_windows_matching(keyword: str):
    """Find all top-level windows containing keyword in title."""
    results = []
    kw = keyword.lower().strip()
    if HAS_WIN32:
        def enum_cb(hwnd, _):
            if win32gui.IsWindow(hwnd):
                length = win32gui.GetWindowTextLength(hwnd)
                if length > 0:
                    title = win32gui.GetWindowText(hwnd)
                    if kw in title.lower():
                        results.append((hwnd, title))
        try:
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass
    return results


def focus_window(hwnd) -> bool:
    """Bring a window to the foreground."""
    if not HAS_WIN32:
        return False
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        if HAS_PYAUTOGUI:
            pyautogui.press('alt')
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        return True
    except Exception:
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════════════════════
# JARVIS LAPTOP AUTOMATION TOOLS (Exposed to Gemini Function Calling)
# ═════════════════════════════════════════════════════════════════════════════

def open_application(app_name: str) -> str:
    """
    Opens any Windows application, tool, or utility on the laptop.
    Examples: camera, calendar, calculator, notepad, chrome, edge, spotify, paint,
    settings, task manager, vs code, powershell, command prompt, photos, clock.
    """
    from modules.commands import open_target
    return open_target(app_name)


def close_application(app_name: str) -> str:
    """
    Closes a running application or window on the laptop.
    Examples: notepad, calculator, camera, chrome, spotify, word.
    """
    from modules.commands import close_application as _close_app
    return _close_app(app_name)


def open_website(url_or_name: str) -> str:
    """
    Opens a website or web application in the default web browser.
    Examples: 'https://github.com', 'youtube', 'gmail', 'chatgpt', 'netflix', 'amazon'.
    """
    from modules.commands import open_target
    return open_target(url_or_name)


def close_browser_tab(site_or_title: str = "") -> str:
    """
    Closes an open tab in Google Chrome, Microsoft Edge, or Firefox.
    Can close a specific tab by name (e.g. 'youtube', 'netflix') or the currently active tab if empty.
    """
    from modules.commands import close_browser_tab as _close_tab, close_active_tab
    if not site_or_title or site_or_title.lower() in ["current", "active", "this", "tab"]:
        return close_active_tab()
    return _close_tab(site_or_title)


def play_youtube_video(query: str) -> str:
    """
    Searches YouTube for a song, artist, video, or tutorial and plays it directly.
    Example: 'iron man mark 85 theme', 'lo-fi beats', 'python tutorial for beginners'.
    """
    clean_q = query.strip()
    encoded = urllib.parse.quote(clean_q)
    url = f"https://www.youtube.com/results?search_query={encoded}"

    if HAS_REQUESTS:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=4)
            video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', r.text)
            if video_ids:
                direct_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                webbrowser.open(direct_url)
                return f"Playing '{clean_q}' on YouTube."
        except Exception:
            pass

    webbrowser.open(url)
    return f"Searching YouTube for '{clean_q}'."


def search_google(query: str) -> str:
    """
    Performs a Google search in the browser for any topic, question, or news.
    """
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return f"Searching Google for '{query}'."


def type_text(text: str, press_enter: bool = False) -> str:
    """
    Types text into the currently focused window, text box, editor, or document on the laptop.
    Set press_enter=True to automatically press the Enter key after typing.
    """
    if not HAS_PYAUTOGUI:
        return "Keyboard automation is not available."
    try:
        # Use clipboard paste for instant, Unicode-safe typing
        if HAS_PYPERCLIP:
            old_clip = pyperclip.paste()
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
        else:
            pyautogui.typewrite(text, interval=0.01)

        if press_enter:
            pyautogui.press('enter')
        return f"Typed: '{text}'"
    except Exception as e:
        return f"Failed to type text: {str(e)}"


def press_keyboard_hotkey(hotkey: str) -> str:
    """
    Presses a keyboard combination on the laptop.
    Examples: 'ctrl+c' (copy), 'ctrl+v' (paste), 'ctrl+z' (undo), 'ctrl+s' (save),
    'ctrl+w' (close tab), 'alt+tab' (switch app), 'win+d' (show desktop), 'enter', 'space', 'escape'.
    """
    if not HAS_PYAUTOGUI:
        return "Keyboard automation is not available."
    try:
        keys = [k.strip().lower() for k in hotkey.split('+')]
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        return f"Pressed hotkey {hotkey}."
    except Exception as e:
        return f"Failed to press hotkey: {str(e)}"


def mouse_click(button: str = "left", double: bool = False) -> str:
    """
    Performs a mouse click on the screen at current cursor position.
    button: 'left', 'right', or 'middle'.
    double: True for double click.
    """
    if not HAS_PYAUTOGUI:
        return "Mouse automation is not available."
    try:
        if double:
            pyautogui.doubleClick(button=button)
            return f"Double-clicked {button} mouse button."
        pyautogui.click(button=button)
        return f"Clicked {button} mouse button."
    except Exception as e:
        return f"Failed to click: {str(e)}"


def scroll_page(direction: str = "down", amount: int = 5) -> str:
    """
    Scrolls the active window up or down.
    direction: 'up' or 'down'.
    amount: number of scroll ticks (default 5).
    """
    if not HAS_PYAUTOGUI:
        return "Scroll automation unavailable."
    try:
        ticks = -abs(amount) * 100 if direction.lower() == "down" else abs(amount) * 100
        pyautogui.scroll(ticks)
        return f"Scrolled {direction}."
    except Exception as e:
        return f"Scroll failed: {str(e)}"


def show_desktop() -> str:
    """
    Minimizes all open windows and reveals the Windows Desktop (Win+D).
    """
    if HAS_PYAUTOGUI:
        pyautogui.hotkey('win', 'd')
        return "Minimizing all windows to show Desktop."
    return "Could not minimize windows."


def switch_to_window(app_or_title: str) -> str:
    """
    Switches active focus to an open window matching the given application name or title.
    Example: 'Chrome', 'Notepad', 'Visual Studio Code', 'Spotify'.
    """
    wins = get_windows_matching(app_or_title)
    if wins:
        hwnd, title = wins[0]
        if focus_window(hwnd):
            return f"Switched to '{title}'."
    if HAS_PYAUTOGUI:
        pyautogui.hotkey('alt', 'tab')
        return f"Switched active window."
    return f"Could not find open window matching '{app_or_title}'."


def create_file(file_path: str, content: str = "") -> str:
    """
    Creates a new text or code file with optional content anywhere on the laptop.
    Supports relative shortcuts like 'desktop/notes.txt', 'downloads/list.py', or full paths.
    """
    full_path = resolve_path(file_path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created successfully at: {full_path}"
    except Exception as e:
        return f"Failed to create file: {str(e)}"


def read_file_content(file_path: str) -> str:
    """
    Reads and returns the contents of a text, log, or code file on the laptop.
    """
    full_path = resolve_path(file_path)
    if not os.path.exists(full_path):
        return f"File not found: {full_path}"
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(2000)
            return f"File contents of {os.path.basename(full_path)}:\n{text}"
    except Exception as e:
        return f"Failed to read file: {str(e)}"


def delete_file(file_path: str) -> str:
    """
    Deletes a file from the laptop.
    """
    full_path = resolve_path(file_path)
    if not os.path.exists(full_path):
        return f"File does not exist: {full_path}"
    try:
        os.remove(full_path)
        return f"Deleted file: {os.path.basename(full_path)}"
    except Exception as e:
        return f"Failed to delete file: {str(e)}"


def create_folder(folder_path: str) -> str:
    """
    Creates a new directory / folder on the laptop.
    Example: 'desktop/MyProject', 'downloads/Temp'.
    """
    full_path = resolve_path(folder_path)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Folder created at: {full_path}"
    except Exception as e:
        return f"Failed to create folder: {str(e)}"


def list_files_in_folder(folder_path: str = "desktop") -> str:
    """
    Lists files and folders inside a directory. Defaults to 'desktop'.
    Supports 'desktop', 'downloads', 'documents', or any path.
    """
    full_path = resolve_path(folder_path or "desktop")
    if not os.path.exists(full_path):
        return f"Directory does not exist: {full_path}"
    try:
        items = os.listdir(full_path)
        if not items:
            return f"Folder '{os.path.basename(full_path)}' is empty."
        display = items[:15]
        extra = f" (and {len(items)-15} more)" if len(items) > 15 else ""
        return f"Items in {os.path.basename(full_path)}: {', '.join(display)}{extra}"
    except Exception as e:
        return f"Could not list directory: {str(e)}"


def search_for_files(filename: str, start_folder: str = "desktop") -> str:
    """
    Searches for files matching a filename or extension on the laptop.
    """
    start_path = resolve_path(start_folder)
    matches = []
    kw = filename.lower()
    try:
        for root, dirs, files in os.walk(start_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['$Recycle.Bin', 'Windows']]
            for f in files:
                if kw in f.lower():
                    matches.append(os.path.join(root, f))
                    if len(matches) >= 5:
                        break
            if len(matches) >= 5:
                break
        if matches:
            return f"Found {len(matches)} matching file(s): " + ", ".join([os.path.basename(m) for m in matches])
        return f"No files matching '{filename}' were found in {start_folder}."
    except Exception as e:
        return f"Search error: {str(e)}"


def open_folder_in_explorer(folder_name: str = "desktop") -> str:
    """
    Opens a folder in Windows File Explorer (e.g. desktop, downloads, documents).
    """
    full_path = resolve_path(folder_name)
    try:
        os.startfile(full_path)
        return f"Opened {folder_name} in File Explorer."
    except Exception as e:
        return f"Failed to open folder: {str(e)}"


def empty_recycle_bin() -> str:
    """
    Permanently empties the Windows Recycle Bin.
    """
    try:
        res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        if res == 0:
            return "Recycle Bin has been emptied."
    except Exception:
        pass
    try:
        subprocess.run(["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], capture_output=True)
        return "Recycle Bin has been emptied."
    except Exception as e:
        return f"Could not empty recycle bin: {str(e)}"


def set_laptop_volume(level: int) -> str:
    """
    Sets laptop audio volume from 0 (mute) to 100 (maximum).
    """
    from modules.commands import set_volume
    return set_volume(level)


def mute_laptop_volume() -> str:
    """
    Toggles audio mute on the laptop.
    """
    from modules.commands import mute_volume
    return mute_volume()


def set_laptop_brightness(level: int) -> str:
    """
    Sets laptop screen brightness from 0 to 100 percent.
    """
    from modules.commands import set_brightness
    return set_brightness(level)


def take_laptop_screenshot(name: str = "") -> str:
    """
    Takes a full screenshot of the laptop screen and saves it to the Screenshots folder.
    """
    from modules.commands import take_screenshot
    return take_screenshot(name or None)


def get_laptop_status() -> str:
    """
    Returns real-time laptop status: CPU usage, RAM usage, storage space, and battery percentage.
    """
    from modules.commands import get_system_info
    return get_system_info()


def laptop_power(action: str) -> str:
    """
    Controls laptop power. action must be: 'shutdown', 'restart', 'sleep', 'lock', or 'cancel'.
    """
    from modules.commands import system_shutdown, system_restart, system_sleep, lock_screen, cancel_shutdown
    act = action.lower().strip()
    if "shut" in act:
        return system_shutdown(30)
    if "restart" in act or "reboot" in act:
        return system_restart(30)
    if "sleep" in act:
        return system_sleep()
    if "lock" in act:
        return lock_screen()
    if "cancel" in act:
        return cancel_shutdown()
    return f"Unknown power action '{action}'."


def get_wifi_networks() -> str:
    """
    Scans and lists visible Wi-Fi networks near the laptop.
    """
    try:
        res = subprocess.run(["netsh", "wlan", "show", "networks"], capture_output=True, text=True, timeout=5)
        ssids = re.findall(r'SSID\s+\d+\s+:\s+(.+)', res.stdout)
        if ssids:
            return f"Visible Wi-Fi networks: {', '.join(ssids[:6])}"
        return "No Wi-Fi networks found or Wi-Fi is turned off."
    except Exception as e:
        return f"Could not scan Wi-Fi: {str(e)}"


def clipboard_copy(text: str) -> str:
    """
    Copies text to the Windows clipboard.
    """
    if HAS_PYPERCLIP:
        pyperclip.copy(text)
        return f"Copied text to clipboard."
    return "Clipboard unavailable."


def clipboard_read() -> str:
    """
    Reads and returns whatever text is currently stored in the Windows clipboard.
    """
    if HAS_PYPERCLIP:
        content = pyperclip.paste()
        if content:
            return f"Clipboard contains: {content[:300]}"
        return "Clipboard is currently empty."
    return "Clipboard unavailable."


def execute_powershell(command: str) -> str:
    """
    Executes any PowerShell or CMD command directly on the Windows laptop and returns output.
    Allows JARVIS to perform any advanced administrative or custom task.
    """
    try:
        res = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True, text=True, timeout=20
        )
        out = (res.stdout.strip() or res.stderr.strip())
        return out[:500] if out else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 20 seconds."
    except Exception as e:
        return f"Execution error: {str(e)}"


# ─── Tool Registry for Gemini ────────────────────────────────────────────────
LAPTOP_TOOLS = [
    open_application,
    close_application,
    open_website,
    close_browser_tab,
    play_youtube_video,
    search_google,
    type_text,
    press_keyboard_hotkey,
    mouse_click,
    scroll_page,
    show_desktop,
    switch_to_window,
    create_file,
    read_file_content,
    delete_file,
    create_folder,
    list_files_in_folder,
    search_for_files,
    open_folder_in_explorer,
    empty_recycle_bin,
    set_laptop_volume,
    mute_laptop_volume,
    set_laptop_brightness,
    take_laptop_screenshot,
    get_laptop_status,
    laptop_power,
    get_wifi_networks,
    clipboard_copy,
    clipboard_read,
    execute_powershell,
]
