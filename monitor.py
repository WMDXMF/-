import sys
import numpy as np
import sounddevice as sd
import pyttsx3
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QLabel, QSlider, QHBoxLayout)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg

class AdvancedMonitor(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- 核心逻辑参数 ---
        self.threshold = 0.15     # 默认触发阈值
        self.fs = 44100          # 采样率
        self.audio_history = np.zeros(1000) # 波形缓存
        
        # 语音引擎初始化
        self.engine = pyttsx3.init()
        self.is_speaking = False
        self.last_speech_time = 0
        self.cooldown = 4        # 两次播报之间至少间隔4秒

        self.initUI()
        
        # 启动音频流
        try:
            self.stream = sd.InputStream(channels=1, samplerate=self.fs, callback=self.audio_callback)
            self.stream.start()
        except Exception as e:
            print(f"音频设备启动失败: {e}")

        # 定时器：每30ms刷新界面
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(30)

    def initUI(self):
        self.setWindowTitle("教室噪音智能监测仪")
        self.setMinimumSize(800, 500)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # 1. 警示显示区
        self.warning_box = QLabel("📢 请保持安静！")
        self.warning_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning_box.setFont(QFont("Microsoft YaHei", 48, QFont.Weight.Bold))
        self.warning_box.setStyleSheet("""
            QLabel {
                color: white; 
                background-color: #e74c3c; 
                border-radius: 20px; 
                margin: 10px;
            }
        """)
        self.warning_box.hide()
        layout.addWidget(self.warning_box)

        # 2. 波形图表区
        self.plot_widget = pg.PlotWidget(title="环境音量实时波形")
        self.plot_widget.setBackground('#f0f0f0')
        self.curve = self.plot_widget.plot(pen=pg.mkPen('#3498db', width=2))
        self.plot_widget.setYRange(-0.8, 0.8)
        layout.addWidget(self.plot_widget)

        # 3. 设置控制区
        control_panel = QVBoxLayout()
        
        # 阈值调节文字
        self.label_status = QLabel(f"当前触发阈值: {self.threshold:.2f} (越小越灵敏)")
        self.label_status.setFont(QFont("Microsoft YaHei", 12))
        
        # 阈值调节滑动条
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 100) # 0.01 到 1.00
        self.slider.setValue(int(self.threshold * 100))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.valueChanged.connect(self.on_slider_change)

        control_panel.addWidget(self.label_status)
        control_panel.addWidget(self.slider)
        layout.addLayout(control_panel)

    def audio_callback(self, indata, frames, time, status):
        """实时捕获麦克风信号"""
        data = indata[:, 0]
        self.audio_history = np.roll(self.audio_history, -len(data))
        self.audio_history[-len(data):] = data

    def on_slider_change(self, value):
        """手动设置触发大小"""
        self.threshold = value / 100.0
        self.label_status.setText(f"当前触发阈值: {self.threshold:.2f} (越小越灵敏)")

    def trigger_voice(self):
        """异步播报语音"""
        def run():
            self.is_speaking = True
            self.engine.say("请同学们保持安静，不要大声讲话")
            self.engine.runAndWait()
            self.is_speaking = False
            self.last_speech_time = time.time()
        
        threading.Thread(target=run, daemon=True).start()

    def refresh_ui(self):
        """界面更新与逻辑判断"""
        # 更新波形图
        self.curve.setData(self.audio_history)
        
        # 获取当前瞬时音量峰值
        peak_volume = np.max(np.abs(self.audio_history))

        # 逻辑判断
        if peak_volume > self.threshold:
            self.warning_box.show()
            # 只有在“非播报中”且“冷却时间已过”时才发声
            if not self.is_speaking and (time.time() - self.last_speech_time > self.cooldown):
                self.trigger_voice()
        else:
            if not self.is_speaking:
                self.warning_box.hide()

    def closeEvent(self, event):
        self.stream.stop()
        self.engine.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedMonitor()
    window.show()
    sys.exit(app.exec())
