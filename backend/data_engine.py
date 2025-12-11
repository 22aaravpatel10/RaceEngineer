import fastf1
import os
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# --- 1. Team Colors Constant ---
class TeamColors:
    COLORS = {
        "Red Bull Racing": "#1E41FF",   # Verstappen / Hadjar
        "Mercedes": "#00D2BE",          # Russell / Antonelli
        "Ferrari": "#FF2800",           # Leclerc / Hamilton
        "McLaren": "#FF8000",           # Norris / Piastri
        "Aston Martin": "#006F62",      # Alonso / Stroll
        "Alpine": "#0090FF",            # Gasly / Colapinto
        "Williams": "#005AFF",          # Sainz / Albon
        "VCARB": "#6692FF",             # Lawson / Lindblad
        "Haas": "#B6BABD",              # Ocon / Bearman
        "Audi": "#FF3B00",              # Hulkenberg / Bortoleto (Neon Red/Grey)
        "Cadillac": "#D4AF37",          # Bottas / Perez (Gold/Black)
    }

    @staticmethod
    def get_color(team_name: str) -> str:
        return TeamColors.COLORS.get(team_name, "#FFFFFF") # Default white

# --- 2. Micro-Sector Logic ---
class MicroSectorCalculator:
    def __init__(self, track_x: np.array, track_y: np.array, n_sectors: int = 25):
        self.track_x = track_x
        self.track_y = track_y
        self.n_sectors = n_sectors
        self.sector_indices = self._calculate_sector_indices()

    def _calculate_sector_indices(self) -> np.array:
        # Simple distance-based slicing for now
        # In a real implementation, we would map distance along track
        total_points = len(self.track_x)
        return np.linspace(0, total_points, self.n_sectors + 1, dtype=int)

    def calculate_sector_deltas(self, measured_lap_time: pd.Series, session_best_time: pd.Series) -> List[float]:
        # Placeholder logic: compute delta for chunks
        # This requires more complex interpolation in a full implementation
        return [0.0] * self.n_sectors

# --- 3. Session Detection ---
class SessionDetector:
    @staticmethod
    def detect_mode(session_name: str) -> str:
        name_lower = session_name.lower()
        if "test" in name_lower or "shakedown" in name_lower:
            return "TEST_DAY"
        return "RACE_WEEKEND"

    @staticmethod
    def calculate_consistency_score(lap_times: List[float]) -> float:
        if not lap_times:
            return 0.0
        return float(np.std(lap_times))

# --- 4. Main Data Engine ---
class DataEngine:
    def __init__(self):
        self._cache = {}
        # Ensure cache directory exists
        if not os.path.exists('cache'):
            os.makedirs('cache')
        # Enable FastF1 cache
        fastf1.Cache.enable_cache('cache') 

    def get_dummy_telemetry(self, driver: str, lap: int) -> Dict[str, Any]:
        """
        Returns dummy data for UI testing before full API integration.
        """
        return {
            "driver": driver,
            "lap": lap,
            "speed": [200, 205, 210, 215, 220, 210, 200], # Fake trace
            "rpm": [10000, 10500, 11000, 11500, 12000, 11000, 10000],
            "microSectors": [0.1, -0.2, 0.0, 0.3, -0.1] * 5, # 25 sectors
        }
