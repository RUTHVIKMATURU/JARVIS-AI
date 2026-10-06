"""
modules/ai_brain.py
────────────────────
Google Gemini-powered AI brain for JARVIS with Autonomous Laptop Tool Execution.
Uses the new google-genai SDK (google.genai).
Equipped with 30 laptop automation tools for direct OS control, file management,
GUI manipulation, shell commands, and multi-turn conversational intelligence.
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GEMINI_API_KEY, ASSISTANT_NAME, USER_NAME, CONVERSATION_MEMORY
from modules.laptop_automation import LAPTOP_TOOLS

# Try new SDK first, fall back to legacy
GEMINI_AVAILABLE = False
USE_NEW_SDK = False

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
    USE_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
        GEMINI_AVAILABLE = True
        USE_NEW_SDK = False
    except ImportError:
        print("[AI Brain] No Gemini SDK found. AI responses disabled.")


# ─── System Persona & Operational Instructions ───────────────────────────────
JARVIS_PERSONA = f"""You are {ASSISTANT_NAME}, an autonomous AI assistant modeled after Iron Man's JARVIS.
You have direct, full control over the user's Windows laptop via your registered laptop automation tools.

Your Personality:
- Highly intelligent, precise, and proactive
- Formal yet warm — address the user as "{USER_NAME}"
- Decisive and action-oriented
- Speak concisely in spoken-friendly English (1 to 2 sentences)
- Never output markdown formatting, asterisks, bullet points, or code blocks because your responses are read aloud via text-to-speech

CRITICAL OPERATIONAL RULES:
1. When {USER_NAME} asks you to perform ANY task on the laptop (such as opening apps, closing tabs, typing text, pressing keys, creating/reading/deleting files, controlling volume/brightness, taking screenshots, playing YouTube, checking Wi-Fi, emptying recycle bin, or running PowerShell), you MUST ALWAYS invoke the corresponding tool.
2. NEVER simply claim you did something without actually calling the tool.
3. If {USER_NAME} asks for an advanced system task not covered by a specific tool, use the 'execute_powershell' tool to accomplish it.
4. After executing the tool, confirm the action in a single, crisp, elegant sentence in the JARVIS style."""


class JarvisBrain:
    """Manages AI conversation and autonomous tool execution with Google Gemini."""

    def __init__(self):
        self.client = None
        self.chat_session = None
        self.conversation_history = []
        self._init_gemini()

    def _init_gemini(self):
        """Initialize the Gemini client and chat session with laptop tools."""
        if not GEMINI_AVAILABLE:
            return
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            print("[AI Brain] WARNING: No Gemini API key set. Edit config.py to add your free key.")
            print("[AI Brain]    Get your key at: https://aistudio.google.com/app/apikey")
            return

        try:
            if USE_NEW_SDK:
                self._init_new_sdk()
            else:
                self._init_legacy_sdk()
            print("[AI Brain] OK: Gemini AI initialized with 30 laptop automation tools.")
        except Exception as e:
            print(f"[AI Brain] ERROR: Failed to initialize Gemini: {e}")
            self.client = None
            self.chat_session = None

    def _init_new_sdk(self):
        """Initialize using the new google-genai SDK with Automatic Function Calling."""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.models_pool = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-2.5-pro"]
        self.current_model_idx = 0
        self.current_model = self.models_pool[0]
        self.chat_session = self._create_session_for_model(self.current_model)

    def _create_session_for_model(self, model_name: str):
        """Create a chat session equipped with all 30 laptop automation tools."""
        return self.client.chats.create(
            model=model_name,
            config=genai_types.GenerateContentConfig(
                system_instruction=JARVIS_PERSONA,
                temperature=0.3,
                max_output_tokens=350,
                tools=LAPTOP_TOOLS,
            )
        )

    def _init_legacy_sdk(self):
        """Fallback initialization using legacy SDK."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            genai_legacy.configure(api_key=GEMINI_API_KEY)
            model = genai_legacy.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=JARVIS_PERSONA,
                generation_config=genai_legacy.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=300,
                )
            )
            self.client = model
            self.chat_session = model.start_chat(history=[])

    def chat(self, user_message: str) -> str:
        """
        Sends user message to Gemini, automatically executes any needed laptop tools,
        and returns the natural spoken response.
        Fails over across models if quota limits are encountered.
        """
        if not self.chat_session and not USE_NEW_SDK:
            return self._fallback_response(user_message)

        if USE_NEW_SDK:
            # Try across model pool if rate limits are hit
            for idx in range(len(self.models_pool)):
                model_name = self.models_pool[(self.current_model_idx + idx) % len(self.models_pool)]
                try:
                    if not self.chat_session or self.current_model != model_name:
                        self.chat_session = self._create_session_for_model(model_name)
                        self.current_model = model_name

                    response = self.chat_session.send_message(user_message)
                    raw_text = response.text or ""
                    reply = self._clean_for_speech(raw_text.strip())

                    if not reply:
                        reply = f"Task completed, {USER_NAME}."

                    # Keep rolling conversation history
                    self.conversation_history.append(("user", user_message))
                    self.conversation_history.append(("assistant", reply))
                    if len(self.conversation_history) > CONVERSATION_MEMORY * 2:
                        self.conversation_history = self.conversation_history[-(CONVERSATION_MEMORY * 2):]

                    return reply

                except Exception as e:
                    err_str = str(e)
                    print(f"[AI Brain] Notice on {model_name}: {err_str[:140]}")
                    if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND"]):
                        # Try next model in pool
                        continue
                    break

            return f"I encountered a temporary cognitive issue, {USER_NAME}. Please try again shortly."

        # Legacy fallback
        try:
            response = self.chat_session.send_message(user_message)
            return self._clean_for_speech(response.text.strip())
        except Exception as e:
            return f"Error executing task: {str(e)}"

    def _clean_for_speech(self, text: str) -> str:
        """Strip markdown asterisks, backticks, and formatting for clean text-to-speech."""
        if not text:
            return ""
        # Remove bold/italic asterisks
        cleaned = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        # Remove code blocks / backticks
        cleaned = re.sub(r'`+(.*?)`+', r'\1', cleaned)
        # Remove markdown headers and bullets
        cleaned = re.sub(r'^[#*\-•]\s+', '', cleaned, flags=re.MULTILINE)
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _fallback_response(self, query: str) -> str:
        """Rule-based fallback when Gemini is not connected."""
        query_lower = query.lower()
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if any(g in query_lower for g in greetings):
            return f"Hello {USER_NAME}! How can I assist you with your laptop today?"
        if "how are you" in query_lower:
            return f"All systems are fully functional, {USER_NAME}."
        if "your name" in query_lower:
            return f"I am {ASSISTANT_NAME}, your personal AI assistant."
        if "thank" in query_lower:
            return f"Always a pleasure, {USER_NAME}."
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            return (f"My AI core is not yet configured, {USER_NAME}. "
                    f"Please verify your Gemini API key in config.py.")
        return f"I understand, {USER_NAME}. However, my AI core appears offline at the moment."

    def is_ready(self) -> bool:
        """Check if AI is initialized and ready."""
        return self.chat_session is not None

    def reset_conversation(self):
        """Start a fresh conversation session."""
        self.conversation_history = []
        self._init_gemini()
