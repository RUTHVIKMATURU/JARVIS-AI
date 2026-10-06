"""
modules/voice.py
─────────────────
Voice input (microphone + speech recognition) and
voice output (text-to-speech) for JARVIS.
"""

import threading
import queue
import speech_recognition as sr
import pyttsx3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WAKE_WORD, VOICE_RATE, VOICE_VOLUME, VOICE_GENDER


# ─── TTS Engine (singleton) ──────────────────────────────────────────────────
_tts_engine = None
_tts_lock = threading.Lock()
_speech_queue: queue.Queue = queue.Queue()
_tts_thread = None


def _tts_worker():
    """Background thread that processes TTS requests one at a time."""
    global _tts_engine
    _tts_engine = pyttsx3.init()
    voices = _tts_engine.getProperty('voices')
    if voices and VOICE_GENDER < len(voices):
        _tts_engine.setProperty('voice', voices[VOICE_GENDER].id)
    _tts_engine.setProperty('rate', VOICE_RATE)
    _tts_engine.setProperty('volume', VOICE_VOLUME)

    while True:
        text = _speech_queue.get()
        if text is None:  # Poison pill to stop the thread
            break
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception as e:
            print(f"[TTS Error] {e}")
        finally:
            _speech_queue.task_done()


def init_tts():
    """Start the TTS worker thread."""
    global _tts_thread
    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_thread = threading.Thread(target=_tts_worker, daemon=True)
        _tts_thread.start()


def say(text: str):
    """Queue text for speech output (non-blocking)."""
    print(f"[JARVIS] {text}")
    _speech_queue.put(text)


def stop_tts():
    """Stop the TTS worker thread gracefully."""
    _speech_queue.put(None)


# ─── Speech Recognition ──────────────────────────────────────────────────────
_recognizer = sr.Recognizer()
_recognizer.energy_threshold = 300
_recognizer.dynamic_energy_threshold = True
_recognizer.pause_threshold = 0.8


def listen_once(timeout: int = 5, phrase_time_limit: int = 10) -> str | None:
    """
    Listen to the microphone once and return recognized text.
    Returns None if nothing was understood.
    """
    try:
        with sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = _recognizer.recognize_google(audio)
        return text.strip()
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"[Voice Error] Google Speech API error: {e}")
        return None
    except Exception as e:
        print(f"[Voice Error] {e}")
        return None


def listen_for_wake_word(callback, stop_event: threading.Event):
    """
    Continuously listen for the wake word in a background thread.
    When the wake word is detected, calls callback().
    Uses phrase detection (no external wake word engine required).
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 250
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5

    print(f"[Wake Word] Listening for '{WAKE_WORD}'...")

    while not stop_event.is_set():
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                    text = recognizer.recognize_google(audio).lower()
                    if WAKE_WORD.lower() in text:
                        print(f"[Wake Word] Detected: '{text}'")
                        callback()
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    pass
        except Exception as e:
            if not stop_event.is_set():
                print(f"[Wake Word Error] {e}")
