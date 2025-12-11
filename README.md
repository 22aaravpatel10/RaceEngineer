# Overcut - F1 Race Engineer Dashboard

A high-fidelity, dark-mode desktop application for Formula 1 telemetry analysis.  
Built with Python (PyQt6) + HTML/CSS/JS frontend + FastF1/OpenF1 data integration.

![Overcut Dashboard](https://via.placeholder.com/800x450/000000/FFFFFF?text=Overcut+Dashboard)

## Features

- **2025 Grid Simulation**: Uses "Time Machine" to map 2025 drivers to 2023 telemetry data
- **Ghost Car Algorithm**: Aligns telemetry by distance for precise driver comparison
- **Apple Health Design**: Bento grid layout, Dynamic Island, minimal Plotly charts
- **Natural Language Commands**: Type "Compare VER and HAM" to overlay traces
- **Click-to-Load Telemetry**: Click any driver card to view their Speed/Throttle traces

## Installation

### Prerequisites
- Python 3.9+
- Node.js (LTS)

### Backend (FastAPI)
```bash
cd backend-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend-web
npm install
npm run dev
```

The dashboard will be available at [http://localhost:4000](http://localhost:4000).

## Usage

1. **Start Backend**: Ensure the API is running on port 8000.
2. **Start Frontend**: Run `npm run dev` in `frontend-web`.
3. **Open Browser**: Go to `http://localhost:4000`.
4. **Compare**: Type "Compare VER and LEC" in the command bar.

## License

MIT
