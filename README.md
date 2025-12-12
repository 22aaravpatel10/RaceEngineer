# Overcut - F1 Race Engineer Dashboard

A high-fidelity, web-based Formula 1 analytics platform.
Built with **FastAPI** (Backend) and **Next.js** (Frontend), utilizing **FastF1** for efficient telemetry data processing.

## Features

- **📊 Live Dashboard**: Real-time telemetry visualization for any F1 session.
- **📅 Weekend Summary**: Comprehensive overview of every session (FP1, FP2, FP3, Quali, Race) including fastest laps and finishing order.
- **🏎️ Telemetry Analysis**:
    - **Speed/Throttle/Brake Traces**: Interactive comparisons between drivers.
    - **"The Worm"**: Gap to leader evolution over the entire race.
    - **Top Speed History**: Track maximum velocity per lap.
    - **Tyre Strategy**: Visual Gantt chart of pit stops and compound usage.
- **👻 Ghost Car**: Advanced GPS delta analysis to find time lost/gained in corners.
- **2025 Grid Simulation**: Optional mode to simulate future driver lineups.

## Installation & Setup

### 1. Backend (Python/FastAPI)
Navigate to the `backend-api` directory:
```bash
cd backend-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*The API will start at `http://localhost:8000`*

### 2. Frontend (Next.js/React)
Navigate to the `frontend-web` directory:
```bash
cd frontend-web
npm install
npm run dev
```
*The Dashboard will start at `http://localhost:4000` (or the port shown in terminal)*

## Usage Guide

1. **Select a Race**: Use the sidebar to pick a Season and Grand Prix (e.g., 2024 Abu Dhabi).
2. **Dashboard Mode**:
    - View live telemetry, gap charts, and consistency plots.
    - Click "Compare" to overlay two drivers.
3. **Summary Mode**:
    - Toggle the switch in the top header to "Summary".
    - View results for all sessions, highlighting fastest laps and gaps.

## License
MIT
