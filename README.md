# J.A.R.V.I.S — Autonomous Laptop AI Assistant

> **Just A Rather Very Intelligent System**
> A real Iron Man-inspired AI assistant for Windows — voice-controlled, equipped with 30 laptop automation tools and Google Gemini AI.

---

## ✨ Autonomous Laptop Automation Capabilities

JARVIS can perform virtually any task you would normally do manually on your laptop:

### 1. 🖱️ Keyboard & Mouse Automation
- **Typing on screen**: *"Jarvis, type 'Hello from the other side' and press enter"*
- **Hotkeys**: *"Jarvis, press ctrl+s"*, *"Jarvis, press alt+tab"*, *"Jarvis, press enter"*, *"Jarvis, hit space"*
- **Scrolling**: *"Jarvis, scroll down"*, *"Jarvis, scroll up"*
- **Window Management**: *"Jarvis, minimize all windows"*, *"Jarvis, switch to Chrome"*, *"Jarvis, focus on Notepad"*

### 2. 📱 Apps & Web Browsing
- **Open Any Windows App**: Camera, Calendar, Calculator, Notepad, Chrome, VS Code, Spotify, Settings, Task Manager, Paint, Clock, Photos, etc.
- **Close Apps & Specific Tabs**:
  - *"Jarvis, close the opened youtube from chrome"* (closes the tab using `Ctrl+W` without killing your browser!)
  - *"Jarvis, close camera"*, *"Jarvis, close calculator"*, *"Jarvis, close tab"*
- **Direct YouTube Playback**: *"Jarvis, play lo-fi beats on YouTube"* (finds and auto-plays the video directly!)
- **Web Search**: *"Jarvis, search Google for Python tutorials"*

### 3. 📂 File & Folder Operations
- **Create Files with Content**: *"Jarvis, create a file on my desktop called notes.txt with text 'Meeting at 3 PM'"*
- **Read Files Aloud**: *"Jarvis, read the file notes.txt on my desktop"*
- **Delete Files**: *"Jarvis, delete the file old_report.pdf on my desktop"*
- **Create Folders**: *"Jarvis, make a folder called Project Alpha on my desktop"*
- **Browse Folders**: *"Jarvis, open downloads folder"*, *"Jarvis, open desktop"*
- **List & Search**: *"Jarvis, list files in my downloads"*, *"Jarvis, find file resume.docx"*
- **Recycle Bin**: *"Jarvis, empty the recycle bin"*

### 4. 🔊 Hardware & System Control
- **Volume**: *"Jarvis, set volume to 70"*, *"Jarvis, mute volume"*, *"Jarvis, unmute"*
- **Brightness**: *"Jarvis, set brightness to 80"*
- **Laptop Diagnostics**: *"Jarvis, system info"* (reports real-time CPU, RAM, disk, and battery)
- **Wi-Fi**: *"Jarvis, show available Wi-Fi networks"*
- **Clipboard**: *"Jarvis, what is in my clipboard?"*, *"Jarvis, copy 'Iron Man' to clipboard"*
- **Screenshots**: *"Jarvis, take a screenshot"* (saved automatically to `Screenshots/`)
- **Power Controls**: *"Jarvis, lock the screen"*, *"Jarvis, put the laptop to sleep"*, *"Jarvis, restart the computer"*
- **Terminal Execution**: *"Jarvis, run powershell command ipconfig"*

---

## 🚀 Quick Start

### 1. Launch JARVIS (Double Click)
```bash
START_JARVIS.bat
```
Or from terminal:
```powershell
$env:PYTHONIOENCODING="utf-8"; python jarvis.py
```

### 2. Configuration
Open `config.py` to customize:
- `GEMINI_API_KEY`: Your Gemini API key
- `WAKE_WORD`: "jarvis"
- `USER_NAME`: "Sir"
- `VOICE_RATE`: Speech speed (default 175)

---

## 🗣️ Try These Commands

Just say **"Jarvis"** or click the mic button:

```
"Jarvis, open camera"
"Jarvis, open calender"
"Jarvis, play lo-fi beats on youtube"
"Jarvis, close the opened youtube from chrome"
"Jarvis, empty the recycle bin"
"Jarvis, show available wifi networks"
"Jarvis, minimize all windows"
"Jarvis, what's in my clipboard?"
"Jarvis, create a file on desktop called todo.txt with text '1. Learn AI 2. Build robots'"
"Jarvis, type 'Meeting in 10 minutes' and press enter"
"Jarvis, scroll down"
"Jarvis, set volume to 60"
"Jarvis, what is the battery level?"
"Jarvis, take a screenshot"
```

---

## 📁 Project Architecture

```
JARVIS-AI/
├── jarvis.py                  ← Main entry point & orchestrator
├── START_JARVIS.bat           ← One-click UTF-8 launcher
├── config.py                  ← Configuration & keys
├── requirements.txt           ← Dependencies
└── modules/
    ├── laptop_automation.py   ← 30 Direct Windows OS automation tools
    ├── ai_brain.py            ← Gemini 2.5 AI with Automatic Tool Calling
    ├── commands.py            ← High-speed local command dispatcher
    ├── gui.py                 ← Dark Iron Man Arc-Reactor GUI
    └── voice.py               ← Wake word, speech recognition & TTS
```