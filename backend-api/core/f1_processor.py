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


class F1Processor:
    """Singleton-style processor for F1 data"""
    
    def __init__(self):
        self.session = None
        self.laps = None
        self.session_info = {}
    
    def load_session(self, year: int, gp: str, session_type: str = 'Q') -> Dict:
        """Load a session and return basic info"""
        try:
            self.session = fastf1.get_session(year, gp, session_type)
            self.session.load()
            self.laps = self.session.laps
            
            # Extract driver list
            drivers = []
            for driver in self.laps['Driver'].unique():
                try:
                    d_laps = self.laps.pick_driver(driver)
                    fastest = d_laps.pick_fastest()
                    if fastest is None:
                        continue
                    
                    team = d_laps['Team'].iloc[0]
                    try:
                        color = fastf1.plotting.team_color(team)
                    except:
                        color = "#FFFFFF"
                    
                    lap_time = str(fastest['LapTime']).split('days')[-1].strip()
                    if '.' in lap_time:
                        lap_time = lap_time[:-3]
                    
                    drivers.append({
                        "code": driver,
                        "team": team,
                        "color": color,
                        "bestLap": lap_time,
                        "position": int(fastest['Position']) if pd.notna(fastest['Position']) else 99
                    })
                except Exception:
                    continue
            
            drivers.sort(key=lambda x: x['position'])
            
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
                "year": year,
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
        try:
            color = fastf1.plotting.team_color(team)
        except:
            color = "#0A84FF"
        
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
            try:
                team = d_laps['Team'].iloc[0]
                color = fastf1.plotting.team_color(team)
            except:
                color = "#FFFFFF"
            
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
            try:
                team = d_laps['Team'].iloc[0]
                color = fastf1.plotting.team_color(team)
            except:
                color = "#FFFFFF"
            
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
        try:
            t1 = self.laps.pick_driver(driver1)['Team'].iloc[0]
            c1 = fastf1.plotting.team_color(t1)
        except:
            c1 = "#0A84FF"
        try:
            t2 = self.laps.pick_driver(driver2)['Team'].iloc[0]
            c2 = fastf1.plotting.team_color(t2)
        except:
            c2 = "#FF3B30"
        
        return {
            "driver1": {"code": driver1, "color": c1, "speed": speed1.tolist()},
            "driver2": {"code": driver2, "color": c2, "speed": speed2.tolist()},
            "distance": common_dist.tolist(),
            "delta": (speed1 - speed2).tolist(),
            "corners": self.session_info.get('corners', [])
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
