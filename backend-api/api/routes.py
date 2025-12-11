"""
API Routes - Overcut F1 API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from core.f1_processor import processor

router = APIRouter()


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
    """Get gap to leader evolution for all drivers"""
    try:
        gaps = processor.get_race_gaps()
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
