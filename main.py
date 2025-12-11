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
        self.year_combo.addItems(["2025", "2024", "2023"])  # UPDATED with 2025
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
        
        self.load_sessions("2025")  # Default to 2025

    def load_sessions(self, year):
        self.session_combo.clear()
        self.session_combo.addItem("Fetching OpenF1...", None)
        # Using the backend helper directly for UI speed
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
    
    def __init__(self, view):
        super().__init__()
        self.view = view

    @pyqtSlot(str)
    def driver_selected(self, driver_id):
        self.request_telemetry.emit(driver_id)
        
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
        
        # LOAD LOCAL FILE
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend/dashboard.html"))
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        
        self.setCentralWidget(self.browser)
        
        self.channel = QWebChannel()
        self.bridge = Bridge(self.browser)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

    def setup_backend(self):
        self.thread = QThread()
        self.worker = RaceControlWorker()
        self.worker.moveToThread(self.thread)
        
        self.request_load.connect(self.worker.load_session)
        self.bridge.request_telemetry.connect(self.worker.fetch_telemetry)
        
        self.worker.initialized.connect(self.on_ready)
        self.worker.telemetry_ready.connect(self.send_telemetry)
        
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

    def send_telemetry(self, data):
        self.browser.page().runJavaScript(f"renderTelemetry({json.dumps(data)});")

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
    if not os.path.exists('f1_cache'): os.makedirs('f1_cache')
    import fastf1
    fastf1.Cache.enable_cache('f1_cache')

    app = QApplication(sys.argv)
    
    # 1. Select Session
    selector = SessionSelectDialog()
    if selector.exec():
        # 2. Run Main Window
        window = OvercutWindow(selector.selected_session)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()
