"""
JARVIS Configuration Template
Copy or rename this file to config.py and insert your own API keys.
DO NOT commit your real config.py with actual keys to GitHub.
"""

# ─── AI API Keys ────────────────────────────────────────────────────────────
# Get your free Gemini API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Legacy OpenAI key (optional, kept for compatibility)
apikey = ""

# ─── Wake Word ──────────────────────────────────────────────────────────────
WAKE_WORD = "jarvis"

# ─── Voice Settings ─────────────────────────────────────────────────────────
# Voice rate (words per minute). Default: 175
VOICE_RATE = 175
# Voice volume (0.0 - 1.0). Default: 1.0
VOICE_VOLUME = 1.0
# Voice gender: 0 = male, 1 = female
VOICE_GENDER = 0

# ─── Assistant Identity ─────────────────────────────────────────────────────
ASSISTANT_NAME = "Jarvis"
USER_NAME = "Sir"

# ─── Email Settings (for send email feature) ────────────────────────────────
EMAIL_ADDRESS = ""        # Your Gmail address
EMAIL_PASSWORD = ""       # Your Gmail App Password (not regular password)

# ─── Reminder Check Interval (seconds) ─────────────────────────────────────
REMINDER_CHECK_INTERVAL = 30

# ─── Screenshot Save Directory ──────────────────────────────────────────────
SCREENSHOT_DIR = "Screenshots"

# ─── AI Response Memory (number of past exchanges to remember) ───────────────
CONVERSATION_MEMORY = 10
