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
            
            # Handle aliases for GP names via strict schedule lookup
            # This prevents FastF1's fuzzy matcher from returning British GP when we want Qatar
            schedule = fastf1.get_event_schedule(target_year)
            matches = schedule[schedule['EventName'].str.lower().str.contains(gp.lower())]
            
            if matches.empty:
                # Fallback: Maybe user passed "British" and schedule says "British Grand Prix" -> OK
                # But if empty, we might have an alias issue. 
                # Try fuzzy matching manually or just trust get_session? 
                # No, the user issue is Over-Fuzzy matching.
                # Let's try to match "Location" too.
                matches = schedule[schedule['Location'].str.lower().str.contains(gp.lower())]
                
            if matches.empty:
                 # If still empty, let's try the direct call as a last resort, but warn
                 print(f"WARNING: Strict lookup failed for '{gp}'. Trying direct fuzzy load...")
                 self.session = fastf1.get_session(target_year, gp, session_type)
            else:
                 # Take the best match (Round > 0 preferred)
                 if len(matches) > 1:
                     r_matches = matches[matches['RoundNumber'] > 0]
                     if not r_matches.empty:
                         matches = r_matches
                 
                 event_name = matches.iloc[0]['EventName']
                 print(f"Resolved '{gp}' to '{event_name}'")
                 self.session = fastf1.get_session(target_year, event_name, session_type)
            
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
        print(f"DEBUG: get_lap_telemetry for {driver_code} Lap {lap_number}")
        if self.laps is None:
            raise Exception("No session loaded")
        
        try:
            d_laps = self.laps.pick_driver(driver_code)
            lap = d_laps[d_laps['LapNumber'] == lap_number].iloc[0]
            
            # Check if telemetry is already loaded
            car = lap.get_car_data().add_distance()
            
            if car.empty:
                 print(f"DEBUG: Car data empty for {driver_code} Lap {lap_number}")
                 raise Exception("Telemetry data not available for this lap")
                 
        except Exception as e:
            print(f"DEBUG: Telemetry Error: {e}")
            raise e

        
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
        print(f"DEBUG: Ghost Analysis {driver1} vs {driver2}")
        if self.laps is None:
            print("Ghost Error: No session loaded")
            raise Exception("No session loaded")
            
        d1_laps = self.laps.pick_driver(driver1)
        d2_laps = self.laps.pick_driver(driver2)
        
        if d1_laps.empty or d2_laps.empty:
             print(f"Ghost Error: Missing laps for {driver1} or {driver2}")
             raise Exception(f"Missing laps for {driver1} or {driver2}")

        lap1 = d1_laps.pick_fastest()
        lap2 = d2_laps.pick_fastest()
        
        if lap1 is None or pd.isna(lap1['LapTime']):
             print(f"Ghost Error: No valid fastest lap for {driver1}")
             raise Exception(f"No valid fastest lap for {driver1}")
             
        if lap2 is None or pd.isna(lap2['LapTime']):
             print(f"Ghost Error: No valid fastest lap for {driver2}")
             raise Exception(f"No valid fastest lap for {driver2}")

        print(f"DEBUG: Ghost Laps - {driver1}: {lap1['LapTime']}, {driver2}: {lap2['LapTime']}")
            
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
            "delta": delta_data.get('delta', []),
            "corners": self.session_info.get('corners', [])
        }

    def get_top_speed_analysis(self) -> Dict:
        """Get Max Speed Heatmap Data (Top 15 speeds per driver)"""
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
                print(f"DEBUG: No speed columns found. Available: {list(self.laps.columns)}")
                return {} # No speed data
        
        print(f"DEBUG: Using speed column: {speed_col}")
        
        for driver in drivers:
            d_laps = self.laps.pick_driver(driver)
            if d_laps.empty:
                continue
            
            team = d_laps['Team'].iloc[0]
            color = get_team_color(team)
            
            # Extract Speed Data - Get ALL speeds for this driver in this session
            # Drop NaNs and zeros
            speeds = d_laps[speed_col].dropna()
            speeds = speeds[speeds > 10].astype(float).tolist() # Filter out pit/slow
            
            if not speeds: continue
            
            # Sort Descending (Fastest first)
            speeds.sort(reverse=True)
            
            # Take Top 15
            top_15 = speeds[:15]
            
            # Calculate Average of the Top 15 (or fewer)
            avg_speed = sum(top_15) / len(top_15) if top_15 else 0
            
            result.append({
                "driver": driver,
                "team": team,
                "color": color,
                "top_speeds": top_15,
                "average": avg_speed,
                "max_speed": top_15[0] if top_15 else 0
            })
                
        # Sort Drivers by their SINGLE FASTEST speed (descending)
        result.sort(key=lambda x: x['max_speed'], reverse=True)
            
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
        Robustly extract session results with correct Gap calculations.
        """
        results_data = []
        
        # --- STRATEGY 1: OFFICIAL RESULTS (Preferred) ---
        use_official = False
        if hasattr(session, 'results') and not session.results.empty:
            positions = session.results['Position']
            # specific check: ensure positions are not all 0/NaN
            if not positions.isna().all() and not (positions == 0).all():
                # [OVERRIDE] For Race/Sprint, we often skip official results if they are unreliable
                # But if we want Gaps, Official is best if available.
                # However, previous issues showed Official data often has wrong order.
                # Let's trust official ONLY if not Race/Sprint OR if the user wants it.
                # Actually, for Gaps, Official Results usually contain 'Time' column as Timedelta.
                use_official = True
                
        # FORCE FALLBACK for Race/Sprint to avoid "Random Order" bug unless we are sure
        if session_type in ['R', 'S']:
             use_official = False

        if use_official:
            # 1. Prepare Winner's Time for Gap Calculation
            winner_time = None
            try:
                # Get P1 row safely
                p1_row = session.results[session.results['Position'] == 1]
                if not p1_row.empty:
                    winner_time = p1_row.iloc[0].get('Time') # This is a Timedelta
            except: pass

            top = session.results.sort_values(by='Position') # Get all
            
            for _, row in top.iterrows():
                try:
                    driver = row.get('Abbreviation', 'UNK')
                    team = row.get('TeamName', '')
                    color = get_team_color(team)
                    position = int(row.get('Position', 0))
                    status = str(row.get('Status', 'Finished'))
                    
                    time_str = "No Time"
                    
                    # --- RACE / SPRINT LOGIC ---
                    if session_type in ['R', 'S']:
                        driver_time = row.get('Time')
                        
                        # Case A: The Winner
                        if position == 1:
                            if pd.notna(driver_time):
                                ts = driver_time.total_seconds()
                                h = int(ts // 3600)
                                m = int((ts % 3600) // 60)
                                s = ts % 60
                                if h > 0:
                                    time_str = f"{h}:{m:02d}:{s:06.3f}"
                                else:
                                    time_str = f"{m}:{s:06.3f}"
                            else:
                                time_str = "Winner"
                                
                        # Case B: The Rest (Calculate Gap)
                        else:
                            # 1. Try to calculate mathematical gap
                            if pd.notna(driver_time) and pd.notna(winner_time):
                                delta = driver_time - winner_time
                                dt_s = delta.total_seconds()
                                time_str = f"+{dt_s:.3f}s"
                            
                            # 2. If no time (Lapped or DNF), use Status
                            else:
                                # Status often contains "+1 Lap" or "DNF"
                                time_str = status

                    # --- QUALI / PRACTICE LOGIC ---
                    else:
                        # For Quali, we want the Fastest Lap set in the latest session
                        # FastF1 results usually put the best relevant time in 'Time' or Q1/Q2/Q3 cols
                        
                        best_val = pd.NaT
                        # Priority: Time > Q3 > Q2 > Q1 (and SQ3/SQ2/SQ1)
                        # We check SQ columns first as they are specific to Sprint Shootout
                        cols_to_check = ['SQ3', 'SQ2', 'SQ1', 'Q3', 'Q2', 'Q1', 'Time']
                        for col in cols_to_check:
                            val = row.get(col)
                            if pd.notna(val):
                                # Check if it's a valid time (not 0 days 00:00:00)
                                if isinstance(val, (pd.Timedelta, datetime.timedelta)) and val.total_seconds() > 0:
                                    best_val = val
                                    break
                                # If it's just a string or other non-null, take it?
                                elif not isinstance(val, (pd.Timedelta, datetime.timedelta)) and val:
                                     # Sometimes it's a string from FastF1? Rarely.
                                     pass
                                
                        if pd.notna(best_val):
                             t_str = str(best_val).split('days')[-1].strip()
                             if '.' in t_str: t_str = t_str[:-3]
                             time_str = t_str
                    
                    results_data.append({
                        "position": position,
                        "driver": driver,
                        "team": team,
                        "time": time_str,
                        "color": color,
                        "status": status
                    })
                except Exception as e: 
                    continue
                    
            return results_data

        # --- STRATEGY 2: FALLBACK (Calculated from Laps) ---
        if session.laps is None or session.laps.empty: return []
        
        drivers = session.laps['Driver'].unique()
        leaderboard = []
        
        for drv in drivers:
            try:
                d_laps = session.laps.pick_driver(drv)
                if d_laps.empty: continue
                
                team = d_laps['Team'].iloc[0]
                
                # 1. Best Lap (for Quali)
                fastest = d_laps.pick_fastest()
                best_lap_time = fastest['LapTime'].total_seconds() if fastest is not None and pd.notna(fastest['LapTime']) else float('inf')
                
                # 2. Race Finish Time (Cumulative)
                # We use the 'Time' column of the LAST LAP. This is the session time when they crossed the line.
                last_lap = d_laps.iloc[-1]
                finish_time = last_lap['Time'] # Timedelta
                laps_completed = len(d_laps)
                
                leaderboard.append({
                    "driver": drv,
                    "team": team,
                    "best_lap_val": best_lap_time,
                    "finish_time": finish_time,
                    "laps_completed": laps_completed,
                    "last_pos": int(last_lap['Position']) if pd.notna(last_lap['Position']) else 999
                })
            except: continue
            
        # SORTING
        if session_type in ['R', 'S']:
            # Sort by Laps Completed (Desc), then Finish Time (Asc)
            # This handles lapped cars correctly (more laps = higher pos)
            leaderboard.sort(key=lambda x: (-x['laps_completed'], x['finish_time']))
            
            # Calculate Gaps
            if leaderboard:
                winner = leaderboard[0]
                winner_time = winner['finish_time']
                
                for i, row in enumerate(leaderboard):
                    # Winner
                    if i == 0:
                        # Format winner time
                        ts = winner_time.total_seconds()
                        h = int(ts // 3600)
                        m = int((ts % 3600) // 60)
                        s = ts % 60
                        row['display_time'] = f"{h}:{m:02d}:{s:06.3f}"
                    # Others
                    else:
                        # Check if on same lap
                        if row['laps_completed'] == winner['laps_completed']:
                             gap = row['finish_time'] - winner_time
                             row['display_time'] = f"+{gap.total_seconds():.3f}s"
                        else:
                             lap_diff = winner['laps_completed'] - row['laps_completed']
                             # Check if DNF (e.g. < 90% distance)
                             if row['laps_completed'] < winner['laps_completed'] * 0.9:
                                 row['display_time'] = "DNF"
                             else:
                                 row['display_time'] = f"+{lap_diff} Lap{'s' if lap_diff > 1 else ''}"
        else:
            # Quali: Sort by Best Lap
            leaderboard.sort(key=lambda x: x['best_lap_val'])
            for row in leaderboard:
                # Format lap time
                if row['best_lap_val'] == float('inf'):
                    row['display_time'] = "No Time"
                else:
                    m = int(row['best_lap_val'] // 60)
                    s = row['best_lap_val'] % 60
                    row['display_time'] = f"{m}:{s:06.3f}"
            
        # Final Format
        for i, row in enumerate(leaderboard):
            results_data.append({
                "position": i + 1,
                "driver": row['driver'],
                "team": row['team'],
                "time": row.get('display_time', '-'), 
                "color": get_team_color(row['team']),
                "status": "Calculated"
            })
            
        return results_data
        
    def get_theoretical_best_lap(self, driver: str) -> Dict:
        """
        Calculate Theoretical Best Lap using Mini-Sectors.
        """
        if self.laps is None:
            print("Theoretical Best: No session loaded")
            raise Exception("No session loaded")

        print(f"DEBUG: Theoretical Best for {driver}")

        # 1. Filter Laps
        # Must be accurate, not in/out
        driver_laps = self.laps.pick_driver(driver)
        if driver_laps.empty:
            print(f"DEBUG: No laps for driver {driver}")
            return {}
            
        d_laps = driver_laps.pick_accurate()
        if d_laps.empty:
            print(f"DEBUG: No ACCURATE laps for driver {driver} (Total: {len(driver_laps)})")
            # Fallback: Try all valid laps (not in/out) if accurate is too strict
            d_laps = driver_laps.pick_wo_box()
            if d_laps.empty:
                 return {}

        # 2. Reference Lap (The Actual Fastest)
        fastest_lap = d_laps.pick_fastest()
        if fastest_lap is None or pd.isna(fastest_lap['LapTime']):
             print("DEBUG: No fastest lap found")
             return {}
             
        try:
            ref_tel = fastest_lap.get_telemetry()
        except Exception as e:
             print(f"DEBUG: Failed to get ref telemetry: {e}")
             return {}
             
        # Normalize distance (ensure strictly increasing for interp)
        max_dist = ref_tel['Distance'].max()
        
        # 3. Define N Sectors
        N_SECTORS = 25
        chunk_size = max_dist / N_SECTORS
        
        # We need to collect sector times for ALL valid laps
        # Matrix: [Lap_i][Sector_j]
        sector_times_matrix = []
        
        # Pre-calculate lap objects to iterate
        valid_laps_telemetry = []
        
        for _, lap in d_laps.iterrows():
            try:
                # We need telemetry for interpolation
                tel = lap.get_telemetry()
                if tel.empty: continue
                
                # Setup interpolation: Time (s) vs Distance (m)
                # Ensure Distance is sorted for np.interp
                tel = tel.sort_values(by='Distance')
                dist_vals = tel['Distance'].values
                time_vals = tel['Time'].dt.total_seconds().values
                
                valid_laps_telemetry.append((dist_vals, time_vals))
            except:
                continue
                
        if not valid_laps_telemetry:
            return {}
            
        # 4. Processing Loop
        boundaries = [i * chunk_size for i in range(N_SECTORS + 1)]
        all_laps_sectors = [] 
        
        for dist_series, time_series in valid_laps_telemetry:
            # Interpolate times at all boundaries
            t_boundaries = np.interp(boundaries, dist_series, time_series)
            # Calculate durations
            sector_durations = np.diff(t_boundaries)
            all_laps_sectors.append(sector_durations)
            
        if not all_laps_sectors:
            return {}

        # 5. Find Theoretical Best
        matrix = np.array(all_laps_sectors)
        best_sector_times = np.min(matrix, axis=0) # Shape: (25,)
        theoretical_best_time = np.sum(best_sector_times)
        
        # 6. Compare with Actual Best Lap (Reference)
        ref_dist = ref_tel['Distance'].values
        ref_time = ref_tel['Time'].dt.total_seconds().values
        ref_t_bounds = np.interp(boundaries, ref_dist, ref_time)
        ref_sector_times = np.diff(ref_t_bounds)
        actual_best_time = np.sum(ref_sector_times) 
        
        # Calculate Delta/Gain per sector
        deltas = ref_sector_times - best_sector_times
        
        # 7. Prepare Visualization Data (Track Map Segments)
        map_segments = []
        
        if 'X' not in ref_tel.columns:
            return {"error": "No GPS data"}
            
        for i in range(N_SECTORS):
            d_start = boundaries[i]
            d_end = boundaries[i+1]
            
            # Filter ref_tel for points in this range
            mask = (ref_tel['Distance'] >= d_start) & (ref_tel['Distance'] <= d_end)
            segment_points = ref_tel[mask]
            
            if segment_points.empty: continue
            
            map_segments.append({
                "sector_index": i + 1,
                "x": segment_points['X'].tolist(),
                "y": segment_points['Y'].tolist(),
                "time_lost": float(deltas[i]),
                "pct_lost": float(deltas[i] / ref_sector_times[i]) if ref_sector_times[i] > 0 else 0
            })
            
        return {
            "driver": driver,
            "theoretical_best": float(theoretical_best_time),
            "actual_best": float(actual_best_time),
            "diff": float(actual_best_time - theoretical_best_time),
            "segments": map_segments
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
