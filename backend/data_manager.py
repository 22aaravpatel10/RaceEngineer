import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import requests
from scipy.interpolate import interp1d
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import config

# --- HELPER: OpenF1 Client ---
class OpenF1Client:
    BASE_URL = "https://api.openf1.org/v1"
    
    @staticmethod
    def get_sessions(year=2024):
        try:
            url = f"{OpenF1Client.BASE_URL}/sessions?year={year}"
            response = requests.get(url, timeout=10)
            data = response.json()
            # Filter distinct meaningful sessions
            seen = set()
            clean = []
            for s in data:
                uid = f"{s.get('country_name', '')}-{s.get('session_name', '')}"
                if uid not in seen and s.get('session_name') in ['Qualifying', 'Race', 'Practice 1', 'Practice 2', 'Practice 3', 'Sprint']:
                    seen.add(uid)
                    clean.append(s)
            clean.sort(key=lambda x: x.get('date_start', ''), reverse=True)
            return clean
        except Exception as e:
            print(f"OpenF1 Error: {e}")
            return []


# --- MAIN WORKER ---
class RaceControlWorker(QObject):
    initialized = pyqtSignal(list)
    telemetry_ready = pyqtSignal(dict)
    analysis_ready = pyqtSignal(dict)  # New Signal for Mode Data
    comparison_ready = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.laps = None
        self.current_map = None

    def clean_for_json(self, data):
        """Sanitizes numpy/NaNs for JSON safety"""
        if isinstance(data, dict):
            return {k: self.clean_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_for_json(i) for i in data]
        elif isinstance(data, (np.ndarray, pd.Series)):
            return [None if pd.isna(x) else (float(x) if isinstance(x, (np.floating, np.integer)) else x) for x in data.tolist()]
        elif isinstance(data, (np.floating, np.integer)):
            return float(data)
        elif pd.isna(data):
            return None
        return data

    @pyqtSlot(str, str, str)
    def load_session(self, year, country, session_type):
        print(f"RaceControl: Loading {year} {country} [{session_type}]...")
        try:
            # 1. Load Session
            self.session = fastf1.get_session(int(year), country, 'Q')
            self.session.load()
            self.laps = self.session.laps
            
            # 2. Apply "Simulation" Map if requested
            self.current_map = config.GRID_2025 if session_type == 'Simulation' else None
            
            # 3. Generate Grid List
            ui_drivers = []
            drivers_to_scan = self.current_map.keys() if self.current_map else self.laps['Driver'].unique()
            
            for drv_id in drivers_to_scan:
                source_id = self.current_map[drv_id]['source'] if self.current_map else drv_id
                team_color = "#FFFFFF"
                team_name = "F1 Team"
                
                # Get Color
                if self.current_map:
                    team_name = self.current_map[drv_id]['team']
                    team_color = config.TEAM_COLORS.get(team_name, "#FFF")
                else:
                    try:
                        team_name = self.laps.pick_driver(source_id)['Team'].iloc[0]
                        team_color = fastf1.plotting.team_color(team_name)
                    except:
                        pass

                # Get Best Lap
                try:
                    d_laps = self.laps.pick_driver(source_id)
                    fastest = d_laps.pick_fastest()
                    if fastest is not None and pd.notna(fastest['LapTime']):
                        lap_time = str(fastest['LapTime']).split('days')[-1].strip()
                        if '.' in lap_time:
                            lap_time = lap_time[:-3]
                        ui_drivers.append({
                            "id": drv_id,
                            "team": team_name,
                            "color": team_color,
                            "lap_time": lap_time,
                            "position": int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                        })
                except:
                    pass

            ui_drivers.sort(key=lambda x: x['position'])
            self.initialized.emit(ui_drivers)
            print(f"Session Ready: {len(ui_drivers)} drivers")

        except Exception as e:
            print(f"Load Failed: {e}")
            import traceback
            traceback.print_exc()

    # --- THE ALGORITHM ENGINE ---
    @pyqtSlot(str, str)
    def request_analysis(self, driver_id, mode):
        """
        Generates specific charts based on Session Mode.
        mode: 'PRACTICE', 'QUALI', 'RACE'
        """
        if self.laps is None:
            return
        
        try:
            # 1. Resolve Source Driver
            source_id = driver_id
            team_color = "#0A84FF"
            if self.current_map and driver_id in self.current_map:
                source_id = self.current_map[driver_id]['source']
                team_color = config.TEAM_COLORS.get(self.current_map[driver_id]['team'], "#FFF")
            else:
                try:
                    team = self.laps.pick_driver(source_id)['Team'].iloc[0]
                    team_color = fastf1.plotting.team_color(team)
                except:
                    pass
            
            # 2. Get All Laps for Driver
            d_laps = self.laps.pick_driver(source_id).copy()
            
            # 3. RUN ALGORITHM: Classify Laps
            fastest = d_laps.pick_fastest()
            if fastest is None:
                return
                
            pb_time = fastest['LapTime']
            
            # Logic Mask
            d_laps['LapType'] = 'SLOW'
            # 107% Rule for Push
            push_threshold = pb_time * 1.07
            d_laps.loc[d_laps['LapTime'] < push_threshold, 'LapType'] = 'PUSH'
            d_laps.loc[~pd.isnull(d_laps['PitInTime']), 'LapType'] = 'IN'
            d_laps.loc[~pd.isnull(d_laps['PitOutTime']), 'LapType'] = 'OUT'

            payload = {}

            # --- MODE 1: PRACTICE (Stint Analysis) ---
            if mode == 'PRACTICE':
                stint_data = d_laps[d_laps['LapType'] == 'PUSH']
                if len(stint_data) == 0:
                    stint_data = d_laps[d_laps['LapTime'].notna()]
                    
                payload = {
                    "mode": "PRACTICE",
                    "title": f"{driver_id} Long Run Pace",
                    "x": stint_data['LapNumber'].tolist(),
                    "y": stint_data['LapTime'].dt.total_seconds().tolist(),
                    "color": team_color
                }

            # --- MODE 2: QUALI (The Perfect Lap) ---
            elif mode == 'QUALI':
                car = fastest.get_car_data().add_distance()
                payload = {
                    "mode": "QUALI",
                    "title": f"{driver_id} Qualifying Trace",
                    "distance": car['Distance'].tolist(),
                    "speed": car['Speed'].tolist(),
                    "throttle": car['Throttle'].tolist(),
                    "gear": car['nGear'].tolist(),
                    "color": team_color
                }

            # --- MODE 3: RACE (Gap Evolution) ---
            elif mode == 'RACE':
                session_mean = self.laps.pick_fastest()['LapTime'].total_seconds()
                d_laps_valid = d_laps[d_laps['LapTime'].notna()].copy()
                d_laps_valid['PaceDelta'] = d_laps_valid['LapTime'].dt.total_seconds() - session_mean
                d_laps_valid['GapTrend'] = d_laps_valid['PaceDelta'].cumsum()
                
                payload = {
                    "mode": "RACE",
                    "title": f"{driver_id} Race Pace Trend",
                    "x": d_laps_valid['LapNumber'].tolist(),
                    "y": d_laps_valid['GapTrend'].tolist(),
                    "color": team_color
                }

            # Clean & Send
            clean_payload = self.clean_for_json(payload)
            self.analysis_ready.emit(clean_payload)

        except Exception as e:
            print(f"Analysis Error: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str)
    def fetch_telemetry(self, driver_id):
        """Fetch telemetry for a single driver (legacy support)"""
        # Redirect to QUALI mode by default
        self.request_analysis(driver_id, 'QUALI')

    @pyqtSlot(str, str)
    def align_drivers(self, d1, d2):
        """Ghost Car Alignment"""
        if self.laps is None:
            return
        
        try:
            s1 = self.current_map[d1]['source'] if self.current_map and d1 in self.current_map else d1
            s2 = self.current_map[d2]['source'] if self.current_map and d2 in self.current_map else d2
            
            l1 = self.laps.pick_driver(s1).pick_fastest().get_car_data().add_distance()
            l2 = self.laps.pick_driver(s2).pick_fastest().get_car_data().add_distance()
            
            max_d = min(l1['Distance'].max(), l2['Distance'].max())
            common_dist = np.arange(0, max_d, 5)
            
            speed1 = interp1d(l1['Distance'], l1['Speed'], fill_value="extrapolate")(common_dist)
            speed2 = interp1d(l2['Distance'], l2['Speed'], fill_value="extrapolate")(common_dist)
            
            delta = speed1 - speed2
            
            c1 = config.TEAM_COLORS.get(self.current_map[d1]['team'], "#1E41FF") if self.current_map else "#1E41FF"
            c2 = config.TEAM_COLORS.get(self.current_map[d2]['team'], "#FF2800") if self.current_map else "#FF2800"
            
            payload = {
                "type": "comparison",
                "axis": common_dist.tolist(),
                "drivers": {
                    d1: speed1.tolist(),
                    d2: speed2.tolist()
                },
                "delta": delta.tolist(),
                "meta": {"d1": d1, "d2": d2, "c1": c1, "c2": c2}
            }
            
            clean_payload = self.clean_for_json(payload)
            self.comparison_ready.emit(clean_payload)
            
        except Exception as e:
            print(f"Alignment Error: {e}")
