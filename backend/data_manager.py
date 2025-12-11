import fastf1
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import config

class RaceControlWorker(QObject):
    """
    The Single Source of Truth. Runs on a background thread.
    Owns the FastF1 session and handles all data requests.
    """
    initialized = pyqtSignal(list)       # Returns list of drivers when done loading
    telemetry_ready = pyqtSignal(dict)   # Returns telemetry data
    comparison_ready = pyqtSignal(dict)  # Returns alignment data
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.laps = None
        self.current_map = None
        self.year_mode = None

    @pyqtSlot(str)
    def load_season(self, mode):
        """
        Loads the simulation.
        mode: '2025' or '2026'
        """
        print(f"RaceControl: Loading {mode} Grid...")
        try:
            # 1. Select Map
            self.year_mode = mode
            self.current_map = config.GRID_2026 if mode == '2026' else config.GRID_2025
            
            # 2. Load FastF1 Session (Abu Dhabi 2023 as base)
            self.session = fastf1.get_session(2023, 'Abu Dhabi', 'Q')
            self.session.load()
            self.laps = self.session.laps
            
            # 3. Generate Driver List for UI
            ui_drivers = []
            for drv_id, info in self.current_map.items():
                source = info['source']
                # Check if source driver exists in 2023 data
                if source in self.laps['Driver'].unique():
                    drv_laps = self.laps.pick_driver(source)
                    fastest = drv_laps.pick_fastest()
                    
                    if fastest is not None:
                        # Formatting lap time
                        lap_time = str(fastest['LapTime']).split('days')[-1].strip()
                        # Clean up microseconds
                        if '.' in lap_time:
                            lap_time = lap_time[:-3]
                            
                        ui_drivers.append({
                            "id": drv_id,
                            "team": info['team'],
                            "color": config.TEAM_COLORS.get(info['team'], "#FFF"),
                            "lap_time": lap_time,
                            "position": int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                        })
            
            # Sort by position
            ui_drivers.sort(key=lambda x: x['position'])
            self.initialized.emit(ui_drivers)
            print(f"RaceControl: Load Complete. {len(ui_drivers)} drivers.")

        except Exception as e:
            print(f"RaceControl Error: {e}")
            self.error_occurred.emit(str(e))

    @pyqtSlot(str)
    def fetch_telemetry(self, driver_id):
        """Get single driver telemetry"""
        if not self.current_map or driver_id not in self.current_map:
            print(f"Unknown driver: {driver_id}")
            return

        try:
            source = self.current_map[driver_id]['source']
            lap = self.laps.pick_driver(source).pick_fastest()
            
            if lap is None:
                print(f"No lap data for source driver: {source}")
                return
                
            car = lap.get_car_data().add_distance()
            
            data = {
                "driver": driver_id,
                "team": self.current_map[driver_id]['team'],
                "color": config.TEAM_COLORS.get(self.current_map[driver_id]['team'], "#FFF"),
                "distance": car['Distance'].tolist(),
                "speed": car['Speed'].tolist(),
                "throttle": car['Throttle'].tolist(),
                "brake": car['Brake'].astype(int).tolist(),
                "rpm": car['RPM'].tolist(),
                "gear": car['nGear'].tolist()
            }
            self.telemetry_ready.emit(data)
        except Exception as e:
            print(f"Telem Error {driver_id}: {e}")

    @pyqtSlot(str, str)
    def align_drivers(self, d1, d2):
        """Ghost Car Alignment"""
        if not self.current_map:
            return
            
        if d1 not in self.current_map or d2 not in self.current_map:
            print(f"Unknown driver in comparison: {d1} or {d2}")
            return
        
        try:
            # Map new IDs to old sources
            s1 = self.current_map[d1]['source']
            s2 = self.current_map[d2]['source']
            
            l1 = self.laps.pick_driver(s1).pick_fastest().get_car_data().add_distance()
            l2 = self.laps.pick_driver(s2).pick_fastest().get_car_data().add_distance()
            
            # Interpolation Logic
            max_d = min(l1['Distance'].max(), l2['Distance'].max())
            common_dist = np.arange(0, max_d, 5)  # 5m slices
            
            # Scipy Interp
            speed1 = interp1d(l1['Distance'], l1['Speed'], fill_value="extrapolate")(common_dist)
            speed2 = interp1d(l2['Distance'], l2['Speed'], fill_value="extrapolate")(common_dist)
            
            delta = speed1 - speed2
            
            payload = {
                "type": "comparison",
                "axis": common_dist.tolist(),
                "drivers": {
                    d1: speed1.tolist(),
                    d2: speed2.tolist()
                },
                "delta": delta.tolist(),
                "meta": {
                    "d1": d1,
                    "d2": d2,
                    "c1": config.TEAM_COLORS.get(self.current_map[d1]['team'], "#1E41FF"),
                    "c2": config.TEAM_COLORS.get(self.current_map[d2]['team'], "#FF2800")
                }
            }
            self.comparison_ready.emit(payload)
            
        except Exception as e:
            print(f"Alignment Error: {e}")
