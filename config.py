# config.py
# Overcut F1 Dashboard - Grid Configuration

# --- TEAM COLORS (2025/2026) ---
TEAM_COLORS = {
    "Red Bull Racing": "#1E41FF",
    "Mercedes": "#00D2BE",
    "Ferrari": "#FF2800",
    "McLaren": "#FF8000",
    "Aston Martin": "#006F62",
    "Alpine": "#0090FF",
    "Williams": "#005AFF",
    "VCARB": "#6692FF",
    "Haas": "#B6BABD",
    "Audi": "#FF3B00",
    "Cadillac": "#D4AF37"
}

# --- 2025 GRID SIMULATION (Based on Abu Dhabi 2023 Data) ---
# Maps NEW driver to OLD driver's telemetry from 2023.
GRID_2025 = {
    "VER": {"team": "Red Bull Racing", "source": "VER"},
    "LAW": {"team": "Red Bull Racing", "source": "PER"},  # Lawson takes Perez seat
    "RUS": {"team": "Mercedes", "source": "RUS"},
    "ANT": {"team": "Mercedes", "source": "HAM"},         # Kimi takes Lewis's data
    "LEC": {"team": "Ferrari", "source": "LEC"},
    "HAM": {"team": "Ferrari", "source": "SAI"},         # Lewis takes Sainz's data
    "NOR": {"team": "McLaren", "source": "NOR"},
    "PIA": {"team": "McLaren", "source": "PIA"},
    "ALO": {"team": "Aston Martin", "source": "ALO"},
    "STR": {"team": "Aston Martin", "source": "STR"},
    "GAS": {"team": "Alpine", "source": "GAS"},
    "DOO": {"team": "Alpine", "source": "OCO"},          # Doohan takes Ocon
    "ALB": {"team": "Williams", "source": "ALB"},
    "SAI": {"team": "Williams", "source": "SAR"},        # Sainz in, Sargeant data
    "TSU": {"team": "VCARB", "source": "TSU"},
    "HAD": {"team": "VCARB", "source": "RIC"},           # Hadjar takes Ric/Lawson slot
    "OCO": {"team": "Haas", "source": "MAG"},            # Ocon takes Mag
    "BEA": {"team": "Haas", "source": "HUL"},            # Bearman takes Hulk
    "HUL": {"team": "Audi", "source": "BOT"},            # Hulk in Sauber (Audi)
    "BOR": {"team": "Audi", "source": "ZHO"},            # Bortoleto in Sauber
}

# --- 2026 GRID PREDICTION (Hypothetical) ---
# Adds Cadillac, keeps Audi.
GRID_2026 = GRID_2025.copy()
GRID_2026.update({
    "BOT": {"team": "Cadillac", "source": "STR"},        # Cadillac uses Aston data as proxy
    "PER": {"team": "Cadillac", "source": "ALO"},        # Perez in 2nd Caddy
})

def get_driver_color(driver_code: str, grid: dict = None) -> str:
    """Returns the team color for a given driver code."""
    if grid and driver_code in grid:
        team = grid[driver_code]["team"]
        return TEAM_COLORS.get(team, "#FFFFFF")
    return "#FFFFFF"
