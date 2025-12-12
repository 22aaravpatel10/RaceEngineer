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
        """Return list of races for a given year with available sessions"""
        try:
            schedule = fastf1.get_event_schedule(year)
            races = []
            for _, event in schedule.iterrows():
                if event['EventName'] == "Pre-Season Testing":
                    continue
                
                # Extract available sessions
                sessions = []
                # Check Session1..5
                for i in range(1, 6):
                    sess_name = event.get(f'Session{i}')
                    if not sess_name or pd.isna(sess_name):
                        continue
                    
                    # Map to code
                    code = self._map_session_name(sess_name)
                    if code:
                        sessions.append(code)
                    
                races.append({
                    "round": int(event['RoundNumber']),
                    "name": event['EventName'],
                    "location": event['Location'],
                    "date": str(event['EventDate'].date()),
                    "sessions": sessions
                })
            return races
        except Exception as e:
            print(f"Error getting races: {e}")
            return []

    def _map_session_name(self, name: str) -> Optional[str]:
        """Map FastF1 session name to API code"""
        name = str(name).lower()
        if "practice 1" in name: return "FP1"
        if "practice 2" in name: return "FP2"
        if "practice 3" in name: return "FP3"
        if "sprint shootout" in name or "sprint qualifying" in name: return "SS"
        if "sprint" in name: return "S" # Careful, "Sprint Shootout" contains "Sprint"
        if "qualifying" in name: return "Q"
        if "race" in name: return "R"
        return None

    def get_lap_distribution(self) -> Dict:
        """Get lap time distribution for box plots"""
        if self.laps is None:
            raise Exception("No session loaded")
        
        print(f"Calculating Consistency for {len(self.laps)} laps...")
            
        # Filter for valid racing laps (exclude in/out laps and slow laps)
        try:
            clean_laps = self.laps.pick_quicklaps()
        except:
             # Fallback if pick_quicklaps fails (e.g. no valid laps)
             clean_laps = self.laps
             
        drivers = clean_laps['Driver'].unique()
        result = []
        
        for driver in drivers:
            d_laps = clean_laps.pick_driver(driver)
            if d_laps.empty:
                continue
                
            team = d_laps['Team'].iloc[0]
            color = get_team_color(team)
            
            # Convert to seconds and remove NaNs
            times = d_laps['LapTime'].dt.total_seconds().dropna().tolist()
            
            # Remove extreme outliers manually if needed (e.g. > 107% of best)
            # relying on pick_quicklaps for now
            
            if times:
                result.append({
                    "driver": driver,
                    "color": color,
                    "lapTimes": times
                })
        
        print(f"Found consistency data for {len(result)} drivers")
            
        # Sort by median lap time (fastest drivers on left/top)
        result.sort(key=lambda x: np.median(x['lapTimes']) if x['lapTimes'] else float('inf'))
        
        return {"data": result}

    
    def load_session(self, year: int, gp: str, session_type: str = 'R') -> Dict:
        """Load a session and return basic info"""
        # [SAFETY FIX] Clear previous session data immediately
        self.session = None
        self.laps = None
        self.session_info = {}

        try:
            # --- 2025 SIMULATION LOGIC ---
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
            
            # [SAFETY FIX] Replace float('inf') with None for JSON compliance
            for d in drivers:
                if d['bestLapVal'] == float('inf'):
                    d['bestLapVal'] = None
            
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
        
        # Sort drivers by finishing position if available
        # Find finishing order
        finish_order = []
        for driver in drivers:
             d_laps = self.laps.pick_driver(driver)
             if not d_laps.empty:
                 # Last lap position
                 pos = d_laps.iloc[-1]['Position']
                 finish_order.append((driver, pos if pd.notna(pos) else 99))
        
        finish_order.sort(key=lambda x: x[1])
        sorted_drivers = [d[0] for d in finish_order]

        for driver in sorted_drivers:
            d_laps = self.laps.pick_driver(driver)
            
            # Group by Stint ID instead of Compound change
            # FastF1 'Stint' column increments on pit stops
            stints = []
            
            # Check if Stint column exists and has data
            if 'Stint' in d_laps.columns and d_laps['Stint'].notna().any():
                for stint_id, stint_laps in d_laps.groupby('Stint'):
                    if stint_laps.empty:
                        continue
                        
                    compound = stint_laps['Compound'].iloc[0]
                    if pd.isna(compound) or compound == '':
                        compound = 'UNKNOWN'
                        
                    start_lap = int(stint_laps['LapNumber'].min())
                    end_lap = int(stint_laps['LapNumber'].max())
                    
                    stints.append({
                        "compound": compound,
                        "startLap": start_lap,
                        "endLap": end_lap
                    })
            else:
                # Fallback to compound change logic if Stint is missing
                d_laps = d_laps.sort_values('LapNumber')
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
                
                if current_compound is not None:
                     stints.append({
                        "compound": current_compound,
                        "startLap": stint_start,
                        "endLap": int(d_laps['LapNumber'].max())
                    })

            # Get color
            team = d_laps['Team'].iloc[0] if not d_laps.empty else "Unknown"
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
            
        # [SORTING FIX] Process drivers in order of their finishing position
        # This ensures the tooltip list is ordered nicely (Winner on top)
        drivers = self.laps['Driver'].unique().tolist()
        
        # Determine finishing order
        finish_order = []
        for drv in drivers:
            d_laps = self.laps.pick_driver(drv)
            if not d_laps.empty:
                # Use 'Position' from the last available lap
                final_pos = d_laps.iloc[-1]['Position']
                finish_order.append((drv, final_pos if pd.notna(final_pos) else 999))
            else:
                finish_order.append((drv, 999))
                
        # Sort by position (ascending)
        finish_order.sort(key=lambda x: x[1])
        sorted_drivers = [x[0] for x in finish_order]
        
        gaps_data = analysis_engine.calculate_race_gaps(self.laps, sorted_drivers)
        
        # Format for frontend (add colors)
        result = []
        for drv in sorted_drivers:
            if drv not in gaps_data:
                continue
                
            # Safely get team color
            d_laps = self.laps.pick_driver(drv)
            color = "#888"
            if not d_laps.empty:
                 team = d_laps['Team'].iloc[0]
                 color = get_team_color(team)
            
            result.append({
                "driver": drv,
                "color": color,
                "data": gaps_data[drv]
            })
            
        return result

    def get_lap_distribution(self) -> Dict:
        """Get lap time distribution for box plots"""
        if self.laps is None:
            raise Exception("No session loaded")
            
        # Filter for valid racing laps (exclude in/out laps and slow laps)
        clean_laps = self.laps.pick_quicklaps()
        drivers = clean_laps['Driver'].unique()
        
        result = []
        
        for driver in drivers:
            d_laps = clean_laps.pick_driver(driver)
            if d_laps.empty:
                continue
                
            team = d_laps['Team'].iloc[0]
            color = get_team_color(team)
            
            # Convert to seconds and remove NaNs
            times = d_laps['LapTime'].dt.total_seconds().dropna().tolist()
            
            if times:
                result.append({
                    "driver": driver,
                    "color": color,
                    "lapTimes": times
                })
            
        # Sort by median lap time (fastest drivers on left/top)
        result.sort(key=lambda x: np.median(x['lapTimes']) if x['lapTimes'] else float('inf'))
        
        return {"data": result}
        
    def get_ghost_trace(self, driver1: str, driver2: str) -> Dict:
        """Get ghost delta trace"""
        if self.laps is None:
            raise Exception("No session loaded")
            
        lap1 = self.laps.pick_driver(driver1).pick_fastest()
        lap2 = self.laps.pick_driver(driver2).pick_fastest()
        
        if lap1 is None or lap2 is None:
            raise Exception("One of the drivers has no laps")
            
        tel1 = lap1.get_car_data().add_distance().add_relative_distance()
        if 'Time' not in tel1.columns:
             tel1['Time'] = tel1.index
        
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

    def get_top_speed_analysis(self) -> Dict:
        """Get Max Speed (Speed Trap) per lap for all drivers"""
        if self.laps is None:
            raise Exception("No session loaded")
            
        drivers = self.laps['Driver'].unique()
        result = []
        
        # Decide which column to use: SpeedST > SpeedI1 > SpeedFL
        speed_col = 'SpeedST'
        if speed_col not in self.laps.columns or self.laps[speed_col].isna().all():
            if 'SpeedI1' in self.laps.columns and not self.laps['SpeedI1'].isna().all():
                speed_col = 'SpeedI1'
            elif 'SpeedFL' in self.laps.columns:
                speed_col = 'SpeedFL'
            else:
                return {} # No speed data
        
        for driver in drivers:
            d_laps = self.laps.pick_driver(driver)
            if d_laps.empty:
                continue
            
            # Identify Team Color
            team = d_laps['Team'].iloc[0]
            color = get_team_color(team)
            
            # Extract Speed Data
            lap_speeds = []
            for _, lap in d_laps.iterrows():
                # Safety checks
                if pd.isna(lap['LapNumber']): continue
                
                speed_val = lap.get(speed_col)
                if pd.isna(speed_val): continue
                
                lap_speeds.append({
                    "lap": int(lap['LapNumber']),
                    "speed": float(speed_val)
                })
                
            if lap_speeds:
                result.append({
                    "driver": driver,
                    "color": color,
                    "data": lap_speeds
                })
                
        # Sort by fastest single speed achieved
        result.sort(key=lambda x: max([l['speed'] for l in x['data']]) if x['data'] else 0, reverse=True)
            
        return {"data": result, "metric": speed_col}

    def get_weekend_summary(self, year: int, gp: str) -> Dict:
        """Get comprehensive summary of the entire race weekend"""
        # [NEW FEATURE] Fetch data for all sessions
        
        print(f"Fetching Summary for {year} {gp}")
        
        # 1. Find the event explicitly from Schedule
        # This avoids FastF1's fuzzy matching giving us the wrong event (e.g. British instead of Qatar)
        try:
           schedule = fastf1.get_event_schedule(year)
           # Filter by name
           # Strict-ish match: check if user query is in event name
           matches = schedule[schedule['EventName'].str.lower().str.contains(gp.lower())]
           
           if matches.empty:
               # Try fuzzy fallback or just pick the first one? No, fail.
               # Maybe user passed "Qatar" and event is "Qatar Grand Prix" -> matches!
               raise Exception(f"Event '{gp}' not found in {year} schedule")
           
           # Take the first match
           # Make sure to handle testing sessions if they appear (usually Round 0)
           if len(matches) > 1:
               # If multiple, prefer the one with a RoundNumber > 0
               matches = matches[matches['RoundNumber'] > 0]
               
           event_row = matches.iloc[0]
           
           # Get the full Event object
           event = fastf1.get_event(year, event_row['RoundNumber'])
           
        except Exception as e:
            print(f"Event Lookup Failed: {e}")
            raise Exception(f"Event not found: {e}")

        summary = {
            "eventName": event['EventName'],
            "location": event['Location'],
            "date": str(event['EventDate'].date()),
            "sessions": []
        }
        
        # 2. Iterate through canonical sessions in the Event
        # FastF1 Event object identifies sessions by 'Session1', 'Session2', etc. or usage of .get_session(name)
        
        # Mapping for display (normalize names)
        # We need to map the RAW session name (e.g. "Practice 1") to our display code (FP1)
        # to ensure the UI shows nice labels.
        
        for i in range(1, 6):
            sess_name = event.get(f'Session{i}')
            if not sess_name or pd.isna(sess_name):
                continue
            
            # Use `_map_session_name` just for the DISPLAY TYPE code
            sess_type_code = self._map_session_name(sess_name)
            if not sess_type_code:
                 # It might be "Sprint" or "Sprint Qualifying" which _map handles
                 sess_type_code = "UNK"
            
            # Display Name (Short)
            display_name = sess_name
            if sess_type_code == "FP1": display_name = "FP1"
            elif sess_type_code == "FP2": display_name = "FP2"
            elif sess_type_code == "FP3": display_name = "FP3"
            elif sess_type_code == "Q": display_name = "Qualifying"
            elif sess_type_code == "SS": display_name = "Sprint Quali"
            elif sess_type_code == "S": display_name = "Sprint"
            elif sess_type_code == "R": display_name = "Race"
            
            try:
                # Load session DIRECTLY from the event object using the valid name
                # This prevents "British" / "Qatar" mixups entirely
                sess = event.get_session(sess_name)
                
                # Check if session has happened (data exists)
                # We can try loading
                print(f"Loading {sess_name}...")
                sess.load(telemetry=False, laps=True, weather=False, messages=False)
                # Extract Results
                
                # Helper to get results (official or calculated)
                results_data = self._get_session_results(sess, sess_type_code)
                
                if not results_data:
                     # If still no data, maybe it is a future session
                     # Check if we have any laps at all
                     if not sess.laps.empty:
                         # Should have been caught by helper, but just in case
                         pass
                     else:
                        raise Exception("No results data found")

                # Fast Lap (Session wide)
                fastest_lap_info = None
                try:
                    fastest = sess.laps.pick_fastest()
                    if fastest is not None and pd.notna(fastest['LapTime']):
                        fl_driver = fastest['Driver']
                        fl_team = sess.laps.pick_driver(fl_driver)['Team'].iloc[0]
                        fl_time = str(fastest['LapTime']).split('days')[-1].strip()[:-3]
                        fastest_lap_info = {
                            "driver": fl_driver,
                            "team": fl_team,
                            "time": fl_time,
                            "color": get_team_color(fl_team)
                        }
                except: pass

                summary['sessions'].append({
                    "name": display_name,
                    "type": sess_type_code,
                    "results": results_data,
                    "fastestLap": fastest_lap_info
                })
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Failed to load summary for {display_name}: {e}")
                summary['sessions'].append({
                    "name": display_name,
                    "error": "Data unavailable"
                })

        return summary

    def _get_session_results(self, session, session_type: str) -> List[Dict]:
        """
        Robustly extract session results.
        Prioritizes official session.results if valid.
        Falls back to calculating from session.laps if official results are missing/broken (Ergast fail).
        """
        results_data = []
        
        # 1. Try Official Results first
        if hasattr(session, 'results') and not session.results.empty:
            # Check if Position looks valid (not all NaNs or all 0s)
            positions = session.results['Position']
            if not positions.isna().all() and not (positions == 0).all():
                 # Looks good, use it
                 # Sort
                 top = session.results.sort_values(by='Position').head(10)
                 
                 for _, row in top.iterrows():
                     # Safe extraction
                     try:
                         driver = row.get('Abbreviation', 'UNK')
                         team = row.get('TeamName', '')
                         color = get_team_color(team)
                         
                         pos_val = row.get('Position')
                         position = int(pos_val) if pd.notna(pos_val) else 0
                         
                         status = str(row.get('Status', 'Finished'))
                         
                         time_str = "No Time"
                         # Time Logic
                         if session_type in ['R', 'S']:
                             t = row.get('Time')
                             if pd.notna(t):
                                 ts = t.total_seconds()
                                 m = int(ts // 60)
                                 s = ts % 60
                                 time_str = f"{m}:{s:06.3f}"
                             elif status.startswith("+"):
                                 time_str = status
                             elif position == 1:
                                 time_str = "Winner"
                             else:
                                 time_str = status
                         else:
                             # Q/FP - Best Lap
                             for col in ['Q3', 'Q2', 'Q1', 'Time']:
                                 val = row.get(col)
                                 if pd.notna(val):
                                     t_str = str(val).split('days')[-1].strip()
                                     if '.' in t_str: t_str = t_str[:-3]
                                     time_str = t_str
                                     break
                         
                         results_data.append({
                             "position": position,
                             "driver": driver,
                             "team": team,
                             "time": time_str,
                             "color": color,
                             "status": status
                         })
                     except: continue
                 
                 if results_data:
                     # Double check ordering - sometimes sort_values fails if types are mixed
                     results_data.sort(key=lambda x: x['position'] if x['position'] > 0 else 999)
                     return results_data

        # 2. Fallback: Calculate from Laps
        # This happens if Ergast is down
        if session.laps is None or session.laps.empty:
            return []
            
        print(f"Calculating fallback results for {session_type}...")
        
        # Get list of drivers
        drivers = session.laps['Driver'].unique()
        leaderboard = []
        
        for drv in drivers:
            d_laps = session.laps.pick_driver(drv)
            if d_laps.empty: continue
            
            team = d_laps['Team'].iloc[0]
            fastest = d_laps.pick_fastest()
            
            best_time = float('inf')
            best_time_str = "No Time"
            
            if fastest is not None and pd.notna(fastest['LapTime']):
                best_time = fastest['LapTime'].total_seconds()
                tmp_str = str(fastest['LapTime']).split('days')[-1].strip()
                if '.' in tmp_str: tmp_str = tmp_str[:-3]
                best_time_str = tmp_str
            
            # For Race, we ideally want finishing position.
            # laps['Position'] exists?
            last_pos = 999
            if 'Position' in d_laps.columns:
                last_val = d_laps.iloc[-1]['Position']
                if pd.notna(last_val):
                    last_pos = int(last_val)
            
            leaderboard.append({
                "driver": drv,
                "team": team,
                "best_time": best_time,
                "best_time_str": best_time_str,
                "last_pos": last_pos,
                "laps_count": len(d_laps)
            })
            
        # SORTING LOGIC
        if session_type in ['R', 'S']:
            # Race: Sort by Last Position (if available), then by Laps Completed (desc), then Time
            # If position is 999 (missing), we rely on laps count
            leaderboard.sort(key=lambda x: (x['last_pos'], -x['laps_count'], x['best_time']))
        else:
            # FP/Quali: Sort by Best Time
            leaderboard.sort(key=lambda x: x['best_time'])
            
        # Format for output
        for i, row in enumerate(leaderboard[:10]): # Top 10
            pos = i + 1
            
            time_display = row['best_time_str']
            if session_type in ['R', 'S'] and pos > 1:
                pass

            results_data.append({
                "position": pos,
                "driver": row['driver'],
                "team": row['team'],
                "time": time_display, 
                "color": get_team_color(row['team']),
                "status": "Calculated"
            })
            
        return results_data
        
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
