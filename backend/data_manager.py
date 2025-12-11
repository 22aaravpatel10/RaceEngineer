import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import requests
from scipy.interpolate import interp1d
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import config

class OpenF1Client:
    """
    Direct client for OpenF1.org to fetch Session Lists fast.
    """
    BASE_URL = "https://api.openf1.org/v1"

    @staticmethod
    def get_sessions(year=2024):
        try:
            url = f"{OpenF1Client.BASE_URL}/sessions?year={year}"
            print(f"Fetching sessions from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filter for meaningful sessions (Quali/Race) to reduce noise
            sessions = [
                s for s in data 
                if s.get('session_name') in ['Qualifying', 'Race', 'Sprint']
            ]
            # Sort by date (newest first)
            sessions.sort(key=lambda x: x.get('date_start', ''), reverse=True)
            return sessions
        except Exception as e:
            print(f"OpenF1 Error: {e}")
            return []


class RaceControlWorker(QObject):
    """
    Unified backend worker running on QThread.
    Handles session loading, telemetry fetch, and Ghost Car alignment.
    """
    initialized = pyqtSignal(list)
    telemetry_ready = pyqtSignal(dict)
    comparison_ready = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.laps = None
        self.current_map = None  # If None, we use Real Drivers

    @staticmethod
    def clean_for_json(data_dict):
        """
        CRITICAL FIX: Converts numpy types to Python native types.
        Replaces NaN with None so JSON doesn't break.
        """
        clean = {}
        for key, value in data_dict.items():
            if isinstance(value, (np.ndarray, pd.Series)):
                # Convert to list and handle NaNs
                arr = value.tolist() if hasattr(value, 'tolist') else list(value)
                clean[key] = [
                    None if (isinstance(x, float) and (np.isnan(x) if not isinstance(x, type(None)) else False)) 
                    else (float(x) if isinstance(x, (np.floating, np.integer)) else x)
                    for x in arr
                ]
            elif isinstance(value, list):
                clean[key] = [
                    None if (isinstance(x, float) and np.isnan(x)) 
                    else (float(x) if isinstance(x, (np.floating, np.integer)) else x)
                    for x in value
                ]
            elif isinstance(value, (np.floating, np.integer)):
                clean[key] = float(value)
            else:
                clean[key] = value
        return clean

    @pyqtSlot(str, str, str)
    def load_session(self, year, country, session_type):
        """
        Loads a specific session via FastF1.
        session_type: 'Simulation' or 'Real'
        """
        print(f"RaceControl: Loading {year} {country} ({session_type})...")
        try:
            # 1. Load Data
            self.session = fastf1.get_session(int(year), country, 'Q')
            self.session.load()
            self.laps = self.session.laps
            
            # 2. Determine Mode
            ui_drivers = []
            
            if session_type == 'Simulation':
                # --- 2025 SIMULATION MODE ---
                self.current_map = config.GRID_2025
                for drv_id, info in self.current_map.items():
                    source = info['source']
                    if source in self.laps['Driver'].unique():
                        fastest = self.laps.pick_driver(source).pick_fastest()
                        if fastest is not None and pd.notna(fastest['LapTime']):
                            lap_time = str(fastest['LapTime']).split('days')[-1].strip()
                            if '.' in lap_time:
                                lap_time = lap_time[:-3]
                            ui_drivers.append({
                                "id": drv_id,
                                "team": info['team'],
                                "color": config.TEAM_COLORS.get(info['team'], "#FFF"),
                                "lap_time": lap_time,
                                "position": int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                            })
            else:
                # --- REAL HISTORICAL MODE ---
                self.current_map = None
                drivers = self.laps['Driver'].unique()
                for drv in drivers:
                    try:
                        drv_laps = self.laps.pick_driver(drv)
                        team = drv_laps['Team'].iloc[0] if len(drv_laps) > 0 else "Unknown"
                        try:
                            color = fastf1.plotting.team_color(team)
                        except:
                            color = "#FFFFFF"
                    except:
                        color = "#FFFFFF"
                        team = "Unknown"

                    fastest = self.laps.pick_driver(drv).pick_fastest()
                    if fastest is not None and pd.notna(fastest['LapTime']):
                        lap_time = str(fastest['LapTime']).split('days')[-1].strip()
                        if '.' in lap_time:
                            lap_time = lap_time[:-3]
                        pos = int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                        ui_drivers.append({
                            "id": drv,
                            "team": team,
                            "color": color,
                            "lap_time": lap_time,
                            "position": pos
                        })

            # Sort and Send
            ui_drivers.sort(key=lambda x: x['position'])
            self.initialized.emit(ui_drivers)
            print(f"Session Ready: {len(ui_drivers)} drivers")

        except Exception as e:
            print(f"Load Error: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str)
    def fetch_telemetry(self, driver_id):
        """Fetch telemetry for a single driver"""
        if self.laps is None:
            print("No session loaded")
            return

        try:
            # Handle Map vs Real
            target_id = driver_id
            team_color = "#0A84FF"
            
            if self.current_map and driver_id in self.current_map:
                target_id = self.current_map[driver_id]['source']
                team_name = self.current_map[driver_id]['team']
                team_color = config.TEAM_COLORS.get(team_name, "#FFF")
            else:
                # Try to get real team color
                try:
                    drv_laps = self.laps.pick_driver(target_id)
                    team = drv_laps['Team'].iloc[0]
                    team_color = fastf1.plotting.team_color(team)
                except:
                    pass
            
            # Fetch telemetry
            lap = self.laps.pick_driver(target_id).pick_fastest()
            if lap is None:
                print(f"No fastest lap for {target_id}")
                return
                
            car = lap.get_car_data().add_distance()
            
            # Get position data for track map
            x_pos = []
            y_pos = []
            try:
                pos = lap.get_pos_data()
                if pos is not None and len(pos) > 0:
                    # Interpolate X/Y to match telemetry timestamps
                    pos['Time_sec'] = pos['Time'].dt.total_seconds()
                    car['Time_sec'] = car['Time'].dt.total_seconds()
                    
                    fx = interp1d(pos['Time_sec'], pos['X'], fill_value="extrapolate")
                    fy = interp1d(pos['Time_sec'], pos['Y'], fill_value="extrapolate")
                    
                    x_pos = fx(car['Time_sec']).tolist()
                    y_pos = fy(car['Time_sec']).tolist()
            except Exception as e:
                print(f"GPS Data not available: {e}")
            
            # Prepare Raw Data
            raw_data = {
                "driver": driver_id,
                "color": team_color,
                "distance": car['Distance'],
                "speed": car['Speed'],
                "throttle": car['Throttle'],
                "brake": car['Brake'].astype(int),
                "rpm": car['RPM'],
                "gear": car['nGear'],
                "x_pos": x_pos,
                "y_pos": y_pos
            }
            
            # SANITIZE (The Fix for "No Data")
            clean_data = self.clean_for_json(raw_data)
            
            self.telemetry_ready.emit(clean_data)
            print(f"Telemetry sent for {driver_id}")
            
        except Exception as e:
            print(f"Telem Error ({driver_id}): {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str, str)
    def align_drivers(self, d1, d2):
        """Ghost Car Alignment"""
        if self.laps is None:
            return
        
        try:
            # Map IDs if in simulation mode
            s1 = self.current_map[d1]['source'] if self.current_map and d1 in self.current_map else d1
            s2 = self.current_map[d2]['source'] if self.current_map and d2 in self.current_map else d2
            
            l1 = self.laps.pick_driver(s1).pick_fastest().get_car_data().add_distance()
            l2 = self.laps.pick_driver(s2).pick_fastest().get_car_data().add_distance()
            
            max_d = min(l1['Distance'].max(), l2['Distance'].max())
            common_dist = np.arange(0, max_d, 5)
            
            speed1 = interp1d(l1['Distance'], l1['Speed'], fill_value="extrapolate")(common_dist)
            speed2 = interp1d(l2['Distance'], l2['Speed'], fill_value="extrapolate")(common_dist)
            
            delta = speed1 - speed2
            
            # Get colors
            c1 = config.TEAM_COLORS.get(self.current_map[d1]['team'], "#1E41FF") if self.current_map else "#1E41FF"
            c2 = config.TEAM_COLORS.get(self.current_map[d2]['team'], "#FF2800") if self.current_map else "#FF2800"
            
            raw_payload = {
                "type": "comparison",
                "axis": common_dist,
                "drivers": {
                    d1: speed1,
                    d2: speed2
                },
                "delta": delta,
                "meta": {"d1": d1, "d2": d2, "c1": c1, "c2": c2}
            }
            
            # Sanitize nested data
            clean_payload = {
                "type": "comparison",
                "axis": self.clean_for_json({"arr": common_dist})["arr"],
                "drivers": {
                    d1: self.clean_for_json({"arr": speed1})["arr"],
                    d2: self.clean_for_json({"arr": speed2})["arr"]
                },
                "delta": self.clean_for_json({"arr": delta})["arr"],
                "meta": {"d1": d1, "d2": d2, "c1": c1, "c2": c2}
            }
            
            self.comparison_ready.emit(clean_payload)
            
        except Exception as e:
            print(f"Alignment Error: {e}")
