"""
API Routes - Overcut F1 API
"""
from fastapi import APIRouter, HTTPException, Query
from urllib.parse import unquote
from typing import Optional

from core.f1_processor import processor

router = APIRouter()


@router.get("/seasons")
async def get_seasons():
    """Get list of supported seasons"""
    return processor.get_seasons()


@router.get("/races")
async def get_races(year: int = Query(..., description="Season year")):
    """Get list of races for a specific year"""
    try:
        races = processor.get_races(year)
        return races
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/init")
async def init_session(
    year: int = Query(..., description="Season year"),
    gp: str = Query(..., description="Grand Prix name"),
    session: str = Query("Q", description="Session type: FP1, FP2, FP3, Q, R")
):
    """Initialize a session and return drivers + circuit info"""
    try:
        result = processor.load_session(year, gp, session)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telemetry/driver/{driver_code}")
async def get_driver_laps(driver_code: str):
    """Get all laps for a specific driver"""
    try:
        laps = processor.get_driver_laps(driver_code.upper())
        return {"driver": driver_code.upper(), "laps": laps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telemetry/lap/{driver_code}/{lap_number}")
async def get_lap_telemetry(driver_code: str, lap_number: int):
    """Get granular telemetry for a specific lap"""
    try:
        telemetry = processor.get_lap_telemetry(driver_code.upper(), lap_number)
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/race/gaps")
async def get_race_gaps():
    """Get gap to leader evolution for all drivers (Worm Chart)"""
    try:
        gaps = processor.get_race_gaps_v2()
        return gaps
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/race/pitstops")
async def get_pit_stops():
    """Get pit stop strategy data for all drivers"""
    try:
        stops = processor.get_pit_stops()
        return {"strategies": stops}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{driver1}/{driver2}")
async def compare_drivers(driver1: str, driver2: str):
    """Compare two drivers' fastest laps"""
    try:
        comparison = processor.compare_drivers(driver1.upper(), driver2.upper())
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/fuel/{driver_code}")
async def get_fuel_analysis(driver_code: str):
    """Get fuel-corrected lap times"""
    try:
        data = processor.get_fuel_corrected_laps(driver_code.upper())
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/ghost/{driver1}/{driver2}")
async def get_ghost_analysis(driver1: str, driver2: str):
    """Get GPS Ghost Delta trace"""
    try:
        data = processor.get_ghost_trace(driver1.upper(), driver2.upper())
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/consistency")
async def get_consistency_data():
    """Get Lap Time Consistency (Box Plot)"""
    try:
        data = processor.get_lap_distribution()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekend/{year}/{gp}")
async def get_weekend_summary(year: int, gp: str):
    """Get a summary of the weekend's sessions and results"""
    try:
        # URL decode GP name just in case
        decoded_gp = unquote(gp)
        data = processor.get_weekend_summary(year, decoded_gp)
        return {"data": data}
    except Exception as e:
         print(f"Weekend summary error: {e}")
         raise HTTPException(status_code=500, detail=str(e))


@router.get("/race/topspeed")
async def get_top_speed():
    """Get Top Speed Analysis (Heatmap data)"""
    try:
        data = processor.get_top_speed_analysis()
        return data
    except Exception as e:
        print(f"Top speed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/theoretical_best/{driver_code}")
async def get_theoretical_best(driver_code: str):
    """Get Theoretical Best Lap analysis"""
    try:
        data = processor.get_theoretical_best_lap(driver_code.upper())
        return data
    except Exception as e:
        print(f"Theoretical best error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
