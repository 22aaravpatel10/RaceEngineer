import sys
import os
import json
import re
import fastf1

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QDialog, QPushButton, QLabel, QHBoxLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, Qt, QThread, pyqtSignal

from backend.data_manager import RaceControlWorker

# --- Startup Dialog ---
class SeasonSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Season")
        self.setStyleSheet("background-color: #1C1C1E; color: white; font-family: sans-serif;")
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("SELECT GRID CONFIGURATION")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 20px;")
        layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        
        self.btn_2025 = QPushButton("2025 SIMULATION\n(Abu Dhabi Data)")
        self.btn_2025.setStyleSheet("background: #0A84FF; border: none; padding: 15px; border-radius: 8px; font-weight: bold;")
        self.btn_2025.clicked.connect(lambda: self.done(2025))
        
        self.btn_2026 = QPushButton("2026 PREDICTION\n(Audi + Cadillac)")
        self.btn_2026.setStyleSheet("background: #FF3B30; border: none; padding: 15px; border-radius: 8px; font-weight: bold;")
        self.btn_2026.clicked.connect(lambda: self.done(2026))
        
        btn_layout.addWidget(self.btn_2025)
        btn_layout.addWidget(self.btn_2026)
        layout.addLayout(btn_layout)


# --- Bridge ---
class Bridge(QObject):
    command_received = pyqtSignal(str)
    request_telemetry = pyqtSignal(str)
    
    def __init__(self, view):
        super().__init__()
        self.view = view

    @pyqtSlot(str)
    def driver_selected(self, driver_id):
        """Called when user clicks a driver card"""
        print(f"Driver Selected: {driver_id}")
        self.request_telemetry.emit(driver_id)
        
    @pyqtSlot(str)
    def process_command(self, cmd):
        """Pass command to Main Window for processing"""
        self.command_received.emit(cmd)

    @pyqtSlot()
    def minimize_window(self):
        """Minimize the application window"""
        window = self.view.window()
        if window:
            window.showMinimized()

    @pyqtSlot()
    def close_window(self):
        """Close the application window"""
        window = self.view.window()
        if window:
            window.close()


# --- Main Window ---
class OvercutWindow(QMainWindow):
    request_load_season = pyqtSignal(str)
    request_alignment = pyqtSignal(str, str)

    def __init__(self, mode):
        super().__init__()
        self.mode = str(mode)
        self._drag_pos = None
        self.setup_ui()
        self.setup_backend()

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1300, 850)
        self.setStyleSheet("background-color: #000000;")
        
        self.browser = QWebEngineView()
        self.browser.setStyleSheet("background: transparent;")
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend/dashboard.html"))
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        
        self.setCentralWidget(self.browser)
        
        # Channel
        self.channel = QWebChannel()
        self.bridge = Bridge(self.browser)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)
        
        # Connect bridge commands
        self.bridge.command_received.connect(self.handle_command)

    def setup_backend(self):
        # Threading
        self.thread = QThread()
        self.worker = RaceControlWorker()
        self.worker.moveToThread(self.thread)
        
        # Connect Signals
        self.request_load_season.connect(self.worker.load_season)
        self.bridge.request_telemetry.connect(self.worker.fetch_telemetry)
        self.request_alignment.connect(self.worker.align_drivers)
        
        # Worker Responses
        self.worker.initialized.connect(self.on_grid_ready)
        self.worker.telemetry_ready.connect(self.send_to_js_telemetry)
        self.worker.comparison_ready.connect(self.send_to_js_chart)
        
        # Start Thread
        self.thread.start()
        
        # Trigger Load after a small delay to ensure JS is ready
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, lambda: self.request_load_season.emit(self.mode))

    def on_grid_ready(self, drivers):
        """Called when worker finishes loading driver grid"""
        txt = f"ABU DHABI - {self.mode} GRID"
        self.browser.page().runJavaScript(f'updateSessionStatus({{"type":"status", "text":"{txt}", "flag":"GREEN"}});')
        self.browser.page().runJavaScript(f"updateDriverList({json.dumps(drivers)});")

    def send_to_js_telemetry(self, data):
        self.browser.page().runJavaScript(f"renderTelemetry({json.dumps(data)});")

    def send_to_js_chart(self, data):
        self.browser.page().runJavaScript(f"renderChart({json.dumps(data)});")

    def handle_command(self, command: str):
        """Parse natural language commands"""
        print(f"Command: {command}")
        match = re.search(r"compare (\w+) and (\w+)", command, re.IGNORECASE)
        if match:
            d1, d2 = match.groups()
            self.request_alignment.emit(d1.upper(), d2.upper())
        else:
            print("Command not recognized. Try 'Compare VER and HAM'")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 50:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# --- Entry Point ---
if __name__ == "__main__":
    # Ensure cache exists
    if not os.path.exists('f1_cache'):
        os.makedirs('f1_cache')
    fastf1.Cache.enable_cache('f1_cache')

    app = QApplication(sys.argv)
    
    # Show Selector
    dialog = SeasonSelectDialog()
    result = dialog.exec()
    
    if result in [2025, 2026]:
        window = OvercutWindow(result)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()
