import sys
import os
import re
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, Qt, QThread, pyqtSignal

from backend.data_manager import DataManager, SessionManager
from config import get_driver_color

class Bridge(QObject):
    """
    Bridge between JavaScript frontend and Python backend.
    """
    command_received = pyqtSignal(str)
    driver_selected_signal = pyqtSignal(str) # Signal when driver clicked

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.session_manager = SessionManager()

    @pyqtSlot(str)
    def process_command(self, command):
        """Pass command to Main Thread for processing"""
        self.command_received.emit(command)

    @pyqtSlot()
    def start_simulation(self):
        """Called by JavaScript when the app loads - loads 2025 Simulation"""
        print("Initializing 2025 Simulation...")
        drivers = self.session_manager.load_simulation_2025()
        
        # Send the full driver list to the UI
        json_str = json.dumps(drivers)
        self.view.page().runJavaScript(f"updateDriverList({json_str});")
        
        # Update Dynamic Island
        self.view.page().runJavaScript('updateSessionStatus({"type":"status","text":"ABU DHABI 2025 SIM","flag":"GREEN"});')

    @pyqtSlot(str)
    def driver_selected(self, driver_id):
        """Called when user clicks a driver card"""
        print(f"Driver Selected: {driver_id}")
        
        # Get the fake 2025 telemetry (Time Machine)
        telemetry = self.session_manager.get_telemetry_for_driver(driver_id)
        
        if telemetry:
            json_str = json.dumps(telemetry)
            self.view.page().runJavaScript(f"renderTelemetry({json_str});")
        else:
            print(f"No telemetry found for {driver_id}")

    def send_chart_data(self, payload):
        """Invoke JS function to render comparison chart"""
        json_str = json.dumps(payload)
        self.view.page().runJavaScript(f"renderChart({json_str});")

    def send_session_status(self, payload):
        """Update Dynamic Island"""
        json_str = json.dumps(payload)
        self.view.page().runJavaScript(f"updateSessionStatus({json_str});")

    @pyqtSlot()
    def minimize_window(self):
        """Minimize the application window"""
        # Get the parent window and minimize
        window = self.view.window()
        if window:
            window.showMinimized()

    @pyqtSlot()
    def close_window(self):
        """Close the application window"""
        window = self.view.window()
        if window:
            window.close()


class OvercutWindow(QMainWindow):
    request_alignment_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #000000;") # True black for Apple aesthetic

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Frameless Drag Logic Init
        self._drag_pos = None

        # WebView
        self.browser = QWebEngineView()
        self.browser.setStyleSheet("background: transparent;")
        
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend/dashboard.html"))
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        
        layout.addWidget(self.browser)

        # Bridge Setup
        self.channel = QWebChannel()
        self.bridge = Bridge(self.browser)
        self.channel.registerObject("bridge", self.bridge) # Expose as "bridge" to JS
        self.browser.page().setWebChannel(self.channel)
        
        # Connect Bridge Signal for text commands
        self.bridge.command_received.connect(self.handle_command)

        # Backend Thread Setup (for live polling / Ghost Car)
        self.thread = QThread()
        self.data_manager = DataManager()
        self.data_manager.moveToThread(self.thread)
        self.thread.start()

        # Connect Backend Signals
        self.data_manager.data_ready.connect(self.bridge.send_chart_data)
        self.data_manager.session_status_updated.connect(self.bridge.send_session_status)
        
        # Connect alignment signal
        self.request_alignment_signal.connect(self.data_manager.align_telemetry)

    def mousePressEvent(self, event):
        # Custom Drag Logic for Title Bar Area (Top 50px for Dynamic Island area)
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 50:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def handle_command(self, command: str):
        print(f"Command: {command}")
        # Regex Parser
        # Pattern: Compare [DriverA] and [DriverB]
        match = re.search(r"compare (\w+) and (\w+)", command, re.IGNORECASE)
        if match:
            d1, d2 = match.groups()
            self.request_alignment_signal.emit(d1.upper(), d2.upper())
        else:
            print("Command not recognized. Try 'Compare VER and HAM'")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OvercutWindow()
    window.show()
    sys.exit(app.exec())
