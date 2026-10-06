"""
modules/gui.py
───────────────
JARVIS Desktop GUI — Dark-themed, futuristic Iron Man-inspired interface.
Built with CustomTkinter for a modern look.
"""

import sys
import os
import threading
import datetime
import tkinter as tk
from tkinter import scrolledtext, ttk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import math
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ASSISTANT_NAME, USER_NAME

# ─── Theme ───────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colour palette
C_BG        = "#0a0e1a"       # Deep navy background
C_PANEL     = "#0d1527"       # Panel background
C_PANEL2    = "#101c35"       # Secondary panel
C_ACCENT    = "#00b4d8"       # Cyan accent (JARVIS blue)
C_ACCENT2   = "#0077b6"       # Darker accent
C_GLOW      = "#00e5ff"       # Glow colour
C_TEXT      = "#caf0f8"       # Light cyan text
C_TEXT_DIM  = "#4a7a8a"       # Dimmed text
C_USER      = "#00b4d8"       # User message colour
C_JARVIS    = "#00e5ff"       # JARVIS message colour
C_SUCCESS   = "#06d6a0"       # Green success
C_WARNING   = "#ffb703"       # Amber warning
C_ERROR     = "#ef233c"       # Red error
C_BORDER    = "#1a3050"       # Panel borders


class PulseCanvas(tk.Canvas):
    """Animated pulsing arc — the JARVIS 'arc reactor' effect."""

    def __init__(self, master, size=120, **kwargs):
        super().__init__(master, width=size, height=size,
                         bg=C_BG, highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        self.active = False
        self._arcs = []
        self._draw()

    def _draw(self):
        self.delete("all")
        cx, cy, s = self.cx, self.cy, self.size

        # Outer ring
        r_outer = s // 2 - 5
        self.create_oval(cx - r_outer, cy - r_outer,
                         cx + r_outer, cy + r_outer,
                         outline=C_ACCENT2, width=1)

        # Middle ring with glow segments
        r_mid = s // 2 - 18
        for i in range(8):
            start = i * 45 + self.angle
            extent = 30
            alpha_factor = 0.4 + 0.6 * abs(math.sin(math.radians(self.angle + i * 45)))
            colour = C_GLOW if self.active else C_ACCENT
            self.create_arc(cx - r_mid, cy - r_mid,
                            cx + r_mid, cy + r_mid,
                            start=start, extent=extent,
                            style="arc", outline=colour, width=2)

        # Inner spinning arc
        r_inner = s // 2 - 30
        self.create_arc(cx - r_inner, cy - r_inner,
                        cx + r_inner, cy + r_inner,
                        start=self.angle * 2, extent=220,
                        style="arc", outline=C_ACCENT, width=2)

        # Centre dot
        pulse_r = 8 + self.pulse * 3
        colour = C_GLOW if self.active else C_ACCENT2
        self.create_oval(cx - pulse_r, cy - pulse_r,
                         cx + pulse_r, cy + pulse_r,
                         fill=colour, outline="")
        self.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                         fill="#ffffff", outline="")

        # Status text
        status = "ACTIVE" if self.active else "STANDBY"
        self.create_text(cx, s - 8, text=status,
                         fill=C_GLOW if self.active else C_TEXT_DIM,
                         font=("Consolas", 7, "bold"))

        # Schedule next frame
        self.after(30, self._animate)

    def _animate(self):
        self.angle = (self.angle + 2) % 360
        self.pulse += 0.1 * self.pulse_dir
        if self.pulse >= 1.0:
            self.pulse_dir = -1
        elif self.pulse <= 0.0:
            self.pulse_dir = 1
        self._draw()

    def set_active(self, active: bool):
        self.active = active


class JarvisGUI:
    """Main JARVIS desktop application window."""

    def __init__(self, on_command_callback, on_voice_toggle_callback, on_wake_toggle_callback):
        """
        Args:
            on_command_callback: called with (query_str) when user sends a command
            on_voice_toggle_callback: called with (bool) when mic button toggled
            on_wake_toggle_callback: called with (bool) when wake word toggled
        """
        self.on_command = on_command_callback
        self.on_voice_toggle = on_voice_toggle_callback
        self.on_wake_toggle = on_wake_toggle_callback
        self.listening = False
        self.wake_enabled = True

        # Root window
        self.root = ctk.CTk()
        self.root.title(f"{ASSISTANT_NAME} — Personal AI Assistant")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(fg_color=C_BG)

        # Try to set icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "jarvis_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self._build_ui()
        self._start_clock()

    # ─── UI Building ────────────────────────────────────────────────────────
    def _build_ui(self):
        """Construct the main UI layout."""
        # Header bar
        self._build_header()

        # Main content area (left sidebar + chat + right panel)
        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Left sidebar
        self._build_sidebar(content)

        # Chat panel (centre)
        self._build_chat_panel(content)

        # Right panel
        self._build_right_panel(content)

    def _build_header(self):
        header = ctk.CTkFrame(self.root, fg_color=C_PANEL, height=70, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Left: JARVIS name + status
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(left, text=f"⬡  {ASSISTANT_NAME.upper()}",
                     font=ctk.CTkFont("Consolas", 22, "bold"),
                     text_color=C_GLOW).pack(side="left", padx=(0, 15))

        self.status_label = ctk.CTkLabel(left,
                                          text="● STANDBY",
                                          font=ctk.CTkFont("Consolas", 11),
                                          text_color=C_TEXT_DIM)
        self.status_label.pack(side="left")

        # Right: clock
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=20)

        self.clock_label = ctk.CTkLabel(right, text="",
                                         font=ctk.CTkFont("Consolas", 20, "bold"),
                                         text_color=C_ACCENT)
        self.clock_label.pack()
        self.date_label = ctk.CTkLabel(right, text="",
                                        font=ctk.CTkFont("Consolas", 10),
                                        text_color=C_TEXT_DIM)
        self.date_label.pack()

        # Separator
        sep = ctk.CTkFrame(self.root, height=2, fg_color=C_BORDER)
        sep.pack(fill="x")

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=220, fg_color=C_PANEL,
                                corner_radius=12)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        sidebar.grid_propagate(False)

        # Arc reactor animation
        arc_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        arc_frame.pack(pady=20)
        self.pulse_canvas = PulseCanvas(arc_frame, size=120)
        self.pulse_canvas.pack()

        # Listening indicator
        self.listen_indicator = ctk.CTkLabel(sidebar, text="",
                                              font=ctk.CTkFont("Consolas", 10),
                                              text_color=C_TEXT_DIM)
        self.listen_indicator.pack(pady=(0, 10))

        # Quick Action Buttons
        ctk.CTkLabel(sidebar, text="QUICK ACTIONS",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color=C_TEXT_DIM).pack(pady=(10, 5))

        actions = [
            ("🎤  Mic On/Off", self._toggle_mic),
            ("🔊  Wake Word", self._toggle_wake),
            ("📸  Screenshot", lambda: self._send_command("take a screenshot")),
            ("🔇  Mute Volume", lambda: self._send_command("mute volume")),
            ("💻  System Info", lambda: self._send_command("system info")),
            ("🌤️  Weather", lambda: self._send_command("what's the weather")),
            ("⏰  What Time", lambda: self._send_command("what time is it")),
            ("🗑️  Clear Chat", self._clear_chat),
        ]

        for label, cmd in actions:
            btn = ctk.CTkButton(sidebar, text=label, command=cmd,
                                height=34, corner_radius=8,
                                fg_color=C_PANEL2, hover_color=C_ACCENT2,
                                text_color=C_TEXT, border_color=C_BORDER,
                                border_width=1,
                                font=ctk.CTkFont("Consolas", 11),
                                anchor="w")
            btn.pack(fill="x", padx=12, pady=2)

        # Bottom: version
        ctk.CTkLabel(sidebar, text=f"{ASSISTANT_NAME} v2.0  •  AI Powered",
                     font=ctk.CTkFont("Consolas", 8),
                     text_color=C_TEXT_DIM).pack(side="bottom", pady=10)

    def _build_chat_panel(self, parent):
        chat_frame = ctk.CTkFrame(parent, fg_color=C_PANEL, corner_radius=12)
        chat_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=0)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        # Chat header
        chat_header = ctk.CTkFrame(chat_frame, fg_color=C_PANEL2, corner_radius=8, height=36)
        chat_header.pack(fill="x", padx=10, pady=(10, 0))
        chat_header.pack_propagate(False)
        ctk.CTkLabel(chat_header, text="◈  CONVERSATION LOG",
                     font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=C_ACCENT).pack(side="left", padx=12, pady=8)

        # Chat display
        self.chat_display = tk.Text(
            chat_frame,
            bg=C_BG, fg=C_TEXT, wrap="word",
            font=("Consolas", 12), bd=0, padx=16, pady=12,
            state="disabled", cursor="arrow",
            relief="flat", insertbackground=C_ACCENT,
            selectbackground=C_ACCENT2
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        # Text tags for styling
        self.chat_display.tag_configure("user",   foreground=C_USER,   font=("Consolas", 12, "bold"))
        self.chat_display.tag_configure("jarvis", foreground=C_JARVIS, font=("Consolas", 12))
        self.chat_display.tag_configure("system", foreground=C_TEXT_DIM, font=("Consolas", 10, "italic"))
        self.chat_display.tag_configure("time",   foreground=C_TEXT_DIM, font=("Consolas", 9))
        self.chat_display.tag_configure("success",foreground=C_SUCCESS, font=("Consolas", 12))
        self.chat_display.tag_configure("error",  foreground=C_ERROR,   font=("Consolas", 12))

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(chat_frame, command=self.chat_display.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=8)
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        # Input area
        self._build_input_area(chat_frame)

    def _build_input_area(self, parent):
        input_frame = ctk.CTkFrame(parent, fg_color=C_PANEL2, corner_radius=10, height=56)
        input_frame.pack(fill="x", padx=10, pady=10)
        input_frame.pack_propagate(False)

        # Mic button
        self.mic_btn = ctk.CTkButton(input_frame, text="🎤", width=44, height=40,
                                      corner_radius=8, fg_color=C_ACCENT2,
                                      hover_color=C_GLOW,
                                      font=ctk.CTkFont(size=18),
                                      command=self._toggle_mic)
        self.mic_btn.pack(side="left", padx=(8, 4), pady=8)

        # Text input
        self.input_entry = ctk.CTkEntry(input_frame,
                                         placeholder_text=f"Type a command or say '{ASSISTANT_NAME}'...",
                                         font=ctk.CTkFont("Consolas", 12),
                                         fg_color=C_BG, border_color=C_BORDER,
                                         text_color=C_TEXT, border_width=1,
                                         corner_radius=8)
        self.input_entry.pack(side="left", fill="both", expand=True, padx=4, pady=8)
        self.input_entry.bind("<Return>", self._on_enter)

        # Send button
        send_btn = ctk.CTkButton(input_frame, text="➤ SEND", width=90, height=40,
                                  corner_radius=8, fg_color=C_ACCENT2,
                                  hover_color=C_ACCENT,
                                  font=ctk.CTkFont("Consolas", 11, "bold"),
                                  text_color="#ffffff",
                                  command=self._on_send)
        send_btn.pack(side="right", padx=(4, 8), pady=8)

    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, width=220, fg_color=C_PANEL, corner_radius=12)
        right.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=0)
        right.grid_propagate(False)

        # ── Reminders section ───────────────────────────
        ctk.CTkLabel(right, text="◈  REMINDERS",
                     font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=C_ACCENT).pack(padx=12, pady=(15, 5), anchor="w")

        self.reminder_msg_entry = ctk.CTkEntry(right, placeholder_text="Reminder message...",
                                                font=ctk.CTkFont("Consolas", 10),
                                                fg_color=C_BG, border_color=C_BORDER,
                                                text_color=C_TEXT, border_width=1)
        self.reminder_msg_entry.pack(fill="x", padx=12, pady=3)

        self.reminder_time_entry = ctk.CTkEntry(right, placeholder_text="HH:MM (today)",
                                                 font=ctk.CTkFont("Consolas", 10),
                                                 fg_color=C_BG, border_color=C_BORDER,
                                                 text_color=C_TEXT, border_width=1)
        self.reminder_time_entry.pack(fill="x", padx=12, pady=3)

        ctk.CTkButton(right, text="+ Set Reminder", height=32,
                      corner_radius=8, fg_color=C_ACCENT2, hover_color=C_ACCENT,
                      font=ctk.CTkFont("Consolas", 10, "bold"),
                      command=self._set_reminder).pack(fill="x", padx=12, pady=3)

        # ── Email section ───────────────────────────────
        sep = ctk.CTkFrame(right, height=1, fg_color=C_BORDER)
        sep.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(right, text="◈  QUICK EMAIL",
                     font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=C_ACCENT).pack(padx=12, pady=(0, 5), anchor="w")

        self.email_to = ctk.CTkEntry(right, placeholder_text="To (email address)...",
                                      font=ctk.CTkFont("Consolas", 10),
                                      fg_color=C_BG, border_color=C_BORDER,
                                      text_color=C_TEXT, border_width=1)
        self.email_to.pack(fill="x", padx=12, pady=3)

        self.email_subject = ctk.CTkEntry(right, placeholder_text="Subject...",
                                           font=ctk.CTkFont("Consolas", 10),
                                           fg_color=C_BG, border_color=C_BORDER,
                                           text_color=C_TEXT, border_width=1)
        self.email_subject.pack(fill="x", padx=12, pady=3)

        self.email_body = ctk.CTkTextbox(right, height=80,
                                          font=ctk.CTkFont("Consolas", 10),
                                          fg_color=C_BG, border_color=C_BORDER,
                                          text_color=C_TEXT, border_width=1)
        self.email_body.pack(fill="x", padx=12, pady=3)
        self.email_body.insert("0.0", "Message...")

        ctk.CTkButton(right, text="✉ Send Email", height=32,
                      corner_radius=8, fg_color=C_ACCENT2, hover_color=C_ACCENT,
                      font=ctk.CTkFont("Consolas", 10, "bold"),
                      command=self._send_email_from_form).pack(fill="x", padx=12, pady=3)

        # ── Terminal section ────────────────────────────
        sep2 = ctk.CTkFrame(right, height=1, fg_color=C_BORDER)
        sep2.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(right, text="◈  TERMINAL",
                     font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=C_ACCENT).pack(padx=12, pady=(0, 5), anchor="w")

        self.terminal_entry = ctk.CTkEntry(right, placeholder_text="PowerShell command...",
                                            font=ctk.CTkFont("Consolas", 10),
                                            fg_color=C_BG, border_color=C_BORDER,
                                            text_color=C_TEXT, border_width=1)
        self.terminal_entry.pack(fill="x", padx=12, pady=3)
        self.terminal_entry.bind("<Return>", self._run_terminal)

        ctk.CTkButton(right, text="▶ Run Command", height=32,
                      corner_radius=8, fg_color=C_PANEL2, hover_color=C_ACCENT2,
                      font=ctk.CTkFont("Consolas", 10, "bold"),
                      border_color=C_BORDER, border_width=1,
                      command=self._run_terminal).pack(fill="x", padx=12, pady=3)

    # ─── Clock ──────────────────────────────────────────────────────────────
    def _start_clock(self):
        def update():
            now = datetime.datetime.now()
            self.clock_label.configure(text=now.strftime("%I:%M:%S %p"))
            self.date_label.configure(text=now.strftime("%A, %B %d, %Y"))
            self.root.after(1000, update)
        update()

    # ─── Chat Helpers ────────────────────────────────────────────────────────
    def add_message(self, sender: str, message: str, tag: str = None):
        """Add a message to the chat display."""
        self.chat_display.configure(state="normal")
        now = datetime.datetime.now().strftime("%H:%M")

        if sender == "system":
            self.chat_display.insert("end", f"\n[{now}] {message}\n", "system")
        else:
            self.chat_display.insert("end", f"\n[{now}] {sender}:\n", "time")
            display_tag = tag or ("user" if sender == f"► {USER_NAME}" else "jarvis")
            self.chat_display.insert("end", f"  {message}\n", display_tag)

        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def add_user_message(self, message: str):
        self.add_message(f"► {USER_NAME}", message, "user")

    def add_jarvis_message(self, message: str):
        self.add_message(f"◈ {ASSISTANT_NAME}", message, "jarvis")

    def add_system_message(self, message: str):
        self.add_message("system", message)

    def _clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.add_system_message(f"{ASSISTANT_NAME} conversation cleared.")

    # ─── Status Updates ──────────────────────────────────────────────────────
    def set_status(self, status: str, colour: str = None):
        """Update the header status label."""
        colour = colour or C_TEXT_DIM
        self.root.after(0, lambda: self.status_label.configure(
            text=f"● {status.upper()}", text_color=colour))

    def set_listening(self, listening: bool):
        """Update UI for listening state."""
        self.listening = listening
        if listening:
            self.pulse_canvas.set_active(True)
            self.set_status("LISTENING", C_GLOW)
            self.root.after(0, lambda: self.mic_btn.configure(
                fg_color=C_ERROR, text="⏹"))
            self.root.after(0, lambda: self.listen_indicator.configure(
                text="🎤 Listening...", text_color=C_GLOW))
        else:
            self.pulse_canvas.set_active(False)
            self.set_status("STANDBY", C_TEXT_DIM)
            self.root.after(0, lambda: self.mic_btn.configure(
                fg_color=C_ACCENT2, text="🎤"))
            self.root.after(0, lambda: self.listen_indicator.configure(
                text="", text_color=C_TEXT_DIM))

    def set_processing(self, processing: bool):
        """Indicate JARVIS is thinking."""
        if processing:
            self.set_status("PROCESSING", C_WARNING)
            self.pulse_canvas.set_active(True)
        else:
            self.pulse_canvas.set_active(False)
            self.set_status("STANDBY", C_TEXT_DIM)

    def show_notification(self, message: str, title: str = "JARVIS"):
        """Show a popup notification for reminders etc."""
        def _show():
            popup = ctk.CTkToplevel(self.root)
            popup.title(title)
            popup.geometry("380x140")
            popup.configure(fg_color=C_PANEL)
            popup.attributes("-topmost", True)
            ctk.CTkLabel(popup, text=f"⏰  {title}",
                         font=ctk.CTkFont("Consolas", 14, "bold"),
                         text_color=C_WARNING).pack(pady=(15, 5))
            ctk.CTkLabel(popup, text=message,
                         font=ctk.CTkFont("Consolas", 12),
                         text_color=C_TEXT, wraplength=340).pack(pady=5)
            ctk.CTkButton(popup, text="Dismiss", command=popup.destroy,
                          fg_color=C_ACCENT2, hover_color=C_ACCENT,
                          font=ctk.CTkFont("Consolas", 11)).pack(pady=10)
        self.root.after(0, _show)

    # ─── Event Handlers ──────────────────────────────────────────────────────
    def _on_enter(self, event=None):
        self._on_send()

    def _on_send(self):
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, "end")
            self._send_command(text)

    def _send_command(self, command: str):
        self.add_user_message(command)
        threading.Thread(target=self.on_command, args=(command,), daemon=True).start()

    def _toggle_mic(self):
        self.on_voice_toggle(not self.listening)

    def _toggle_wake(self):
        self.wake_enabled = not self.wake_enabled
        self.on_wake_toggle(self.wake_enabled)
        status = "Wake word ENABLED" if self.wake_enabled else "Wake word DISABLED"
        self.add_system_message(status)

    def _set_reminder(self):
        msg = self.reminder_msg_entry.get().strip()
        time_str = self.reminder_time_entry.get().strip()
        if not msg or not time_str:
            self.add_system_message("Please enter both a message and time for the reminder.")
            return
        self._send_command(f"set reminder '{msg}' at {time_str}")
        self.reminder_msg_entry.delete(0, "end")
        self.reminder_time_entry.delete(0, "end")

    def _send_email_from_form(self):
        to = self.email_to.get().strip()
        subject = self.email_subject.get().strip()
        body = self.email_body.get("0.0", "end").strip()
        if not to or not subject:
            self.add_system_message("Please fill in the 'To' and 'Subject' fields.")
            return
        from modules.commands import send_email
        threading.Thread(
            target=lambda: self.add_jarvis_message(send_email(to, subject, body)),
            daemon=True
        ).start()

    def _run_terminal(self, event=None):
        cmd = self.terminal_entry.get().strip()
        if cmd:
            self.terminal_entry.delete(0, "end")
            self._send_command(f"run command {cmd}")

    # ─── Run ─────────────────────────────────────────────────────────────────
    def run(self):
        """Start the GUI event loop."""
        self.add_system_message(f"  {ASSISTANT_NAME} AI initialised. Say '{ASSISTANT_NAME}' or type below.")
        self.root.mainloop()
