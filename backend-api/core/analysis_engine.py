import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from typing import List, Dict, Any

class AnalysisEngine:
    """
    Scientific F1 Data Processing Unit.
    Handles Fuel Correction, Gap Analysis, and Telemetry Merging.
    """
    
    @staticmethod
    def calculate_race_gaps(laps: pd.DataFrame, drivers: List[str]) -> Dict[str, List[Dict]]:
        """
        The 'Worm' Chart Logic.
        Calculate cumulative time for every driver and compare to the leader.
        """
        # Ensure laps are sorted
        laps = laps.sort_values(['Driver', 'LapNumber'])
        
        # Calculate cumulative time (RaceTime)
        laps['CumTime'] = laps['Time'].dt.total_seconds()
        
        # 1. Identify the Leader Time for each lap
        # Use the time of the driver who is physically in Position 1
        leader_laps = laps[laps['Position'] == 1.0][['LapNumber', 'CumTime']].set_index('LapNumber')
        
        # 2. Pivot everyone's times AND positions
        pivot_time = laps.pivot(index='LapNumber', columns='Driver', values='CumTime')
        pivot_pos = laps.pivot(index='LapNumber', columns='Driver', values='Position')
        
        # 3. Calculate Deltas
        result = {}
        
        for driver in drivers:
            if driver not in pivot_time.columns:
                continue
                
            driver_gaps = []
            
            # Get driver series
            d_times = pivot_time[driver].dropna()
            d_positions = pivot_pos[driver] # Will likely match index of d_times but let's be safe
            
            for lap_num, driver_time in d_times.items():
                if lap_num not in leader_laps.index:
                    continue
                    
                leader_time = leader_laps.loc[lap_num, 'CumTime']
                gap = driver_time - leader_time
                
                # Get position safely
                pos = d_positions.get(lap_num, None)
                
                # Only add if it makes sense
                driver_gaps.append({
                    "lap": int(lap_num),
                    "gap": float(gap),
                    "position": int(pos) if pd.notna(pos) else None
                })
            
            result[driver] = driver_gaps
            
        return result

    @staticmethod
    def calculate_fuel_correction(laps: pd.DataFrame, start_fuel_kg: float = 110.0, burn_rate_kg_lap: float = 1.8, time_loss_sec_kg: float = 0.035) -> List[Dict]:
        """
        Calculate Fuel-Corrected Lap Times to isolate Tyre Degradation.
        
        Formula:
        FuelEffect = (RemainingFuel) * PenaltyPerKg
        CorrectedTime = ActualTime - FuelEffect  (Normalizing to Empty Tank)
        
        Why usage of Subtract:
        Actual Time includes the penalty of the weight. To see the 'raw' performance 
        of the car/tyres without the fuel weight, we remove (subtract) that penalty.
        Since fuel drops over time, potential speed increases.
        Corrected Time should only show Tyre Deg (Time going UP).
        """
        results = []
        
        # Filter valid laps
        valid_laps = laps[laps['LapTime'].notna() & (laps['PitInTime'].isna()) & (laps['PitOutTime'].isna())]
        
        for _, lap in valid_laps.iterrows():
            lap_num = lap['LapNumber']
            actual_time = lap['LapTime'].total_seconds()
            
            # Fuel Math
            fuel_burned = lap_num * burn_rate_kg_lap
            remaining_fuel = max(0, start_fuel_kg - fuel_burned)
            fuel_effect = remaining_fuel * time_loss_sec_kg
            
            # Correction: Normalize to zero fuel (Remove the weight penalty)
            corrected_time = actual_time - fuel_effect
            
            results.append({
                "lap": int(lap_num),
                "actual": float(actual_time),
                "corrected": float(corrected_time),
                "fuelLoad": float(remaining_fuel)
            })
            
        return results

    @staticmethod
    def calculate_ghost_delta(telemetry_a: pd.DataFrame, telemetry_b: pd.DataFrame) -> Dict[str, List]:
        """
        Calculate GPS Time Delta between two telemetry traces based on Distance.
        """
        # 1. Add Distance if missing (assume passed in)
        if 'Distance' not in telemetry_a.columns or 'Distance' not in telemetry_b.columns:
            return {}

        # 2. Create common distance axis
        max_dist = min(telemetry_a['Distance'].max(), telemetry_b['Distance'].max())
        common_dist = np.arange(0, max_dist, 5) # 5m resolution
        
        # 3. Interpolate Time vs Distance
        # We need cumulative time at each distance.
        # FastF1 telemetry has 'Time' (timedelta) and 'Distance'.
        
        time_a_sec = telemetry_a['Time'].dt.total_seconds()
        time_b_sec = telemetry_b['Time'].dt.total_seconds()
        
        # Interpolator: Distance -> Time
        interp_a = interp1d(telemetry_a['Distance'], time_a_sec, fill_value="extrapolate")
        interp_b = interp1d(telemetry_b['Distance'], time_b_sec, fill_value="extrapolate")
        
        t_a_interp = interp_a(common_dist)
        t_b_interp = interp_b(common_dist)
        
        # Delta: Positive means A is Slower (Time is higher)
        delta = t_a_interp - t_b_interp
        
        return {
            "distance": common_dist.tolist(),
            "delta": delta.tolist()
        }

    @staticmethod
    def calculate_tyre_degradation(laps: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Calculate Tyre Degradation corrected for Fuel AND Track Evolution.
        """
        from scipy import stats  # Lazy import

        # 1. Strict Filtering (Green Flag, Accurate)
        clean = laps[
            (laps['TrackStatus'] == '1') & 
            (laps['IsAccurate'] == True) & 
            (laps['PitInTime'].isna()) & 
            (laps['PitOutTime'].isna())
        ].copy()
        
        if clean.empty: return {}

        # 2. Fuel Correction (Standard Model)
        # 110kg start, 0.035s loss/kg, 1.7kg burn/lap
        # We ADD this time back to normalize to "Zero Fuel" weight
        fuel_penalty = 1.7 * 0.035 
        clean['FuelCorrected'] = clean['LapTime'].dt.total_seconds() + (clean['LapNumber'] * fuel_penalty)

        # 3. Estimate Track Evolution (The "Global Drift")
        # We assume the 'average' driver gets faster due to track rubbering.
        # We calculate the linear trend of the WHOLE FIELD's FuelCorrected times.
        # If the field average slope is negative (getting faster), that's Track Evo.
        
        # Get x (Laps) and y (FuelCorrected Times) for entire field
        x_global = clean['LapNumber'].values
        y_global = clean['FuelCorrected'].values
        
        # Robust fit of the global trend
        # Note: theilslopes returns (slope, intercept, low_slope, high_slope)
        slope_global, _, _, _ = stats.theilslopes(y_global, x_global, 0.90)
        
        # If slope is negative (getting faster), we treat that as Track Evolution
        track_evo_per_lap = 0
        if slope_global < 0:
            track_evo_per_lap = abs(slope_global)
            
        # Apply Track Correction
        # We ADD this time back to simulate a track that never rubbers in.
        clean['FullyCorrected'] = clean['FuelCorrected'] + (clean['LapNumber'] * track_evo_per_lap)

        # 4. Calculate Degradation per Driver/Compound
        results = {"SOFT": [], "MEDIUM": [], "HARD": [], "INTERMEDIATE": [], "WET": []}
        drivers = clean['Driver'].unique()
        
        for driver in drivers:
            d_laps = clean[clean['Driver'] == driver]
            
            for compound in d_laps['Compound'].unique():
                if compound not in results: continue
                c_laps = d_laps[d_laps['Compound'] == compound]
                
                # Need ~4 laps for a trend
                if len(c_laps) < 4: continue
                
                # Robust Regression on Fully Corrected Data
                x = c_laps['TyreLife'].values
                y = c_laps['FullyCorrected'].values
                
                slope, intercept, _, _ = stats.theilslopes(y, x, 0.90)
                
                # Slope is now Pure Degradation (s/lap lost)
                
                results[compound].append({
                    "driver": driver,
                    "deg_per_lap": float(slope),
                    "confidence": 1.0, # Placeholder
                    "laps_analyzed": int(len(c_laps))
                })

        # Sort
        for comp in results:
            results[comp].sort(key=lambda x: x['deg_per_lap'])
            
        return results

analysis_engine = AnalysisEngine()
