"""
modules/commands.py
────────────────────
Command dispatcher for JARVIS.
Parses voice/text commands and routes to appropriate handler functions.
Includes advanced app launching (Windows URI + exes), tab and window closing
(Ctrl+W for tabs, WM_CLOSE / taskkill for apps), system controls, and AI fallback.
"""

import os
import sys
import subprocess
import webbrowser
import datetime
import json
import threading
import time
import platform
import shutil
import glob
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_NAME, SCREENSHOT_DIR, REMINDER_CHECK_INTERVAL, EMAIL_ADDRESS, EMAIL_PASSWORD

# Optional UI automation imports
try:
    import win32gui
    import win32con
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


# ─── Typo & Synonym Normalization ──────────────────────────────────────────
TYPO_MAP = {
    'calender': 'calendar',
    'camra': 'camera',
    'webcam': 'camera',
    'chrom': 'chrome',
    'youtub': 'youtube',
    'notpad': 'notepad',
    'calc': 'calculator',
    'terminal': 'command prompt',
    'pictures': 'photos',
    'gallery': 'photos',
    'alarms': 'clock',
    'timer': 'clock',
    'stopwatch': 'clock',
    'this pc': 'file explorer',
    'my computer': 'file explorer',
    'my pc': 'file explorer',
    'explorer': 'file explorer',
    'recyclebin': 'recycle bin',
    'trash': 'recycle bin',
    'snip': 'snipping tool',
    'snip tool': 'snipping tool',
}

# ─── Application Database ──────────────────────────────────────────────────
# open: URI scheme or exe command
# process: executable names for taskkill
# title: window title substring for graceful close
APPLICATIONS = {
    # Windows Built-in UWP & Utilities
    'camera': {
        'open': 'microsoft.windows.camera:',
        'process': ['WindowsCamera.exe', 'Camera.exe'],
        'title': 'Camera'
    },
    'calendar': {
        'open': 'outlookcal:',
        'process': ['HxCalendarAppImm.exe', 'Outlook.exe'],
        'title': 'Calendar',
        'web_fallback': 'https://calendar.google.com'
    },
    'calculator': {
        'open': 'calc.exe',
        'process': ['CalculatorApp.exe', 'Calculator.exe', 'calc.exe'],
        'title': 'Calculator'
    },
    'notepad': {
        'open': 'notepad.exe',
        'process': ['notepad.exe', 'Notepad.exe'],
        'title': 'Notepad'
    },
    'clock': {
        'open': 'ms-clock:',
        'process': ['Time.exe', 'Alarms.exe'],
        'title': 'Clock'
    },
    'photos': {
        'open': 'ms-photos:',
        'process': ['Microsoft.Photos.exe', 'Photos.exe'],
        'title': 'Photos'
    },
    'settings': {
        'open': 'ms-settings:',
        'process': ['SystemSettings.exe'],
        'title': 'Settings'
    },
    'control panel': {
        'open': 'control.exe',
        'process': ['control.exe'],
        'title': 'Control Panel'
    },
    'task manager': {
        'open': 'taskmgr.exe',
        'process': ['Taskmgr.exe', 'taskmgr.exe'],
        'title': 'Task Manager'
    },
    'snipping tool': {
        'open': 'SnippingTool.exe',
        'process': ['SnippingTool.exe', 'ScreenClippingHost.exe'],
        'title': 'Snipping Tool'
    },
    'paint': {
        'open': 'mspaint.exe',
        'process': ['mspaint.exe', 'PaintApp.exe'],
        'title': 'Paint'
    },
    'wordpad': {
        'open': 'wordpad.exe',
        'process': ['wordpad.exe'],
        'title': 'WordPad'
    },
    'microsoft store': {
        'open': 'ms-windows-store:',
        'process': ['WinStore.App.exe'],
        'title': 'Microsoft Store'
    },
    'store': {
        'open': 'ms-windows-store:',
        'process': ['WinStore.App.exe'],
        'title': 'Microsoft Store'
    },
    'command prompt': {
        'open': 'cmd.exe',
        'process': ['cmd.exe'],
        'title': 'Command Prompt'
    },
    'cmd': {
        'open': 'cmd.exe',
        'process': ['cmd.exe'],
        'title': 'Command Prompt'
    },
    'powershell': {
        'open': 'powershell.exe',
        'process': ['powershell.exe'],
        'title': 'PowerShell'
    },
    'file explorer': {
        'open': 'explorer.exe',
        'process': ['explorer.exe'],
        'title': 'File Explorer'
    },
    'recycle bin': {
        'open': 'shell:RecycleBinFolder',
        'process': [],
        'title': 'Recycle Bin'
    },

    # Web Browsers
    'chrome': {
        'open': 'chrome.exe',
        'process': ['chrome.exe'],
        'title': 'Google Chrome'
    },
    'google chrome': {
        'open': 'chrome.exe',
        'process': ['chrome.exe'],
        'title': 'Google Chrome'
    },
    'edge': {
        'open': 'msedge.exe',
        'process': ['msedge.exe'],
        'title': 'Microsoft Edge'
    },
    'microsoft edge': {
        'open': 'msedge.exe',
        'process': ['msedge.exe'],
        'title': 'Microsoft Edge'
    },
    'firefox': {
        'open': 'firefox.exe',
        'process': ['firefox.exe'],
        'title': 'Firefox'
    },
    'brave': {
        'open': 'brave.exe',
        'process': ['brave.exe'],
        'title': 'Brave'
    },
    'opera': {
        'open': 'opera.exe',
        'process': ['opera.exe'],
        'title': 'Opera'
    },

    # Desktop Software
    'spotify': {
        'open': 'spotify.exe',
        'process': ['Spotify.exe', 'spotify.exe'],
        'title': 'Spotify'
    },
    'vlc': {
        'open': 'vlc.exe',
        'process': ['vlc.exe'],
        'title': 'VLC media player'
    },
    'visual studio code': {
        'open': 'code.exe',
        'process': ['Code.exe', 'code.exe'],
        'title': 'Visual Studio Code'
    },
    'vs code': {
        'open': 'code.exe',
        'process': ['Code.exe', 'code.exe'],
        'title': 'Visual Studio Code'
    },
    'vscode': {
        'open': 'code.exe',
        'process': ['Code.exe', 'code.exe'],
        'title': 'Visual Studio Code'
    },
    'pycharm': {
        'open': 'pycharm64.exe',
        'process': ['pycharm64.exe', 'pycharm.exe'],
        'title': 'PyCharm'
    },
    'word': {
        'open': 'winword.exe',
        'process': ['WINWORD.EXE', 'winword.exe'],
        'title': 'Word'
    },
    'excel': {
        'open': 'excel.exe',
        'process': ['EXCEL.EXE', 'excel.exe'],
        'title': 'Excel'
    },
    'powerpoint': {
        'open': 'powerpnt.exe',
        'process': ['POWERPNT.EXE', 'powerpnt.exe'],
        'title': 'PowerPoint'
    },
    'outlook': {
        'open': 'outlook.exe',
        'process': ['OUTLOOK.EXE', 'outlook.exe'],
        'title': 'Outlook'
    },
    'teams': {
        'open': 'teams.exe',
        'process': ['Teams.exe', 'ms-teams.exe'],
        'title': 'Teams'
    },
    'discord': {
        'open': 'discord.exe',
        'process': ['Discord.exe', 'discord.exe'],
        'title': 'Discord'
    },
    'zoom': {
        'open': 'zoom.exe',
        'process': ['Zoom.exe', 'zoom.exe'],
        'title': 'Zoom'
    },
    'slack': {
        'open': 'slack.exe',
        'process': ['slack.exe'],
        'title': 'Slack'
    },
    'whatsapp': {
        'open': 'whatsapp.exe',
        'process': ['WhatsApp.exe', 'whatsapp.exe'],
        'title': 'WhatsApp'
    },
    'telegram': {
        'open': 'telegram.exe',
        'process': ['Telegram.exe', 'telegram.exe'],
        'title': 'Telegram'
    },
    'steam': {
        'open': 'steam.exe',
        'process': ['steam.exe', 'Steam.exe'],
        'title': 'Steam'
    },
    'obs': {
        'open': 'obs64.exe',
        'process': ['obs64.exe'],
        'title': 'OBS'
    },
    'photoshop': {
        'open': 'photoshop.exe',
        'process': ['Photoshop.exe'],
        'title': 'Photoshop'
    }
}

# ─── Website Map ─────────────────────────────────────────────────────────────
WEBSITES = {
    'youtube': 'https://www.youtube.com',
    'google': 'https://www.google.com',
    'github': 'https://www.github.com',
    'wikipedia': 'https://www.wikipedia.org',
    'gmail': 'https://mail.google.com',
    'google calendar': 'https://calendar.google.com',
    'facebook': 'https://www.facebook.com',
    'twitter': 'https://twitter.com',
    'x': 'https://x.com',
    'instagram': 'https://www.instagram.com',
    'linkedin': 'https://www.linkedin.com',
    'reddit': 'https://www.reddit.com',
    'netflix': 'https://www.netflix.com',
    'amazon': 'https://www.amazon.com',
    'spotify web': 'https://open.spotify.com',
    'stackoverflow': 'https://stackoverflow.com',
    'chatgpt': 'https://chatgpt.com',
    'google drive': 'https://drive.google.com',
    'google docs': 'https://docs.google.com',
    'google maps': 'https://maps.google.com',
    'news': 'https://news.google.com',
    'weather': 'https://www.weather.com',
    'translate': 'https://translate.google.com',
    'twitch': 'https://www.twitch.tv',
    'notion': 'https://www.notion.so',
    'canva': 'https://www.canva.com',
    'imdb': 'https://www.imdb.com',
    'bing': 'https://www.bing.com',
}

# ─── Reminders Storage ───────────────────────────────────────────────────────
REMINDERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reminders.json")
_reminders = []
_reminder_callback = None


def _load_reminders():
    global _reminders
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r") as f:
                _reminders = json.load(f)
        except Exception:
            _reminders = []


def _save_reminders():
    with open(REMINDERS_FILE, "w") as f:
        json.dump(_reminders, f, indent=2)


def set_reminder_callback(callback):
    """Set a GUI callback for reminder notifications."""
    global _reminder_callback
    _reminder_callback = callback


def _reminder_checker():
    """Background thread that fires reminders at the right time."""
    _load_reminders()
    while True:
        now = datetime.datetime.now()
        for reminder in list(_reminders):
            try:
                remind_time = datetime.datetime.fromisoformat(reminder["datetime"])
                if now >= remind_time and not reminder.get("fired", False):
                    reminder["fired"] = True
                    msg = f"Reminder: {reminder['message']}"
                    if _reminder_callback:
                        _reminder_callback(msg)
                    print(f"[Reminder] {msg}")
            except Exception:
                pass
        _save_reminders()
        time.sleep(REMINDER_CHECK_INTERVAL)


# Start reminder thread
_reminder_thread = threading.Thread(target=_reminder_checker, daemon=True)
_reminder_thread.start()


# ─── Window Helpers ──────────────────────────────────────────────────────────
def get_windows_matching(keyword: str):
    """Return list of (hwnd, title) matching keyword."""
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

    # Fallback to pygetwindow
    if not results:
        try:
            import pygetwindow as gw
            all_wins = gw.getAllWindows()
            for w in all_wins:
                if w.title and kw in w.title.lower():
                    results.append((w._hWnd, w.title))
        except Exception:
            pass

    return results


def focus_window(hwnd) -> bool:
    """Bring window to foreground reliably."""
    if not HAS_WIN32:
        return False
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        if HAS_PYAUTOGUI:
            # Press ALT to bypass Windows SetForegroundWindow restriction
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


# ─── App & Web Launching ─────────────────────────────────────────────────────
def open_target(target_name: str) -> str:
    """
    Intelligently opens applications (UWP or desktop exe) or websites.
    Never searches Google unless requested.
    """
    raw = target_name.lower().strip()

    # Normalize typos
    cleaned = TYPO_MAP.get(raw, raw)

    # 1. Exact match in Applications (Camera, Calendar, Calculator, etc.)
    if cleaned in APPLICATIONS:
        app_data = APPLICATIONS[cleaned]
        open_cmd = app_data['open']
        try:
            os.startfile(open_cmd)
            return f"Opening {cleaned}."
        except Exception:
            try:
                subprocess.Popen(f'start "" "{open_cmd}"', shell=True)
                return f"Opening {cleaned}."
            except Exception as e:
                if 'web_fallback' in app_data:
                    webbrowser.open(app_data['web_fallback'])
                    return f"Opening {cleaned} online."
                return f"Could not launch {cleaned}: {str(e)}"

    # 2. Exact match in Websites (YouTube, Google, GitHub, etc.)
    if cleaned in WEBSITES:
        url = WEBSITES[cleaned]
        webbrowser.open(url)
        return f"Opening {cleaned}."

    # 3. Partial match in Applications
    for key, val in APPLICATIONS.items():
        if key in cleaned or cleaned in key:
            open_cmd = val['open']
            try:
                os.startfile(open_cmd)
                return f"Opening {key}."
            except Exception:
                try:
                    subprocess.Popen(f'start "" "{open_cmd}"', shell=True)
                    return f"Opening {key}."
                except Exception as e:
                    if 'web_fallback' in val:
                        webbrowser.open(val['web_fallback'])
                        return f"Opening {key} online."
                    return f"Could not launch {key}: {str(e)}"

    # 4. Partial match in Websites
    for site_key, site_url in WEBSITES.items():
        if site_key in cleaned or cleaned in site_key:
            webbrowser.open(site_url)
            return f"Opening {site_key}."


    # 3. Direct file/URL check
    if cleaned.startswith(('http://', 'https://', 'www.')) or ('.' in cleaned and not ' ' in cleaned):
        url = cleaned if cleaned.startswith(('http://', 'https://')) else 'https://' + cleaned
        webbrowser.open(url)
        return f"Opening {cleaned} in your browser."

    # 4. Try native Windows start for unregistered apps
    try:
        os.startfile(cleaned)
        return f"Opening {cleaned}."
    except Exception:
        pass

    try:
        proc = subprocess.Popen(f'start "" "{cleaned}"', shell=True)
        return f"Opening {cleaned}."
    except Exception:
        pass

    return f"I couldn't find an application or website named '{target_name}'. Please verify the name."


# ─── App & Tab Closing ───────────────────────────────────────────────────────
def close_target(query: str) -> str:
    """
    Closes either:
    1. A specific browser tab (e.g. YouTube, Netflix)
    2. The active browser tab ("close tab", "close current tab")
    3. An application (Camera, Notepad, Calculator, Chrome, etc.)
    """
    q = query.lower().strip()

    # Strip conversational prefixes
    for prefix in ['tell it to ', 'please ', 'can you ', 'jarvis ', 'could you ']:
        if q.startswith(prefix):
            q = q[len(prefix):].strip()

    q = q.replace('openend', 'opened')

    # Case A: "close [the] [opened] {target} from/in {browser}"
    # Example: "close the opened youtube from chrome"
    match_from = re.search(r'close\s+(?:the\s+)?(?:opened\s+|open\s+)?(.*?)\s+(?:from|in|on)\s+(chrome|edge|firefox|browser)', q)
    if match_from:
        target_site = match_from.group(1).strip()
        browser_name = match_from.group(2).strip()
        return close_browser_tab(target_site, browser_name)

    # Case B: "close {target} tab" or "close the {target} tab"
    match_tab = re.search(r'close\s+(?:the\s+)?(.*?)\s+tab', q)
    if match_tab:
        target_tab = match_tab.group(1).strip()
        if target_tab in ['', 'this', 'current', 'active']:
            return close_active_tab()
        return close_browser_tab(target_tab)

    # Case C: "close tab" / "close current tab" / "close this tab"
    if any(p in q for p in ['close tab', 'close this tab', 'close current tab', 'close active tab']):
        return close_active_tab()

    # Extract clean target by removing "close" and "kill"
    raw_target = re.sub(r'^(?:close|kill)\s+(?:the\s+)?(?:opened\s+|open\s+)?', '', q).strip()

    # Normalize typos
    target = TYPO_MAP.get(raw_target, raw_target)

    # Case D: Target is a known website (e.g. "close youtube", "close netflix")
    if target in WEBSITES or any(site in target for site in ['youtube', 'netflix', 'facebook', 'instagram', 'twitter', 'reddit']):
        return close_browser_tab(target)

    # Case E: Close application
    return close_application(target)


def close_active_tab() -> str:
    """Closes the currently active browser tab using Ctrl+W."""
    if HAS_PYAUTOGUI:
        try:
            pyautogui.hotkey('ctrl', 'w')
            return "Closed current tab."
        except Exception as e:
            return f"Failed to close tab: {str(e)}"
    return "Hotkey support is unavailable."


def close_browser_tab(tab_name: str, preferred_browser: str = None) -> str:
    """
    Finds a browser window that contains tab_name (e.g. YouTube),
    focuses it, and sends Ctrl+W to close that tab.
    """
    keyword = TYPO_MAP.get(tab_name.lower().strip(), tab_name.lower().strip())

    # 1. Search for a window title matching the tab name (e.g. "YouTube - Google Chrome")
    matching_windows = get_windows_matching(keyword)
    if matching_windows:
        hwnd, title = matching_windows[0]
        if focus_window(hwnd):
            if HAS_PYAUTOGUI:
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'w')
                return f"Closed {tab_name} in {title.split(' - ')[-1] if ' - ' in title else 'browser'}."
            elif HAS_WIN32:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return f"Closed {tab_name} window."

    # 2. If no window has the tab name in the title, check if preferred browser is open
    browser = preferred_browser or 'chrome'
    browser_windows = get_windows_matching(browser)
    if browser_windows:
        hwnd, title = browser_windows[0]
        if focus_window(hwnd):
            if HAS_PYAUTOGUI:
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'w')
                return f"Closed active tab in {browser.capitalize()}."

    return f"Could not find an open tab for '{tab_name}'."


def close_application(app_name: str) -> str:
    """
    Gracefully closes an application by window title,
    falling back to terminating its processes.
    """
    key = TYPO_MAP.get(app_name.lower().strip(), app_name.lower().strip())

    app_data = APPLICATIONS.get(key)
    if not app_data:
        for k, v in APPLICATIONS.items():
            if k in key or key in k:
                app_data = v
                key = k
                break

    closed = False

    # 1. Try graceful WM_CLOSE via window title
    title_keyword = app_data.get('title') if app_data else key
    if HAS_WIN32 and title_keyword:
        wins = get_windows_matching(title_keyword)
        for hwnd, _ in wins:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed = True
            except Exception:
                pass

    # 2. Terminate matching processes via taskkill
    process_list = app_data.get('process', []) if app_data else [key + '.exe']
    for proc in process_list:
        try:
            res = subprocess.run(["taskkill", "/F", "/IM", proc],
                                 capture_output=True, text=True)
            if res.returncode == 0:
                closed = True
        except Exception:
            pass

    if closed:
        return f"Closed {key}."

    return f"Could not find a running instance of {app_name}."


# ─── System Control ──────────────────────────────────────────────────────────
def set_volume(level: int) -> str:
    """Set system volume (0-100)."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level} percent."
    except Exception:
        script = f"$obj = New-Object -com wscript.shell; $obj.SendKeys([char]174 * 50); $obj.SendKeys([char]175 * {level // 2})"
        subprocess.run(["powershell", "-Command", script], capture_output=True)
        return f"Volume adjusted to approximately {level} percent."


def mute_volume() -> str:
    """Toggle mute."""
    if HAS_PYAUTOGUI:
        pyautogui.press('volumemute')
        return "Volume muted."
    subprocess.run(["powershell", "-Command",
        "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"], capture_output=True)
    return "Volume toggled."


def system_shutdown(delay: int = 30) -> str:
    subprocess.run(["shutdown", "/s", f"/t {delay}"], shell=True)
    return f"System will shut down in {delay} seconds."


def system_restart(delay: int = 30) -> str:
    subprocess.run(["shutdown", "/r", f"/t {delay}"], shell=True)
    return f"System will restart in {delay} seconds."


def system_sleep() -> str:
    subprocess.run(["powershell", "-Command",
        "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)"])
    return "Going to sleep."


def cancel_shutdown() -> str:
    subprocess.run(["shutdown", "/a"], shell=True)
    return "Shutdown cancelled."


def lock_screen() -> str:
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Screen locked."


def set_brightness(level: int) -> str:
    try:
        cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        return f"Brightness set to {level} percent."
    except Exception as e:
        return f"Could not adjust brightness: {str(e)}"


# ─── Screenshot ───────────────────────────────────────────────────────────────
def take_screenshot(name: str = None) -> str:
    if not HAS_PYAUTOGUI:
        return "Screenshot module is not available."
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = name or f"screenshot_{timestamp}"
        filepath = os.path.join(SCREENSHOT_DIR, f"{filename}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return f"Screenshot saved as {filename}.png in the Screenshots folder."
    except Exception as e:
        return f"Failed to take screenshot: {str(e)}"


# ─── File Management ─────────────────────────────────────────────────────────
def create_folder(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Failed to create folder: {str(e)}"


def list_files(directory: str = None) -> str:
    target = directory or os.path.expanduser("~\\Desktop")
    try:
        items = os.listdir(target)
        if not items:
            return f"The folder '{target}' is empty."
        return f"Found {len(items)} items in {target}: {', '.join(items[:10])}{'...' if len(items) > 10 else ''}"
    except Exception as e:
        return f"Could not list files: {str(e)}"


def open_file(filepath: str) -> str:
    try:
        os.startfile(filepath)
        return f"Opening {os.path.basename(filepath)}."
    except Exception as e:
        return f"Could not open file: {str(e)}"


def search_files(name: str, directory: str = None) -> str:
    search_dir = directory or os.path.expanduser("~")
    matches = []
    try:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['$Recycle.Bin', 'Windows', 'Program Files']]
            for file in files:
                if name.lower() in file.lower():
                    matches.append(os.path.join(root, file))
                    if len(matches) >= 5:
                        break
            if len(matches) >= 5:
                break
        if matches:
            return f"Found {len(matches)} file(s): {', '.join([os.path.basename(m) for m in matches])}"
        return f"No files matching '{name}' were found."
    except Exception as e:
        return f"Search error: {str(e)}"


def open_downloads() -> str:
    path = os.path.expanduser("~\\Downloads")
    os.startfile(path)
    return "Opening your Downloads folder."


def open_desktop() -> str:
    path = os.path.expanduser("~\\Desktop")
    os.startfile(path)
    return "Opening your Desktop."


def open_documents() -> str:
    path = os.path.expanduser("~\\Documents")
    os.startfile(path)
    return "Opening your Documents folder."


# ─── Media Control ────────────────────────────────────────────────────────────
def media_play_pause() -> str:
    if HAS_PYAUTOGUI:
        pyautogui.press('playpause')
        return "Toggling play/pause."
    return "Media control unavailable."


def media_next() -> str:
    if HAS_PYAUTOGUI:
        pyautogui.press('nexttrack')
        return "Skipping to next track."
    return "Media control unavailable."


def media_previous() -> str:
    if HAS_PYAUTOGUI:
        pyautogui.press('prevtrack')
        return "Going to previous track."
    return "Media control unavailable."


def media_stop() -> str:
    if HAS_PYAUTOGUI:
        pyautogui.press('stop')
        return "Stopping media."
    return "Media control unavailable."


# ─── Email ────────────────────────────────────────────────────────────────────
def send_email(to: str, subject: str, body: str) -> str:
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "Email is not configured. Please add your Gmail address and App Password in config.py."
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return f"Email sent to {to} successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"


# ─── Reminders ────────────────────────────────────────────────────────────────
def add_reminder(message: str, remind_datetime: datetime.datetime) -> str:
    _load_reminders()
    _reminders.append({
        "message": message,
        "datetime": remind_datetime.isoformat(),
        "fired": False
    })
    _save_reminders()
    return f"Reminder set: '{message}' at {remind_datetime.strftime('%I:%M %p on %B %d')}."


def list_reminders() -> str:
    _load_reminders()
    active = [r for r in _reminders if not r.get("fired", False)]
    if not active:
        return "You have no active reminders."
    return "Your reminders: " + "; ".join([r['message'] for r in active[:3]])


# ─── Terminal Commands ────────────────────────────────────────────────────────
def run_terminal_command(command: str) -> str:
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output[:300] if output else "Command executed with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Failed to run command: {str(e)}"


# ─── Info Utilities ───────────────────────────────────────────────────────────
def get_time() -> str:
    now = datetime.datetime.now()
    return f"The time is {now.strftime('%I:%M %p')}."


def get_date() -> str:
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


def get_day() -> str:
    return f"Today is {datetime.datetime.now().strftime('%A')}."


def get_system_info() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        battery = psutil.sensors_battery()
        bat_str = ""
        if battery:
            bat_str = f" Battery at {battery.percent:.0f}%."
        return (f"CPU is at {cpu}% usage. "
                f"RAM usage is {ram.percent}% of {ram.total // (1024**3)} GB. "
                f"Disk usage is {disk.percent}%.{bat_str}")
    except Exception as e:
        return f"Could not retrieve system info: {str(e)}"


def get_battery() -> str:
    try:
        import psutil
        battery = psutil.sensors_battery()
        if not battery:
            return "No battery detected — running on AC power."
        status = "charging" if battery.power_plugged else "discharging"
        return f"Battery is at {battery.percent:.0f}% and {status}."
    except Exception as e:
        return f"Could not check battery: {str(e)}"


def get_weather(city: str = "auto") -> str:
    try:
        import requests
        url = f"https://wttr.in/{city}?format=3"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.text.strip()
        return "Could not fetch weather data."
    except Exception as e:
        return f"Weather service unavailable: {str(e)}"


def search_google(query: str) -> str:
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching Google for '{query}'."


# ─── Main Command Parser ──────────────────────────────────────────────────────
def parse_and_execute(query: str, ai_brain=None, ui_log=None) -> str:
    """
    Parse a user command and execute the appropriate action.
    """
    q = query.lower().strip()

    # ── Time / Date ──────────────────────────────
    if any(p in q for p in ["what time", "what's the time", "current time", "tell me the time"]):
        return get_time()
    if any(p in q for p in ["what date", "today's date", "current date"]):
        return get_date()
    if "what day" in q:
        return get_day()

    # ── System Info ──────────────────────────────
    if any(p in q for p in ["system info", "cpu usage", "ram usage", "memory usage", "system status", "performance"]):
        return get_system_info()
    if any(p in q for p in ["battery", "power level", "charge"]):
        return get_battery()

    # ── Weather ──────────────────────────────────
    if "weather" in q:
        city = (q.replace("weather", "").replace("in", "")
                .replace("what's the", "").replace("check", "").strip())
        return get_weather(city if city else "auto")

    # ── Volume ───────────────────────────────────
    if "volume" in q:
        if "mute" in q or "silence" in q:
            return mute_volume()
        if "max" in q or "full" in q or "100" in q:
            return set_volume(100)
        if "half" in q or "50" in q:
            return set_volume(50)
        if "low" in q or "quiet" in q or "25" in q:
            return set_volume(25)
        for word in q.split():
            if word.isdigit():
                return set_volume(int(word))

    # ── Brightness ───────────────────────────────
    if "brightness" in q:
        for word in q.split():
            if word.isdigit():
                return set_brightness(int(word))
        if "max" in q or "full" in q:
            return set_brightness(100)
        if "half" in q or "50" in q:
            return set_brightness(50)
        if "low" in q:
            return set_brightness(30)

    # ── System Power ─────────────────────────────
    if "shut down" in q or "shutdown" in q:
        if "cancel" in q:
            return cancel_shutdown()
        return system_shutdown()
    if "restart" in q or "reboot" in q:
        return system_restart()
    if "sleep" in q and ("computer" in q or "mode" in q or "pc" in q):
        return system_sleep()
    if "lock" in q and ("screen" in q or "computer" in q or "pc" in q):
        return lock_screen()

    # ── Screenshot ────────────────────────────────
    if "screenshot" in q or "capture screen" in q or "take a screen" in q:
        return take_screenshot()

    # ── File & Folder Shortcuts ───────────────────
    if "open downloads" in q or "downloads folder" in q:
        return open_downloads()
    if "open desktop" in q or "go to desktop" in q:
        return open_desktop()
    if "open documents" in q or "documents folder" in q:
        return open_documents()
    if "list files" in q or "show files" in q:
        directory = q.replace("list files", "").replace("show files", "").replace("in", "").strip()
        return list_files(directory or None)
    if "search for file" in q or "find file" in q:
        name = q.replace("search for file", "").replace("find file", "").strip()
        return search_files(name)
    if "create folder" in q or "make folder" in q or "new folder" in q:
        folder_name = (q.replace("create folder", "").replace("make folder", "")
                       .replace("new folder", "").replace("called", "")
                       .replace("named", "").strip())
        path = os.path.join(os.path.expanduser("~\\Desktop"), folder_name)
        return create_folder(path)

    # ── Media Control ─────────────────────────────
    if any(p in q for p in ["play music", "play pause", "pause music", "resume music"]):
        return media_play_pause()
    if any(p in q for p in ["next song", "next track", "skip song", "skip track"]):
        return media_next()
    if any(p in q for p in ["previous song", "previous track", "last song"]):
        return media_previous()
    if "stop music" in q or "stop song" in q:
        return media_stop()

    # ── Email & Reminders ─────────────────────────
    if "send email" in q or "send mail" in q:
        return "Please use the quick email form in the right panel to compose your email."
    if "list reminders" in q or "my reminders" in q or "show reminders" in q:
        return list_reminders()

    # ── Terminal Commands ──────────────────────────
    if q.startswith("run command") or q.startswith("execute command") or q.startswith("powershell "):
        cmd = (q.replace("run command", "").replace("execute command", "")
               .replace("powershell ", "").strip())
        return run_terminal_command(cmd)

    # ── Laptop Automation: Recycle Bin ────────────
    if "empty" in q and ("recycle" in q or "bin" in q or "trash" in q):
        from modules.laptop_automation import empty_recycle_bin
        return empty_recycle_bin()

    # ── Laptop Automation: Wi-Fi Networks ──────────
    if ("wifi" in q or "wi-fi" in q) and any(w in q for w in ["show", "list", "available", "scan", "check", "networks"]):
        from modules.laptop_automation import get_wifi_networks
        return get_wifi_networks()

    # ── Laptop Automation: Clipboard ───────────────
    if "clipboard" in q:
        from modules.laptop_automation import clipboard_read, clipboard_copy
        if any(w in q for w in ["what", "show", "read", "check", "paste", "content", "get"]):
            return clipboard_read()
        if "copy" in q:
            text = q.replace("copy", "").replace("to clipboard", "").strip()
            return clipboard_copy(text)

    # ── Laptop Automation: Window Minimizing ───────
    if "minimize" in q and ("all" in q or "window" in q or "everything" in q) or "show desktop" in q:
        from modules.laptop_automation import show_desktop
        return show_desktop()

    # ── Laptop Automation: Switch Window ──────────
    if q.startswith("switch to") or q.startswith("focus on") or q.startswith("switch window to"):
        target_win = (q.replace("switch window to", "").replace("switch to", "")
                      .replace("focus on", "").strip())
        from modules.laptop_automation import switch_to_window
        return switch_to_window(target_win)

    # ── Laptop Automation: Typing on Screen ────────
    if q.startswith("type ") or q.startswith("write "):
        text_to_type = re.sub(r'^(?:type|write)\s+', '', q).strip()
        press_enter = "and press enter" in text_to_type or "and hit enter" in text_to_type
        text_to_type = (text_to_type.replace("and press enter", "")
                        .replace("and hit enter", "").strip().strip('"').strip("'"))
        from modules.laptop_automation import type_text
        return type_text(text_to_type, press_enter=press_enter)

    # ── Laptop Automation: Press Key or Hotkey ─────
    if q.startswith("press ") or q.startswith("hit "):
        key_name = re.sub(r'^(?:press|hit)\s+', '', q).strip()
        from modules.laptop_automation import press_keyboard_hotkey
        return press_keyboard_hotkey(key_name)

    # ── Laptop Automation: Scrolling ──────────────
    if "scroll down" in q or "scroll up" in q or "scroll page" in q:
        direction = "up" if "up" in q else "down"
        from modules.laptop_automation import scroll_page
        return scroll_page(direction)

    # ── Laptop Automation: YouTube Search & Play ──
    if "play" in q and "youtube" in q:
        song = (q.replace("play", "").replace("on youtube", "")
                .replace("in youtube", "").replace("youtube", "").strip())
        from modules.laptop_automation import play_youtube_video
        return play_youtube_video(song)

    # ── Close Commands (Tabs, Websites, Apps) ─────
    # Examples: "close the opened youtube from chrome", "close youtube", "close camera", "close tab"
    if any(p in q for p in ["close", "kill", "terminate", "exit"]):
        return close_target(q)

    # ── Open Applications & Websites ──────────────
    # Examples: "open camera", "open calender", "open youtube", "open calculator"
    if any(q.startswith(w) for w in ["open ", "launch ", "start ", "go to "]):
        target = re.sub(r'^(?:open|launch|start|go to)\s+(?:the\s+)?', '', q).strip()
        if target:
            return open_target(target)

    # Mid-sentence open: "please open camera"
    for verb in [" open ", " launch ", " start ", " go to "]:
        if verb in q:
            target = q.split(verb, 1)[1].strip()
            target = re.sub(r'^(?:the\s+)', '', target).strip()
            if target:
                return open_target(target)

    # ── Explicit Web Search ───────────────────────
    if q.startswith("search for") or q.startswith("search ") or q.startswith("google "):
        search_term = re.sub(r'^(?:search for|search|google)\s+', '', q).strip()
        if search_term:
            return search_google(search_term)

    # ── Conversational Greetings ──────────────────
    if any(p in q for p in ["hello", "hi jarvis", "hey jarvis", "good morning", "good evening", "good afternoon"]):
        return f"Hello {USER_NAME}! All systems are online and ready to assist."

    if "thank" in q:
        return f"Always at your service, {USER_NAME}."

    if "how are you" in q:
        return f"All diagnostics report normal, {USER_NAME}. Standing by for commands."

    if "your name" in q:
        from config import ASSISTANT_NAME
        return f"I am {ASSISTANT_NAME}, your personal AI assistant."

    if "reset" in q and "conversation" in q:
        if ai_brain:
            ai_brain.reset_conversation()
        return "Conversation memory cleared."

    # ── AI Fallback ────────────────────────────────
    if ai_brain:
        return ai_brain.chat(query)

    return f"I'm not sure how to assist with that, {USER_NAME}."
