"""
Global Configuration & Constants
"""

# --- TEAM COLORS (Master Copy) ---
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "McLaren": "#FF8000",
    "Ferrari": "#E80020",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "VCARB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Haas": "#B6BABD",
    "Haas F1 Team": "#B6BABD",
    "Audi": "#52E252" # Sauber becomes Audi
}

DEFAULT_COLOR = "#FFFFFF"

# --- 2025 / 2026 GRID SIMULATION MAP ---
# Maps 2023 Drivers (Source) -> 2025 Drivers (Target)
# Source: Who drove the car in 2023 (telemetry source)
# Target: Who we want to display (simulation)

GRID_2025 = {
    "VER": {"source": "VER", "team": "Red Bull Racing"},
    "LAW": {"source": "PER", "team": "Red Bull Racing"}, # Lawson replaces Perez
    "HAM": {"source": "SAI", "team": "Ferrari"},        # Hamilton to Ferrari (using Sainz data)
    "LEC": {"source": "LEC", "team": "Ferrari"},
    "RUS": {"source": "RUS", "team": "Mercedes"},
    "ANT": {"source": "HAM", "team": "Mercedes"},       # Antonelli to Merc (using Ham data)
    "NOR": {"source": "NOR", "team": "McLaren"},
    "PIA": {"source": "PIA", "team": "McLaren"},
    "ALO": {"source": "ALO", "team": "Aston Martin"},
    "STR": {"source": "STR", "team": "Aston Martin"},
    "GAS": {"source": "GAS", "team": "Alpine"},
    "DOO": {"source": "OCO", "team": "Alpine"},         # Doohan? Or keep OCO? Let's use DOO for fun or OCO if safer. Screenshot had OCO.
    # User screenshot had OCO. Let's keep OCO for now or stick to rumors. User had OCO.
    # Let's override OCO -> OCO to be safe, or map OCO to OCO.
    "OCO": {"source": "OCO", "team": "Haas"}, # Ocon to Haas (Rumor) - using Ocon 2023 data (Alpine) for Haas performance? No, that's cross-team.
    # To simulate Ocon in a Haas using 2023 data:
    # We should use a chaos mapping or just direct mapping.
    # Simplest: Map 2023 Grid to 2025 Grid conceptually.
    
    # Let's use the USER'S screenshot implied grid if possible, or a standard 2025 guess.
    # Screenshot: OCO, BEA, LEC, ANT, ALB, BOR, SAI, HUL, STR, LAW
    # OCO (Haas?), BEA (Haas), LEC (Fer), ANT (Merc), ALB (Wil), BOR (Audi), SAI (Wil), HUL (Audi), STR (AM), LAW (RB)
    
    "BEA": {"source": "HUL", "team": "Haas F1 Team"},   # Bearman replaces Hulkenberg
    "HUL": {"source": "BOT", "team": "Sauber"},         # Hulk to Sauber/Audi
    "BOR": {"source": "ZHO", "team": "Sauber"},         # Bortoleto to Sauber
    "ALB": {"source": "ALB", "team": "Williams"},
    "SAI": {"source": "SAR", "team": "Williams"},       # Sainz to Williams (replaces Sargeant)
    "TSU": {"source": "TSU", "team": "RB"},
    "HAD": {"source": "DEV", "team": "RB"},            # Hadjar? (using De Vries/Ricciardo data)
    "COL": {"source": "MAG", "team": "Haas"}           # Colapinto?
}

# Update function
def get_team_color(team_name: str) -> str:
    """Returns the hex color for a given team name."""
    if not team_name:
        return DEFAULT_COLOR
    
    # Direct match
    if team_name in TEAM_COLORS:
        return TEAM_COLORS[team_name]
        
    # Case-insensitive search
    for key, color in TEAM_COLORS.items():
        if key.lower() == team_name.lower():
            return color
            
    return DEFAULT_COLOR
