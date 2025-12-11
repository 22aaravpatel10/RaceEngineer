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
    analysis_ready = pyqtSignal(dict)
    comparison_ready = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.laps = None
        self.current_map = None

    def clean_for_json(self, data):
        """Recursively sanitizes data for JSON transmission"""
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
        print(f"RaceControl: Loading {year} {country}...")
        try:
            self.session = fastf1.get_session(int(year), country, 'Q')
            self.session.load()
            self.laps = self.session.laps
            
            self.current_map = config.GRID_2025 if session_type == 'Simulation' else None
            
            ui_drivers = []
            drivers_to_scan = self.current_map.keys() if self.current_map else self.laps['Driver'].unique()
            
            for drv_id in drivers_to_scan:
                source_id = self.current_map[drv_id]['source'] if self.current_map else drv_id
                
                color = "#FFFFFF"
                team_name = "Team"
                if self.current_map:
                    team_name = self.current_map[drv_id]['team']
                    color = config.TEAM_COLORS.get(team_name, "#FFF")
                else:
                    try:
                        team_name = self.laps.pick_driver(source_id)['Team'].iloc[0]
                        color = fastf1.plotting.team_color(team_name)
                    except:
                        pass

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
                            "color": color,
                            "lap_time": lap_time,
                            "position": int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                        })
                except:
                    pass

            ui_drivers.sort(key=lambda x: x['position'])
            self.initialized.emit(ui_drivers)
            print(f"Session Ready: {len(ui_drivers)} drivers")

        except Exception as e:
            print(f"Load Error: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str, str)
    def request_analysis(self, driver_id, mode):
        if self.laps is None:
            return
        
        try:
            # 1. Identify Driver
            source_id = self.current_map[driver_id]['source'] if self.current_map else driver_id
            d_laps = self.laps.pick_driver(source_id).copy()
            
            # Get team color
            team_color = "#0A84FF"
            if self.current_map and driver_id in self.current_map:
                team_color = config.TEAM_COLORS.get(self.current_map[driver_id]['team'], "#FFF")
            else:
                try:
                    team = self.laps.pick_driver(source_id)['Team'].iloc[0]
                    team_color = fastf1.plotting.team_color(team)
                except:
                    pass
            
            # 2. PRO ALGORITHM: Classify Laps
            session_best = self.laps.pick_fastest()['LapTime']
            
            d_laps['LapType'] = 'COOL'
            d_laps.loc[d_laps['LapTime'] < session_best * 1.07, 'LapType'] = 'PUSH'
            d_laps.loc[~pd.isnull(d_laps['PitInTime']), 'LapType'] = 'IN'
            d_laps.loc[~pd.isnull(d_laps['PitOutTime']), 'LapType'] = 'OUT'

            payload = {}

            # --- PRACTICE MODE: Tire Deg Analysis (Colored by Compound) ---
            if mode == 'PRACTICE':
                stints = d_laps[d_laps['LapType'] == 'PUSH']
                if len(stints) == 0:
                    stints = d_laps[d_laps['LapTime'].notna()]
                
                # Map compound to colors
                compound_colors = {
                    'SOFT': '#FF3B30', 'MEDIUM': '#FFCC00', 'HARD': '#FFFFFF',
                    'INTERMEDIATE': '#30D158', 'WET': '#0A84FF'
                }
                colors = stints['Compound'].map(compound_colors).fillna('#888888').tolist()
                
                payload = {
                    "mode": "PRACTICE",
                    "title": f"{driver_id} Long Run Pace",
                    "x": stints['LapNumber'].tolist(),
                    "y": stints['LapTime'].dt.total_seconds().tolist(),
                    "colors": colors,
                    "compounds": stints['Compound'].tolist()
                }

            # --- QUALI MODE: Ghost Car vs Pole ---
            elif mode == 'QUALI':
                my_lap = d_laps.pick_fastest()
                my_car = my_lap.get_car_data().add_distance()
                
                # Get SESSION Fastest (Pole Sitter)
                pole_lap = self.laps.pick_fastest()
                pole_car = pole_lap.get_car_data().add_distance()
                pole_driver = pole_lap['Driver']
                
                # Align them
                max_d = min(my_car['Distance'].max(), pole_car['Distance'].max())
                dist = np.arange(0, max_d, 10)  # 10m slices
                
                my_speed = interp1d(my_car['Distance'], my_car['Speed'], fill_value="extrapolate")(dist)
                pole_speed = interp1d(pole_car['Distance'], pole_car['Speed'], fill_value="extrapolate")(dist)

                payload = {
                    "mode": "QUALI",
                    "title": f"{driver_id} vs POLE ({pole_driver})",
                    "distance": dist.tolist(),
                    "driver_speed": my_speed.tolist(),
                    "pole_speed": pole_speed.tolist(),
                    "pole_driver": pole_driver,
                    "driver_color": team_color
                }

            # --- RACE MODE: Pace Consistency (Filtered) ---
            elif mode == 'RACE':
                # Filter outliers (pit stops, slow laps)
                race_laps = d_laps[d_laps['LapTime'] < session_best * 1.15]
                race_laps = race_laps[race_laps['LapTime'].notna()]
                
                # Map compound to colors for race viz
                compound_colors = {
                    'SOFT': '#FF3B30', 'MEDIUM': '#FFCC00', 'HARD': '#FFFFFF',
                    'INTERMEDIATE': '#30D158', 'WET': '#0A84FF'
                }
                colors = race_laps['Compound'].map(compound_colors).fillna('#888888').tolist()
                
                payload = {
                    "mode": "RACE",
                    "title": f"{driver_id} Race Pace Consistency",
                    "x": race_laps['LapNumber'].tolist(),
                    "y": race_laps['LapTime'].dt.total_seconds().tolist(),
                    "colors": colors,
                    "compounds": race_laps['Compound'].tolist(),
                    "driver_color": team_color
                }

            clean = self.clean_for_json(payload)
            self.analysis_ready.emit(clean)

        except Exception as e:
            print(f"Analysis Failed: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str, str)
    def align_drivers(self, d1, d2):
        """Ghost Car Alignment for Compare command"""
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
