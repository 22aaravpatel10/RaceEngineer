# config.py
# 2026 Grid Configuration for Overcut

# --- Tier 1: Team Colors ---
TEAM_COLORS = {
    "Red Bull Racing": "#1E41FF",   # Verstappen / Hadjar
    "Mercedes": "#00D2BE",          # Russell / Antonelli
    "Ferrari": "#FF2800",           # Leclerc / Hamilton
    "McLaren": "#FF8000",           # Norris / Piastri
    "Aston Martin": "#006F62",      # Alonso / Stroll
    "Alpine": "#0090FF",            # Gasly / Colapinto
    "Williams": "#005AFF",          # Sainz / Albon
    "VCARB": "#6692FF",             # Lawson / Lindblad
    "Haas": "#B6BABD",              # Ocon / Bearman
    "Audi": "#FF3B00",              # Hulkenberg / Bortoleto (Neon Red/Grey)
    "Cadillac": "#D4AF37",          # Bottas / Perez (Gold/Black)
}

# --- Tier 1: Driver Mapping ---
# Maps specific drivers to their 2026 Teams (for effective color lookup)
# This handles the historical data re-mapping (e.g. HAM in Merc data -> Ferrari Red)
DRIVER_MAPPING_2026 = {
    "VER": "Red Bull Racing",
    "HAD": "Red Bull Racing",
    "RUS": "Mercedes",
    "ANT": "Mercedes",
    "LEC": "Ferrari",
    "HAM": "Ferrari",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "ALO": "Aston Martin",
    "STR": "Aston Martin",
    "GAS": "Alpine",
    "COL": "Alpine",
    "SAI": "Williams",
    "ALB": "Williams",
    "LAW": "VCARB",
    "LIN": "VCARB",
    "OCO": "Haas",
    "BEA": "Haas",
    "HUL": "Audi",
    "BOR": "Audi",
    "BOT": "Cadillac",
    "PER": "Cadillac" 
}

# --- Time Machine: 2025 Simulation Map ---
# Maps NEW 2025 drivers to OLD 2023 drivers' telemetry data
SIMULATION_MAP = {
    "HAM": {"team": "Ferrari", "source_driver": "SAI"},       # Lewis takes Sainz's Ferrari data
    "LEC": {"team": "Ferrari", "source_driver": "LEC"},
    "VER": {"team": "Red Bull Racing", "source_driver": "VER"},
    "ANT": {"team": "Mercedes", "source_driver": "HAM"},      # Antonelli takes Lewis's Merc data
    "RUS": {"team": "Mercedes", "source_driver": "RUS"},
    "NOR": {"team": "McLaren", "source_driver": "NOR"},
    "PIA": {"team": "McLaren", "source_driver": "PIA"},
    "SAI": {"team": "Williams", "source_driver": "ALB"},      # Sainz takes Albon's Williams data
    "ALB": {"team": "Williams", "source_driver": "SAR"},
    "HUL": {"team": "Audi", "source_driver": "BOT"},         # Hulkenberg takes a Sauber (Audi) slot
    "BOR": {"team": "Audi", "source_driver": "ZHO"},         # Bortoleto takes the other
    "BEA": {"team": "Haas", "source_driver": "HUL"},         # Bearman takes Hulk's Haas data
    "OCO": {"team": "Haas", "source_driver": "MAG"},
    "BOT": {"team": "Cadillac", "source_driver": "STR"},      # Placeholder: Cadillac takes Aston data
}

def get_driver_color(driver_code: str) -> str:
    """
    Returns the 2026 Team Color for a given driver code.
    If code not found, returns White.
    """
    team = DRIVER_MAPPING_2026.get(driver_code.upper())
    if team:
        return TEAM_COLORS.get(team, "#FFFFFF")
    return "#FFFFFF"
