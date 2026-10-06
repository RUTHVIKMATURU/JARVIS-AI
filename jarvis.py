"""
jarvis.py  ─  Main entry point for JARVIS AI
═══════════════════════════════════════════════
J.A.R.V.I.S — Just A Rather Very Intelligent System
A voice-controlled AI assistant for Windows, powered by Google Gemini.

Usage:
    python jarvis.py

Requirements:
    - Python 3.10+
    - Google Gemini API key in config.py
    - Microphone connected

Commands (speak or type):
    "Jarvis [command]"       — Wake word + any command
    "open [app/site]"        — Launch apps or websites
    "what time is it"        — Get current time/date
    "system info"            — CPU, RAM, battery status
    "take a screenshot"      — Screenshot saved to Screenshots/
    "set volume to 50"       — Control system volume
    "search for [query]"     — Google search
    "what's the weather"     — Current weather
    "run command [cmd]"      — Run PowerShell commands
    "shutdown / restart"     — Power controls
    "jarvis quit"            — Exit JARVIS
    ... or just talk!        — AI-powered general conversation
"""

import sys
import os
import threading
import datetime
import time

# ─── Bootstrap ───────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ASSISTANT_NAME, USER_NAME, WAKE_WORD
from modules.voice import init_tts, say, listen_once, listen_for_wake_word, stop_tts
from modules.ai_brain import JarvisBrain
from modules.commands import parse_and_execute, set_reminder_callback, add_reminder

# GUI import (optional — will gracefully degrade)
try:
    from modules.gui import JarvisGUI
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"[JARVIS] GUI unavailable: {e}")
    GUI_AVAILABLE = False


class JarvisAssistant:
    """
    Core orchestrator for JARVIS.
    Manages the GUI, wake word detection, voice listening,
    command parsing, and AI responses.
    """

    def __init__(self):
        self.brain = JarvisBrain()
        self.gui: JarvisGUI | None = None
        self.wake_stop_event = threading.Event()
        self.wake_thread: threading.Thread | None = None
        self.is_listening = False
        self.wake_enabled = True

        # Wire reminder notifications to GUI popup
        set_reminder_callback(self._on_reminder)

    # ─── Core: Handle a command string ───────────────────────────────────────
    def handle_command(self, query: str):
        """Process a command (from voice or text input)."""
        if not query or not query.strip():
            return

        print(f"\n[Input] {query}")
        if self.gui:
            self.gui.set_processing(True)

        # Check for quit
        if any(p in query.lower() for p in ["jarvis quit", "jarvis exit", "goodbye jarvis", "shut down jarvis"]):
            response = f"Goodbye, {USER_NAME}. It has been a pleasure."
            self._respond(response)
            time.sleep(1.5)
            self._shutdown()
            return

        # Check for reminder with time parsing
        if any(p in query.lower() for p in ["remind me", "set a reminder", "set reminder"]):
            response = self._handle_reminder_voice(query)
            self._respond(response)
            return

        # Dispatch command
        response = parse_and_execute(query, ai_brain=self.brain)
        self._respond(response)

    def _respond(self, response: str):
        """Output a response via speech and GUI."""
        if self.gui:
            self.gui.set_processing(False)
            self.gui.add_jarvis_message(response)
        say(response)

    def _handle_reminder_voice(self, query: str) -> str:
        """Parse a natural-language reminder request."""
        import re
        # Extract time pattern HH:MM
        time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', query)
        if not time_match:
            # Try "at X o'clock" or "in X minutes"
            hour_match = re.search(r'at (\d{1,2})\s*(?:o\'clock|am|pm)?', query.lower())
            minute_match = re.search(r'in (\d+)\s*minute', query.lower())
            if minute_match:
                minutes = int(minute_match.group(1))
                remind_dt = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            elif hour_match:
                hour = int(hour_match.group(1))
                if "pm" in query.lower() and hour < 12:
                    hour += 12
                remind_dt = datetime.datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
            else:
                return "I couldn't parse a time for your reminder. Please specify a time like 'at 3:30 PM' or 'in 10 minutes'."
        else:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            remind_dt = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if remind_dt < datetime.datetime.now():
                remind_dt += datetime.timedelta(days=1)

        # Extract message
        msg = (query.lower()
               .replace("remind me to", "").replace("remind me", "")
               .replace("set a reminder to", "").replace("set reminder to", "")
               .replace("set a reminder", "").replace("set reminder", "")
               .strip())
        # Remove time references
        msg = re.sub(r'at \d{1,2}(:\d{2})?\s*(am|pm|o\'clock)?', '', msg, flags=re.IGNORECASE).strip()
        msg = re.sub(r'in \d+ minutes?', '', msg, flags=re.IGNORECASE).strip()
        msg = msg.strip(" ,.")

        if not msg:
            msg = "Scheduled reminder"

        return add_reminder(msg, remind_dt)

    # ─── Voice Listening ─────────────────────────────────────────────────────
    def start_listening_once(self, triggered_by_wake: bool = False):
        """Listen for a single voice command."""
        if self.is_listening:
            return
        self.is_listening = True

        if self.gui:
            self.gui.set_listening(True)
        say("Yes?" if triggered_by_wake else "Listening.")

        def listen_thread():
            query = listen_once(timeout=6, phrase_time_limit=12)
            self.is_listening = False
            if self.gui:
                self.gui.set_listening(False)
            if query:
                print(f"[Voice] Heard: {query}")
                # Strip the wake word from the beginning if present
                clean = query.lower()
                for wake in [WAKE_WORD.lower() + " ", WAKE_WORD.lower()]:
                    if clean.startswith(wake):
                        query = query[len(wake):].strip()
                        break
                if query:
                    if self.gui:
                        self.gui.add_user_message(query)
                    self.handle_command(query)
            else:
                if triggered_by_wake:
                    say("I didn't catch that. Please try again.")

        threading.Thread(target=listen_thread, daemon=True).start()

    def _on_wake_word(self):
        """Called when the wake word is detected."""
        print(f"[JARVIS] Wake word detected!")
        self.start_listening_once(triggered_by_wake=True)

    # ─── Wake Word Thread ────────────────────────────────────────────────────
    def start_wake_word_listener(self):
        """Start the background wake word detection thread."""
        self.wake_stop_event.clear()
        self.wake_thread = threading.Thread(
            target=listen_for_wake_word,
            args=(self._on_wake_word, self.wake_stop_event),
            daemon=True
        )
        self.wake_thread.start()
        print(f"[JARVIS] Wake word listener started. Say '{WAKE_WORD}' to activate.")

    def stop_wake_word_listener(self):
        """Stop the background wake word detection."""
        self.wake_stop_event.set()

    # ─── GUI Callbacks ───────────────────────────────────────────────────────
    def _on_voice_toggle(self, should_listen: bool):
        """Called when the user clicks the mic button."""
        if should_listen:
            self.start_listening_once()
        else:
            self.is_listening = False
            if self.gui:
                self.gui.set_listening(False)

    def _on_wake_toggle(self, enabled: bool):
        """Called when wake word toggle is clicked."""
        self.wake_enabled = enabled
        if enabled:
            self.start_wake_word_listener()
        else:
            self.stop_wake_word_listener()
        print(f"[JARVIS] Wake word {'enabled' if enabled else 'disabled'}.")

    def _on_reminder(self, message: str):
        """Called when a reminder fires."""
        say(message)
        if self.gui:
            self.gui.show_notification(message, title="Reminder")
            self.gui.add_system_message(f"⏰ {message}")

    # ─── Shutdown ────────────────────────────────────────────────────────────
    def _shutdown(self):
        """Gracefully shut down JARVIS."""
        print("[JARVIS] Shutting down...")
        self.stop_wake_word_listener()
        stop_tts()
        if self.gui:
            self.gui.root.quit()

    # ─── Run ─────────────────────────────────────────────────────────────────
    def run(self):
        """Main run loop — starts the GUI and background services."""
        print("""
+======================================================+
|         J.A.R.V.I.S  AI  ASSISTANT  v2.0            |
|        Powered by Google Gemini  -  Voice + GUI      |
+======================================================+
""")
        # Initialise TTS
        init_tts()
        time.sleep(0.3)  # Let TTS worker start

        # Startup greeting
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        startup_msg = f"{greeting}, {USER_NAME}. {ASSISTANT_NAME} is online and fully operational."
        say(startup_msg)

        if GUI_AVAILABLE:
            # Create GUI
            self.gui = JarvisGUI(
                on_command_callback=self.handle_command,
                on_voice_toggle_callback=self._on_voice_toggle,
                on_wake_toggle_callback=self._on_wake_toggle,
            )

            # Wire AI status to GUI
            if not self.brain.is_ready():
                self.gui.add_system_message("⚠️  No Gemini API key configured. Add key to config.py for full AI features.")
            else:
                self.gui.add_system_message("✅  Gemini AI connected.")

            # Start wake word listener in background
            self.start_wake_word_listener()

            # Start GUI (blocks until window closed)
            self.gui.run()
        else:
            # Fallback: terminal mode
            print("\n[JARVIS] Running in terminal mode (no GUI).")
            print("Type your commands below. Type 'jarvis quit' to exit.\n")
            self.start_wake_word_listener()
            while True:
                try:
                    query = input("You: ").strip()
                    if query:
                        self.handle_command(query)
                except KeyboardInterrupt:
                    print("\n[JARVIS] Interrupted by user.")
                    break
                except EOFError:
                    break

        # Cleanup
        self.stop_wake_word_listener()
        stop_tts()
        print("[JARVIS] Session ended.")


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    assistant = JarvisAssistant()
    assistant.run()
