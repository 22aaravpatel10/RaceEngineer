import sys
import os
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QDialog, 
                             QPushButton, QLabel, QComboBox, QHBoxLayout, QWidget)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, Qt, QThread, pyqtSignal

from backend.data_manager import RaceControlWorker, OpenF1Client


class SessionSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mission Control")
        self.setStyleSheet("""
            QDialog { background-color: #1C1C1E; color: white; }
            QLabel { color: #8E8E93; font-weight: bold; }
            QComboBox { 
                background: #2C2C2E; color: white; padding: 8px; 
                border-radius: 8px; border: 1px solid #333; 
            }
            QPushButton { 
                background: #0A84FF; color: white; border: none; 
                padding: 12px; border-radius: 8px; font-weight: bold; 
            }
            QPushButton:hover { background: #0077ED; }
        """)
        self.resize(450, 300)
        self.selected_session = None
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("SELECT SESSION"))
        
        # 1. Year Selector
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2025", "2024", "2023"])
        self.year_combo.currentTextChanged.connect(self.load_sessions)
        layout.addWidget(self.year_combo)
        
        # 2. Session Selector
        self.session_combo = QComboBox()
        layout.addWidget(self.session_combo)
        
        # 3. Mode Toggle
        layout.addWidget(QLabel("MODE"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Real Data", "Simulation (Proxy)"])
        layout.addWidget(self.mode_combo)
        
        btn = QPushButton("ENTER PITWALL")
        btn.clicked.connect(self.accept_selection)
        layout.addWidget(btn)
        
        self.load_sessions("2025")

    def load_sessions(self, year):
        self.session_combo.clear()
        self.session_combo.addItem("Fetching OpenF1...", None)
        sessions = OpenF1Client.get_sessions(year=int(year))
        
        self.session_combo.clear()
        if not sessions:
            self.session_combo.addItem(f"No Data for {year}", None)
            return
            
        for s in sessions:
            name = f"{s['country_name']} - {s['session_name']}"
            self.session_combo.addItem(name, s['country_name'])

    def accept_selection(self):
        country = self.session_combo.currentData()
        if country:
            self.selected_session = {
                "year": self.year_combo.currentText(),
                "country": country,
                "mode": "Simulation" if "Simulation" in self.mode_combo.currentText() else "Real"
            }
            self.accept()


class Bridge(QObject):
    request_telemetry = pyqtSignal(str)
    request_analysis_bridge = pyqtSignal(str, str)  # driver, mode
    command_received = pyqtSignal(str)
    
    def __init__(self, view):
        super().__init__()
        self.view = view

    @pyqtSlot(str)
    def driver_selected(self, driver_id):
        """Legacy support - redirect to QUALI mode"""
        self.request_analysis_bridge.emit(driver_id, 'QUALI')

    @pyqtSlot(str, str)
    def driver_mode_selected(self, driver_id, mode):
        """Called when user clicks a driver OR changes the mode dropdown"""
        print(f"Requesting {mode} for {driver_id}")
        self.request_analysis_bridge.emit(driver_id, mode)

    @pyqtSlot(str)
    def process_command(self, cmd):
        self.command_received.emit(cmd)
        
    @pyqtSlot()
    def close_window(self):
        self.view.window().close()
    
    @pyqtSlot()
    def minimize_window(self):
        self.view.window().showMinimized()

    @pyqtSlot()
    def maximize_window(self):
        window = self.view.window()
        if window.isMaximized():
            window.showNormal()
        else:
            window.showMaximized()


class OvercutWindow(QMainWindow):
    request_load = pyqtSignal(str, str, str)
    request_alignment = pyqtSignal(str, str)

    def __init__(self, session_data):
        super().__init__()
        self.session_data = session_data
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
        
        self.channel = QWebChannel()
        self.bridge = Bridge(self.browser)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)
        
        self.bridge.command_received.connect(self.handle_command)

    def setup_backend(self):
        self.thread = QThread()
        self.worker = RaceControlWorker()
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.request_load.connect(self.worker.load_session)
        self.bridge.request_analysis_bridge.connect(self.worker.request_analysis)
        self.request_alignment.connect(self.worker.align_drivers)
        
        # Worker responses
        self.worker.initialized.connect(self.on_ready)
        self.worker.analysis_ready.connect(self.send_analysis_to_js)
        self.worker.comparison_ready.connect(self.send_comparison_to_js)
        
        self.thread.start()
        self.request_load.emit(
            self.session_data['year'], 
            self.session_data['country'], 
            self.session_data['mode']
        )

    def on_ready(self, drivers):
        self.browser.page().runJavaScript(f"updateDriverList({json.dumps(drivers)});")
        title = f"{self.session_data['country'].upper()} {self.session_data['year']}"
        self.browser.page().runJavaScript(f'updateSessionStatus({{"text":"{title}", "flag":"GREEN"}});')

    def send_analysis_to_js(self, data):
        self.browser.page().runJavaScript(f"renderAnalysis({json.dumps(data)});")

    def send_comparison_to_js(self, data):
        self.browser.page().runJavaScript(f"renderChart({json.dumps(data)});")

    def handle_command(self, command: str):
        print(f"Command: {command}")
        match = re.search(r"compare (\w+) and (\w+)", command, re.IGNORECASE)
        if match:
            d1, d2 = match.groups()
            self.request_alignment.emit(d1.upper(), d2.upper())

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


if __name__ == "__main__":
    if not os.path.exists('f1_cache'):
        os.makedirs('f1_cache')
    import fastf1
    fastf1.Cache.enable_cache('f1_cache')

    app = QApplication(sys.argv)
    
    selector = SessionSelectDialog()
    if selector.exec():
        window = OvercutWindow(selector.selected_session)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()
