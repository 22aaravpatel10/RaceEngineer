import sys
import os
import json
import re
import fastf1

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QDialog, 
                             QPushButton, QLabel, QComboBox, QHBoxLayout, QWidget)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, Qt, QThread, pyqtSignal

from backend.data_manager import RaceControlWorker, OpenF1Client


class SessionSelectDialog(QDialog):
    """Session selector with OpenF1 integration"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mission Control")
        self.setStyleSheet("""
            QDialog { background-color: #1C1C1E; color: white; }
            QLabel { color: #8E8E93; font-weight: bold; margin-top: 10px; }
            QComboBox { 
                background: #2C2C2E; color: white; padding: 8px; 
                border-radius: 8px; border: 1px solid #333; 
                min-height: 20px;
            }
            QPushButton { 
                background: #0A84FF; color: white; border: none; 
                padding: 12px; border-radius: 8px; font-weight: bold; 
                margin-top: 20px;
            }
            QPushButton:hover { background: #0077ED; }
        """)
        self.resize(450, 350)
        self.selected_session = None
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("OVERCUT - MISSION CONTROL")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 1. Year Selector
        layout.addWidget(QLabel("YEAR"))
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2024", "2023"])
        self.year_combo.currentTextChanged.connect(self.load_sessions)
        layout.addWidget(self.year_combo)
        
        # 2. Session Selector (Populated from OpenF1)
        layout.addWidget(QLabel("SESSION"))
        self.session_combo = QComboBox()
        layout.addWidget(self.session_combo)
        
        # 3. Mode Toggle
        layout.addWidget(QLabel("MODE"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Real Data", "2025 Simulation"])
        layout.addWidget(self.mode_combo)
        
        # Load Button
        btn = QPushButton("ENTER PITWALL")
        btn.clicked.connect(self.accept_selection)
        layout.addWidget(btn)
        
        # Initial Load
        self.load_sessions("2024")

    def load_sessions(self, year):
        self.session_combo.clear()
        self.session_combo.addItem("Loading from OpenF1...", None)
        
        # Fetch sessions
        sessions = OpenF1Client.get_sessions(year=int(year))
        
        self.session_combo.clear()
        if not sessions:
            self.session_combo.addItem("No sessions found (Offline?)", None)
            # Add fallback sessions
            fallback = ["Bahrain", "Saudi Arabia", "Australia", "Japan", "China", 
                       "Miami", "Monaco", "Canada", "Spain", "Austria", "Britain",
                       "Hungary", "Belgium", "Netherlands", "Monza", "Singapore",
                       "United States", "Mexico", "Brazil", "Las Vegas", "Abu Dhabi"]
            for country in fallback:
                self.session_combo.addItem(f"{country} - Qualifying", country)
            return
            
        for s in sessions:
            name = f"{s.get('country_name', 'Unknown')} - {s.get('session_name', 'Session')}"
            self.session_combo.addItem(name, s.get('country_name'))

    def accept_selection(self):
        country = self.session_combo.currentData()
        if country:
            self.selected_session = {
                "year": self.year_combo.currentText(),
                "country": country,
                "mode": "Simulation" if "2025" in self.mode_combo.currentText() else "Real"
            }
            self.accept()


class Bridge(QObject):
    """Bridge between JavaScript and Python"""
    request_telemetry = pyqtSignal(str)
    command_received = pyqtSignal(str)
    
    def __init__(self, view):
        super().__init__()
        self.view = view

    @pyqtSlot(str)
    def driver_selected(self, driver_id):
        print(f"Bridge: driver_selected({driver_id})")
        self.request_telemetry.emit(driver_id)
        
    @pyqtSlot(str)
    def process_command(self, cmd):
        self.command_received.emit(cmd)
        
    @pyqtSlot()
    def close_window(self):
        self.view.window().close()
    
    @pyqtSlot()
    def minimize_window(self):
        self.view.window().showMinimized()


class OvercutWindow(QMainWindow):
    """Main application window"""
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
        
        # Web Channel
        self.channel = QWebChannel()
        self.bridge = Bridge(self.browser)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)
        
        # Connect command handler
        self.bridge.command_received.connect(self.handle_command)

    def setup_backend(self):
        # Threading
        self.thread = QThread()
        self.worker = RaceControlWorker()
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.request_load.connect(self.worker.load_session)
        self.bridge.request_telemetry.connect(self.worker.fetch_telemetry)
        self.request_alignment.connect(self.worker.align_drivers)
        
        # Worker responses
        self.worker.initialized.connect(self.on_ready)
        self.worker.telemetry_ready.connect(self.send_telemetry)
        self.worker.comparison_ready.connect(self.send_comparison)
        
        self.thread.start()
        
        # Trigger the load after a delay to ensure page is ready
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(800, self.trigger_load)

    def trigger_load(self):
        self.request_load.emit(
            self.session_data['year'], 
            self.session_data['country'], 
            self.session_data['mode']
        )

    def on_ready(self, drivers):
        """Called when worker finishes loading driver grid"""
        title = f"{self.session_data['country'].upper()} {self.session_data['year']}"
        mode_text = "(SIM)" if self.session_data['mode'] == 'Simulation' else ""
        self.browser.page().runJavaScript(
            f'updateSessionStatus({{"text":"{title} {mode_text}", "flag":"GREEN"}});'
        )
        self.browser.page().runJavaScript(f"updateDriverList({json.dumps(drivers)});")

    def send_telemetry(self, data):
        self.browser.page().runJavaScript(f"renderTelemetry({json.dumps(data)});")

    def send_comparison(self, data):
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


if __name__ == "__main__":
    # Ensure cache exists
    if not os.path.exists('f1_cache'):
        os.makedirs('f1_cache')
    fastf1.Cache.enable_cache('f1_cache')

    app = QApplication(sys.argv)
    
    # 1. Show Session Selector
    selector = SessionSelectDialog()
    if selector.exec():
        # 2. Launch Main Window with selection
        window = OvercutWindow(selector.selected_session)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()
