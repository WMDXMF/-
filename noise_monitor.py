{\rtf1\ansi\ansicpg936\cocoartf2869
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import tkinter as tk\
from tkinter import font\
import pyaudio\
import numpy as np\
import pyttsx3\
import threading\
import time\
import math\
\
class NoiseMonitorApp:\
    def __init__(self, root):\
        self.root = root\
        self.root.title("\uc0\u35838 \u22530 \u38899 \u37327 \u30417 \u27979 \u31995 \u32479 ")\
        self.root.geometry("600x400")\
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)\
\
        # \uc0\u21021 \u22987 \u21270 \u21442 \u25968 \
        self.CHUNK = 1024\
        self.FORMAT = pyaudio.paInt16\
        self.CHANNELS = 1\
        self.RATE = 44100\
        self.is_running = True\
        self.is_warning = False # \uc0\u26159 \u21542 \u27491 \u22312 \u25253 \u35686 \u65288 \u38450 \u27490 \u37325 \u22797 \u35302 \u21457 \u65289 \
        self.history_vol = [0] * 100 # \uc0\u20445 \u23384 \u21382 \u21490 \u38899 \u37327 \u29992 \u20110 \u32472 \u21046 \u27874 \u24418 \
\
        # \uc0\u21021 \u22987 \u21270 \u35821 \u38899 \u24341 \u25806 \
        self.engine = pyttsx3.init()\
        # \uc0\u23581 \u35797 \u35774 \u32622 \u20013 \u25991 \u35821 \u38899 \
        voices = self.engine.getProperty('voices')\
        for voice in voices:\
            if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():\
                self.engine.setProperty('voice', voice.id)\
                break\
\
        self.setup_ui()\
        \
        # \uc0\u21551 \u21160 \u38899 \u39057 \u30417 \u27979 \u32447 \u31243 \
        self.audio_thread = threading.Thread(target=self.monitor_audio)\
        self.audio_thread.daemon = True\
        self.audio_thread.start()\
\
    def setup_ui(self):\
        # \uc0\u38408 \u20540 \u25511 \u21046 \u21306 \
        control_frame = tk.Frame(self.root)\
        control_frame.pack(pady=20)\
\
        tk.Label(control_frame, text="\uc0\u35774 \u32622 \u25253 \u35686 \u20998 \u36125 \u38408 \u20540 :", font=("\u24494 \u36719 \u38597 \u40657 ", 12)).pack(side=tk.LEFT, padx=10)\
        \
        self.threshold_var = tk.IntVar(value=70) # \uc0\u40664 \u35748 \u38408 \u20540 \u35774 \u20026 70\
        self.slider = tk.Scale(control_frame, from_=30, to=120, orient=tk.HORIZONTAL, \
                               variable=self.threshold_var, length=300)\
        self.slider.pack(side=tk.LEFT)\
\
        # \uc0\u24403 \u21069 \u38899 \u37327 \u26174 \u31034 \
        self.vol_label = tk.Label(self.root, text="\uc0\u24403 \u21069 \u38899 \u37327 : 0 dB", font=("\u24494 \u36719 \u38597 \u40657 ", 16, "bold"), fg="green")\
        self.vol_label.pack(pady=10)\
\
        # \uc0\u27874 \u24418 \u22270 \u30011 \u24067 \
        self.canvas = tk.Canvas(self.root, width=500, height=200, bg="black")\
        self.canvas.pack(pady=10)\
\
        # \uc0\u24377 \u31383 \u21021 \u22987 \u21270  (\u40664 \u35748 \u38544 \u34255 )\
        self.warning_window = tk.Toplevel(self.root)\
        self.warning_window.title("\uc0\u35686 \u21578 \u65281 ")\
        self.warning_window.geometry("800x300")\
        self.warning_window.withdraw() # \uc0\u38544 \u34255 \
        self.warning_window.attributes("-topmost", True) # \uc0\u32622 \u39030 \u26174 \u31034 \
        self.warning_window.configure(bg="red")\
        \
        warning_font = font.Font(family="\uc0\u24494 \u36719 \u38597 \u40657 ", size=48, weight="bold")\
        tk.Label(self.warning_window, text="\uc0\u35831 \u21516 \u23398 \u20204 \u20445 \u25345 \u23433 \u38745 \u65281 \\n\u19981 \u35201 \u22823 \u22768 \u35762 \u35805 \u65281 ", \
                 font=warning_font, bg="red", fg="white").pack(expand=True)\
\
    def monitor_audio(self):\
        p = pyaudio.PyAudio()\
        try:\
            stream = p.open(format=self.FORMAT,\
                            channels=self.CHANNELS,\
                            rate=self.RATE,\
                            input=True,\
                            frames_per_buffer=self.CHUNK)\
        except Exception as e:\
            print(f"\uc0\u26080 \u27861 \u25171 \u24320 \u40614 \u20811 \u39118 : \{e\}")\
            return\
\
        while self.is_running:\
            try:\
                data = stream.read(self.CHUNK, exception_on_overflow=False)\
                audio_data = np.frombuffer(data, dtype=np.int16)\
                \
                # \uc0\u35745 \u31639  RMS (Root Mean Square) \u20316 \u20026 \u38899 \u37327 \u22522 \u20934 \
                rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))\
                \
                # \uc0\u23558  RMS \u36716 \u25442 \u20026 \u20266 \u20998 \u36125 \u20540  (\u36817 \u20284 \u20540 \u65292 \u20165 \u20316 \u30456 \u23545 \u22823 \u23567 \u21442 \u32771 )\
                if rms > 0:\
                    db = 20 * math.log10(rms)\
                else:\
                    db = 0\
                \
                # \uc0\u38480 \u21046 \u26174 \u31034 \u33539 \u22260 \
                display_db = max(0, min(120, int(db)))\
                \
                # \uc0\u26356 \u26032  UI (\u24517 \u39035 \u22312 \u20027 \u32447 \u31243 \u25191 \u34892 )\
                self.root.after(0, self.update_ui, display_db)\
                \
                # \uc0\u26816 \u26597 \u26159 \u21542 \u36229 \u36807 \u38408 \u20540 \u65292 \u19988 \u24403 \u21069 \u19981 \u22312 \u25253 \u35686 \u29366 \u24577 \u20013 \
                if display_db > self.threshold_var.get() and not self.is_warning:\
                    self.is_warning = True\
                    self.root.after(0, self.trigger_warning)\
\
            except Exception as e:\
                print(e)\
\
        stream.stop_stream()\
        stream.close()\
        p.terminate()\
\
    def update_ui(self, db):\
        # \uc0\u26356 \u26032 \u25991 \u23383 \
        color = "red" if db > self.threshold_var.get() else "green"\
        self.vol_label.config(text=f"\uc0\u24403 \u21069 \u38899 \u37327 : \{db\} dB", fg=color)\
\
        # \uc0\u26356 \u26032 \u27874 \u24418 \u22270 \u25968 \u25454 \
        self.history_vol.append(db)\
        if len(self.history_vol) > 100:\
            self.history_vol.pop(0)\
\
        self.canvas.delete("waveform")\
        \
        # \uc0\u32472 \u21046 \u27874 \u24418 \u32447 \
        width = 500\
        height = 200\
        x_step = width / len(self.history_vol)\
        \
        points = []\
        for i, val in enumerate(self.history_vol):\
            x = i * x_step\
            # \uc0\u23558  dB (0-120) \u26144 \u23556 \u21040 \u30011 \u24067 \u39640 \u24230 \
            y = height - (val / 120.0) * height\
            points.append((x, y))\
\
        for i in range(len(points) - 1):\
            self.canvas.create_line(points[i][0], points[i][1], \
                                    points[i+1][0], points[i+1][1], \
                                    fill="lime", width=2, tags="waveform")\
\
    def trigger_warning(self):\
        # \uc0\u26174 \u31034 \u22823 \u23383 \u24377 \u31383 \
        self.warning_window.deiconify()\
        \
        # \uc0\u21551 \u21160 \u35821 \u38899 \u25773 \u25253 \u32447 \u31243  (\u36991 \u20813 \u38459 \u22622 \u20027 \u24490 \u29615 )\
        threading.Thread(target=self.play_voice).start()\
\
    def play_voice(self):\
        # \uc0\u25773 \u25918 \u35821 \u38899 \
        self.engine.say("\uc0\u35831 \u21516 \u23398 \u20204 \u20445 \u25345 \u23433 \u38745 \u65292 \u19981 \u35201 \u22823 \u22768 \u35762 \u35805 ")\
        self.engine.runAndWait()\
        \
        # \uc0\u35821 \u38899 \u25773 \u25918 \u23436 \u27605 \u21518 \u65292 \u24310 \u36831 2\u31186 \u20851 \u38381 \u24377 \u31383 \u65292 \u24182 \u24674 \u22797 \u30417 \u27979 \
        time.sleep(2)\
        self.root.after(0, self.warning_window.withdraw)\
        # \uc0\u31561 \u24453 \u19968 \u23567 \u27573 \u26102 \u38388 \u36991 \u20813 \u33258 \u24049 \u25773 \u25253 \u30340 \u22768 \u38899 \u20877 \u27425 \u35302 \u21457 \u25253 \u35686 \
        time.sleep(1) \
        self.is_warning = False\
\
    def on_closing(self):\
        self.is_running = False\
        self.root.destroy()\
\
if __name__ == "__main__":\
    root = tk.Tk()\
    app = NoiseMonitorApp(root)\
    root.mainloop()}