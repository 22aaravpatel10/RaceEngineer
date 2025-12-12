"""
FastF1 Data Processor - The Brain
Handles all F1 data fetching and processing
"""
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from typing import Optional, Dict, List, Any


from core.config import get_team_color
from core.analysis_engine import analysis_engine

class F1Processor:
    """Singleton-style processor for F1 data"""
    
    def __init__(self):
        self.session = None
        self.laps = None
        self.session_info = {}
    
    def get_seasons(self) -> List[int]:
        """Return supported seasons"""
        return [2023, 2024, 2025]
        
    def get_races(self, year: int) -> List[Dict]:
        """Return list of races for a given year"""
        try:
            schedule = fastf1.get_event_schedule(year)
            races = []
            for _, event in schedule.iterrows():
                # Filter out testing sessions if needed, though they are useful
                if event['EventName'] == "Pre-Season Testing":
                    continue
                    
                races.append({
                    "round": int(event['RoundNumber']),
                    "name": event['EventName'],
                    "location": event['Location'],
                    "date": str(event['EventDate'].date())
                })
            return races
        except Exception as e:
            return []

    
    def load_session(self, year: int, gp: str, session_type: str = 'R') -> Dict:
        """Load a session and return basic info"""
        try:
            # --- 2025 SIMULATION LOGIC ---
            # If requesting 2025/2026, we simulate using 2023 data
            target_year = year
            is_simulation = False
            
            if year >= 2025:
                # Import here to avoid circular dependencies if any (though config is safe)
                from core.config import GRID_2025, TEAM_COLORS
                target_year = 2023
                is_simulation = True
            
            # Handle aliases for GP names if needed, or rely on FastF1's fuzzy match
            self.session = fastf1.get_session(target_year, gp, session_type)
            self.session.load()
            self.laps = self.session.laps
            
            # If Simulation, Patch the DataFrame
            if is_simulation:
                # Create map: Source(2023) -> New(2025)
                # GRID_2025 is { "LAW": {"source": "PER", ...}, ... }
                source_to_new = {v['source']: k for k, v in GRID_2025.items()}
                
                # We need to preserve drivers who are NOT in the map? 
                # The map should cover the grid. If a 2023 driver isn't in the map (e.g. SAR), 
                # they might be mapped to someone (SAI).
                # If a driver has no mapping, they disappear or keep orig name? 
                # Better to keep original if not mapped to avoid crashes, but identifying them might be confusing.
                
                # Apply mapping to 'Driver' column
                # Use a function to handle missing keys comfortably
                self.laps['Driver'] = self.laps['Driver'].apply(lambda x: source_to_new.get(x, x))
                
                # Also update Teams if needed?
                # The GRID_2025 has "team" info. We should update the 'Team' column too.
                # New(2025) -> Team
                new_to_team = {k: v['team'] for k, v in GRID_2025.items()}
                
                # Now that Driver column is updated to NEW names, we can map to Teams
                self.laps['Team'] = self.laps['Team'] # Keep original first
                # Iterate and update (vectorized would be better but this is safe)
                for new_driver, new_team in new_to_team.items():
                    self.laps.loc[self.laps['Driver'] == new_driver, 'Team'] = new_team

            
            # Extract driver list
            drivers = []
            for driver in self.laps['Driver'].unique():
                try:
                    d_laps = self.laps.pick_driver(driver)
                    # Use 'pick_fastest' carefully - if session is just starting it might be empty
                    # For a generic list, we just need the driver info
                    
                    team = d_laps['Team'].iloc[0] if not d_laps.empty else "Unknown"
                    color = get_team_color(team)
                    
                    best_time = "N/A"
                    best_time_val = float('inf')
                    position = 99
                    
                    if not d_laps.empty:
                        fastest = d_laps.pick_fastest()
                        if fastest is not None and pd.notna(fastest['LapTime']):
                            best_time_val = fastest['LapTime'].total_seconds()
                            lap_time = str(fastest['LapTime']).split('days')[-1].strip()
                            if '.' in lap_time:
                                lap_time = lap_time[:-3]
                            best_time = lap_time
                            position = int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                    
                    drivers.append({
                        "code": driver,
                        "team": team,
                        "color": color,
                        "bestLap": best_time,
                        "position": position,
                        "bestLapVal": best_time_val
                    })
                except Exception:
                    continue
            
            # Sort by Best Lap Time (fastest first), then by Position as fallback
            drivers.sort(key=lambda x: (x['bestLapVal'], x['position']))
            
            # Extract circuit info
            corners = []
            try:
                circuit_info = self.session.get_circuit_info()
                if circuit_info is not None:
                    for _, corner in circuit_info.corners.iterrows():
                        corners.append({
                            "number": int(corner['Number']),
                            "distance": float(corner['Distance'])
                        })
            except:
                pass
            
            self.session_info = {
                "year": year, # Report the REQUESTED year
                "gp": gp,
                "sessionType": session_type,
                "eventName": self.session.event['EventName'],
                "circuitName": self.session.event.get('Location', gp),
                "drivers": drivers,
                "corners": corners,
                "totalLaps": int(self.laps['LapNumber'].max()) if len(self.laps) > 0 else 0
            }
            
            return self.session_info
            
        except Exception as e:
            raise Exception(f"Failed to load session: {str(e)}")
    
    def get_driver_laps(self, driver_code: str) -> List[Dict]:
        """Get all laps for a driver with metadata"""
        if self.laps is None:
            raise Exception("No session loaded")
        
        d_laps = self.laps.pick_driver(driver_code)
        result = []
        
        for _, lap in d_laps.iterrows():
            if pd.isna(lap['LapTime']):
                continue
            
            lap_time_sec = lap['LapTime'].total_seconds()
            
            # Sector times
            s1 = lap['Sector1Time'].total_seconds() if pd.notna(lap['Sector1Time']) else None
            s2 = lap['Sector2Time'].total_seconds() if pd.notna(lap['Sector2Time']) else None
            s3 = lap['Sector3Time'].total_seconds() if pd.notna(lap['Sector3Time']) else None
            
            result.append({
                "lapNumber": int(lap['LapNumber']),
                "lapTime": lap_time_sec,
                "sector1": s1,
                "sector2": s2,
                "sector3": s3,
                "compound": lap['Compound'] if pd.notna(lap['Compound']) else "UNKNOWN",
                "tyreLife": int(lap['TyreLife']) if pd.notna(lap['TyreLife']) else 0,
                "isPersonalBest": bool(lap['IsPersonalBest']) if pd.notna(lap['IsPersonalBest']) else False,
                "isPitOut": pd.notna(lap['PitOutTime']),
                "isPitIn": pd.notna(lap['PitInTime'])
            })
        
        return result
    
    def get_lap_telemetry(self, driver_code: str, lap_number: int) -> Dict:
        """Get granular telemetry for a specific lap"""
        if self.laps is None:
            raise Exception("No session loaded")
        
        d_laps = self.laps.pick_driver(driver_code)
        lap = d_laps[d_laps['LapNumber'] == lap_number].iloc[0]
        
        car = lap.get_car_data().add_distance()
        
        # Get team color
        team = d_laps['Team'].iloc[0]
        color = get_team_color(team)
        
        # Calculate braking zones
        car['Braking'] = (car['Brake'] > 0) & (car['Throttle'] < 10)
        braking_zones = []
        is_braking = False
        start_dist = 0
        
        for _, row in car.iterrows():
            if row['Braking'] and not is_braking:
                is_braking = True
                start_dist = row['Distance']
            elif not row['Braking'] and is_braking:
                is_braking = False
                if row['Distance'] - start_dist > 10:
                    braking_zones.append([float(start_dist), float(row['Distance'])])
        
        return {
            "driver": driver_code,
            "lapNumber": lap_number,
            "color": color,
            "distance": self._clean_array(car['Distance']),
            "speed": self._clean_array(car['Speed']),
            "throttle": self._clean_array(car['Throttle']),
            "brake": self._clean_array(car['Brake'].astype(int)),
            "rpm": self._clean_array(car['RPM']),
            "gear": self._clean_array(car['nGear']),
            "drs": self._clean_array(car['DRS']) if 'DRS' in car.columns else [],
            "brakingZones": braking_zones,
            "corners": self.session_info.get('corners', [])
        }
    
    def get_race_gaps(self) -> Dict:
        """Get gap to leader evolution (for Race sessions)"""
        if self.laps is None:
            raise Exception("No session loaded")
        
        drivers = self.laps['Driver'].unique()
        result = {"drivers": {}, "maxLap": 0}
        
        for driver in drivers:
            d_laps = self.laps.pick_driver(driver)
            gaps = []
            
            for _, lap in d_laps.iterrows():
                if pd.isna(lap['LapNumber']):
                    continue
                gaps.append({
                    "lap": int(lap['LapNumber']),
                    "position": int(lap['Position']) if pd.notna(lap['Position']) else None,
                    "gapToLeader": float(lap['GapToLeader']) if pd.notna(lap.get('GapToLeader')) else None
                })
            
            # Get color
            team = d_laps['Team'].iloc[0]
            color = get_team_color(team)
            
            result["drivers"][driver] = {
                "gaps": gaps,
                "color": color
            }
            
            if gaps:
                result["maxLap"] = max(result["maxLap"], max(g['lap'] for g in gaps))
        
        return result
    
    def get_pit_stops(self) -> List[Dict]:
        """Get pit stop strategy data"""
        if self.laps is None:
            raise Exception("No session loaded")
        
        drivers = self.laps['Driver'].unique()
        result = []
        
        for driver in drivers:
            d_laps = self.laps.pick_driver(driver)
            d_laps = d_laps.sort_values('LapNumber')
            
            # Group consecutive laps by compound
            stints = []
            current_compound = None
            stint_start = None
            
            for _, lap in d_laps.iterrows():
                compound = lap['Compound'] if pd.notna(lap['Compound']) else 'UNKNOWN'
                lap_num = int(lap['LapNumber'])
                
                if compound != current_compound:
                    if current_compound is not None:
                        stints.append({
                            "compound": current_compound,
                            "startLap": stint_start,
                            "endLap": lap_num - 1
                        })
                    current_compound = compound
                    stint_start = lap_num
            
            # Close last stint
            if current_compound is not None:
                stints.append({
                    "compound": current_compound,
                    "startLap": stint_start,
                    "endLap": int(d_laps['LapNumber'].max())
                })
            
            # Get color
            team = d_laps['Team'].iloc[0]
            color = get_team_color(team)
            
            result.append({
                "driver": driver,
                "color": color,
                "stints": stints
            })
        
        return result
    
    def compare_drivers(self, driver1: str, driver2: str) -> Dict:
        """Compare two drivers' fastest laps"""
        if self.laps is None:
            raise Exception("No session loaded")
        
        lap1 = self.laps.pick_driver(driver1).pick_fastest()
        lap2 = self.laps.pick_driver(driver2).pick_fastest()
        
        car1 = lap1.get_car_data().add_distance()
        car2 = lap2.get_car_data().add_distance()
        
        # Align to common distance
        max_dist = min(car1['Distance'].max(), car2['Distance'].max())
        common_dist = np.arange(0, max_dist, 10)
        
        speed1 = interp1d(car1['Distance'], car1['Speed'], fill_value="extrapolate")(common_dist)
        speed2 = interp1d(car2['Distance'], car2['Speed'], fill_value="extrapolate")(common_dist)
        
        # Get colors
        t1 = self.laps.pick_driver(driver1)['Team'].iloc[0]
        c1 = get_team_color(t1)
        
        t2 = self.laps.pick_driver(driver2)['Team'].iloc[0]
        c2 = get_team_color(t2)
        
        return {
            "driver1": {"code": driver1, "color": c1, "speed": speed1.tolist()},
            "driver2": {"code": driver2, "color": c2, "speed": speed2.tolist()},
            "distance": common_dist.tolist(),
            "delta": (speed1 - speed2).tolist(),
            "corners": self.session_info.get('corners', [])
        }
    
    
    def get_fuel_corrected_laps(self, driver_code: str) -> List[Dict]:
        """Get actual vs fuel corrected lap times"""
        if self.laps is None:
            raise Exception("No session loaded")
            
        d_laps = self.laps.pick_driver(driver_code)
        return analysis_engine.calculate_fuel_correction(d_laps)
        
    def get_race_gaps_v2(self) -> Dict:
        """Get advanced gap analysis (The Worm)"""
        if self.laps is None:
            raise Exception("No session loaded")
            
        drivers = self.laps['Driver'].unique()
        gaps_data = analysis_engine.calculate_race_gaps(self.laps, drivers)
        
        # Format for frontend (add colors)
        result = []
        for drv in drivers:
            if drv not in gaps_data:
                continue
                
            color = get_team_color(self.laps.pick_driver(drv)['Team'].iloc[0])
            result.append({
                "driver": drv,
                "color": color,
                "data": gaps_data[drv]
            })
            
        return result
        
    def get_ghost_trace(self, driver1: str, driver2: str) -> Dict:
        """Get ghost delta trace"""
        if self.laps is None:
            raise Exception("No session loaded")
            
        lap1 = self.laps.pick_driver(driver1).pick_fastest()
        lap2 = self.laps.pick_driver(driver2).pick_fastest()
        
        if lap1 is None or lap2 is None:
            raise Exception("One of the drivers has no laps")
            
        tel1 = lap1.get_car_data().add_distance().add_relative_distance()
        # We need 'Time' column in car data? 'get_car_data' returns Time indexed? 
        # Actually fastf1 telemetry Time is the index or a column depending.
        # usually we need to merge with lap start time? 
        # Wait, get_car_data returns telemetry relative to LAP START. So Time starts at 0.
        # However, fastf1 car data 'Time' column is a Timedelta.
        
        # Check if Time is in columns
        if 'Time' not in tel1.columns:
             tel1['Time'] = tel1.index # If indexed by time
        
        tel2 = lap2.get_car_data().add_distance().add_relative_distance()
        if 'Time' not in tel2.columns:
             tel2['Time'] = tel2.index

        delta_data = analysis_engine.calculate_ghost_delta(tel1, tel2)
        
        return {
            "driver1": driver1,
            "driver2": driver2,
            "distance": delta_data.get('distance', []),
            "delta": delta_data.get('delta', [])
        }

    def _clean_array(self, arr) -> List:
        """Clean numpy/pandas arrays for JSON"""
        result = []
        for x in arr.tolist():
            if pd.isna(x):
                result.append(None)
            elif isinstance(x, (np.floating, np.integer)):
                result.append(float(x))
            else:
                result.append(x)
        return result


# Global processor instance
processor = F1Processor()
