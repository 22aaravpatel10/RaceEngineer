import fastf1
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
import logging
import os
import requests

# --- Cache Setup (Robust) ---
# Create a cache folder next to the app as requested
CACHE_DIR = os.path.join(os.getcwd(), 'f1_cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

try:
    fastf1.Cache.enable_cache(CACHE_DIR)
    logging.info(f"FastF1 cache enabled at: {CACHE_DIR}")
except Exception as e:
    logging.warning(f"Could not enable FastF1 cache: {e}")


class OpenF1Client:
    """
    Tier 2: Live Data Polling via OpenF1.
    """
    BASE_URL = "https://api.openf1.org/v1"
    # Strict User-Agent to avoid blocking
    HEADERS = {'User-Agent': 'OvercutApp/1.0'}

    @staticmethod
    def get_latest_session():
        try:
            # Poll for the latest session associated with the latest meeting
            url = f"{OpenF1Client.BASE_URL}/sessions?meeting_key=latest"
            response = requests.get(url, headers=OpenF1Client.HEADERS, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                # OpenF1 returns a list. The last item is typically the most recent session.
                return data[-1]
            return None
        except Exception as e:
            logging.error(f"OpenF1 API Error: {e}")
            return None


class MockDataManager:
    """
    Fallback data generator for testing or offline modes.
    Generates consistent sine-wave based telemetry.
    """
    def get_telemetry(self, driver: str) -> dict:
        distance = np.linspace(0, 5000, 100) # 5km track
        
        # Consistent "Seed" based on driver name length to keep curves stable per driver
        seed = len(driver) 
        speed = 200 + 100 * np.sin(distance / 500 + seed) + np.random.normal(0, 2, 100)
        throttle = 50 + 50 * np.sin(distance / 500 + seed)
        throttle = np.clip(throttle, 0, 100)
        
        return {
            "driver": driver,
            "distance": distance.tolist(),
            "speed": speed.tolist(),
            "throttle": throttle.tolist(),
            "rpm": (speed * 50).tolist(),
            "gear": np.clip(speed // 40, 1, 8).tolist()
        }


class DataManager(QObject):
    """
    Tier 2: background Data Engine.
    Handles FastF1 integration, interpolation (Ghost Car), and Metric calculation.
    """
    data_ready = pyqtSignal(dict)
    session_status_updated = pyqtSignal(dict) # Signal for Dynamic Island
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mock = MockDataManager()
        self.use_mock = True # Default to mock for safety until reliable
        
        # Setup Live Polling Timer (10s interval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_live_status)
        self.timer.start(10000) 
        
        # Poll immediately on start
        self.poll_live_status()

    def poll_live_status(self):
        """
        Polls OpenF1 for the current session details.
        """
        session = OpenF1Client.get_latest_session()
        if session:
            # Extract info for Dynamic Island
            # Example: "Practice 1" - "Monza"
            name = session.get('session_name', 'Session')
            meeting = session.get('meeting_name', '') # Might not always be present or requires join
            short_name = name[:3].upper() + " - " + ("LIVE" if True else "END") # Simplification
            
            # Since we don't have exact "Green/Red" flag from this endpoint easily without logic,
            # we just send the name.
            payload = {
                "type": "status",
                "text": f"{name.upper()}",
                "flag": "GREEN" 
            }
            self.session_status_updated.emit(payload)
        else:
            # Fallback or keep silent
            pass

    def _get_session(self, session_id="last"):
        # Wrapper to get session safely
        try:
            # SAFETY FALLBACK: Hardcode a known good session if 'latest' fails standard fastf1 logic
            # session = fastf1.get_session(2023, 'Monza', 'Q') 
            
            # Trying to get latest event's qualifying for variety if cached, else Monza
            session = fastf1.get_session(2023, 'VisualisationTest', 'Q') # Using a test session or Monza
            # Let's stick to the user's suggestion:
            session = fastf1.get_session(2023, 'Monza', 'Q')
            
            session.load()
            return session
        except Exception as e:
            print(f"API Error: {e}")
            return None

    @pyqtSlot(str, str)
    def align_telemetry(self, driver_a: str, driver_b: str):
        """
        The 'Ghost Car' Algorithm.
        Aligns two drivers by Distance, not Time.
        """
        if self.use_mock:
            self._process_mock_alignment(driver_a, driver_b)
            return

        try:
            session = self._get_session()
            if not session:
                raise Exception("Session Load Failed")

            # Pick fastest laps
            laps_a = session.laps.pick_driver(driver_a).pick_fastest()
            laps_b = session.laps.pick_driver(driver_b).pick_fastest()
            
            if laps_a is None or laps_b is None:
                 raise Exception(f"Telem not found for {driver_a} or {driver_b}")

            tel_a = laps_a.get_car_data().add_distance()
            tel_b = laps_b.get_car_data().add_distance()

            # 1. Create Common Distance Vector
            max_dist = min(tel_a['Distance'].max(), tel_b['Distance'].max())
            common_dist = np.arange(0, max_dist, 5) # 5m resolution

            # 2. Interpolate Driver A
            speed_a_func = interp1d(tel_a['Distance'], tel_a['Speed'], kind='linear', fill_value="extrapolate")
            speed_a_interp = speed_a_func(common_dist)

            # 3. Interpolate Driver B
            speed_b_func = interp1d(tel_b['Distance'], tel_b['Speed'], kind='linear', fill_value="extrapolate")
            speed_b_interp = speed_b_func(common_dist)

            # 4. Calculate Delta
            speed_delta = speed_a_interp - speed_b_interp

            payload = {
                "type": "comparison",
                "axis": common_dist.tolist(),
                "drivers": {
                    driver_a: speed_a_interp.tolist(),
                    driver_b: speed_b_interp.tolist()
                },
                "delta": speed_delta.tolist(),
                "meta": {"d1": driver_a, "d2": driver_b}
            }
            self.data_ready.emit(payload)

        except Exception as e:
            print(f"Alignment Error: {e}. Falling back to Mock.")
            self._process_mock_alignment(driver_a, driver_b)

    def _process_mock_alignment(self, d1, d2):
        print(f"Generating Mock Alignment for {d1} vs {d2}")
        data1 = self.mock.get_telemetry(d1)
        data2 = self.mock.get_telemetry(d2)
        
        # Mock Delta
        delta = np.array(data1['speed']) - np.array(data2['speed'])
        
        payload = {
            "type": "comparison",
            "axis": data1['distance'],
            "drivers": {
                d1: data1['speed'],
                d2: data2['speed']
            },
            "delta": delta.tolist(),
            "meta": {"d1": d1, "d2": d2}
        }
        self.data_ready.emit(payload)

    @staticmethod
    def calculate_battery_proxy(df: pd.DataFrame) -> pd.Series:
        mask = (df['Speed'] > 280) & (df['Throttle'] > 95) 
        return mask.astype(int)


class SessionManager:
    """
    The Time Machine: Loads historical session but relabels for 2025 Grid.
    """
    def __init__(self):
        self.current_session = None
        self.laps = None
        # Import here to avoid circular imports at module level
        from config import SIMULATION_MAP, TEAM_COLORS
        self.SIMULATION_MAP = SIMULATION_MAP
        self.TEAM_COLORS = TEAM_COLORS

    def load_simulation_2025(self):
        """Loads Abu Dhabi 2023 but relabels it as 2025"""
        print("Loading Simulation Protocol: Abu Dhabi 2023 -> 2025...")
        
        try:
            # 1. Load the 'Base' Session (Real Data)
            session = fastf1.get_session(2023, 'Abu Dhabi', 'Q') # Quali is best for clean data
            session.load()
            
            self.current_session = session
            self.laps = session.laps
            
            # 2. Build the "Fake" Driver List for the UI
            driver_list = []
            
            for new_driver, sim_data in self.SIMULATION_MAP.items():
                # Find the "Source" driver's best lap
                source_code = sim_data["source_driver"]
                
                # Check if source driver exists in the 2023 data
                if source_code in self.laps['Driver'].unique():
                    source_lap = self.laps.pick_driver(source_code).pick_fastest()
                    
                    if source_lap is not None:
                        # Create the 2025 Driver Object
                        lap_time_str = str(source_lap['LapTime']).split('days')[-1].strip()
                        driver_info = {
                            "id": new_driver,
                            "team": sim_data["team"],
                            "color": self.TEAM_COLORS.get(sim_data["team"], "#FFFFFF"),
                            "lap_time": lap_time_str,
                            "position": str(source_lap['Position']) if pd.notna(source_lap['Position']) else "N/A"
                        }
                        driver_list.append(driver_info)
            
            # Sort by lap time (fastest first)
            driver_list.sort(key=lambda x: x['lap_time'])
            print(f"Loaded {len(driver_list)} simulated 2025 drivers.")
            return driver_list
            
        except Exception as e:
            print(f"Simulation Load Error: {e}")
            return []

    def get_telemetry_for_driver(self, driver_id):
        """
        If UI asks for 'HAM' (Ferrari), we actually fetch 'SAI' (Ferrari 2023)
        but return it labeled as HAM.
        """
        if driver_id in self.SIMULATION_MAP:
            try:
                real_source_driver = self.SIMULATION_MAP[driver_id]["source_driver"]
                laps = self.current_session.laps.pick_driver(real_source_driver)
                fastest = laps.pick_fastest()
                
                if fastest is None:
                    return None
                    
                car_data = fastest.get_car_data().add_distance()
                
                return {
                    "driver": driver_id,
                    "distance": car_data['Distance'].tolist(),
                    "speed": car_data['Speed'].tolist(),
                    "throttle": car_data['Throttle'].tolist(),
                    "brake": car_data['Brake'].tolist(),
                    "gear": car_data['nGear'].tolist(),
                    "rpm": car_data['RPM'].tolist()
                }
            except Exception as e:
                print(f"Telemetry fetch error for {driver_id}: {e}")
                return None
        return None
