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

```bash
# Clone the repo
git clone https://github.com/22aaravpatel10/RaceEngineer.git
cd RaceEngineer

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## Tech Stack

- **GUI**: PyQt6 + QtWebEngine (Chromium)
- **Data**: FastF1 (historical), OpenF1 (live polling)
- **Visualization**: Plotly.js
- **Design**: Apple Health-inspired dark mode

## Usage

1. **Launch**: `python main.py`
2. **Wait**: 5-10s for Abu Dhabi 2023 data to load (first run)
3. **Click**: Any driver to see their telemetry
4. **Compare**: Type "Compare VER and LEC" in the command bar

## License

MIT
