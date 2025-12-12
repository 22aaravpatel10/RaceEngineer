"""
Configuration and Constants
"""

# Team Colors (Official Hex Codes)
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",   # Blue
    "Red Bull": "#3671C6",
    "Mercedes": "#27F4D2",          # Cyan
    "Ferrari": "#E80020",           # Red
    "McLaren": "#FF8000",           # Papaya
    "Aston Martin": "#229971",      # Green
    "Alpine F1 Team": "#0093CC",
    "Alpine": "#0093CC",            # Blue
    "Williams": "#64C4FF",          # Light Blue
    "AlphaTauri": "#5E8FAA",        # Old AT
    "RB F1 Team": "#6692FF",
    "RB": "#6692FF",                # VCARB Blue
    "Visa Cash App RB": "#6692FF",
    "Sauber": "#52E252",
    "Kick Sauber": "#52E252",       # Neon Green
    "Stake F1 Team Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",      # Grey
    "Haas": "#B6BABD",
    "Alfa Romeo": "#900000",        # Old Alfa
}

# 2025 Driver Lineup Simulation Map
# Maps 2025 Drivers -> 2023/2024 Data Sources
GRID_2025 = {
    "HAM": {"source": "HAM", "team": "Ferrari"},
    "LEC": {"source": "LEC", "team": "Ferrari"},
    "VER": {"source": "VER", "team": "Red Bull Racing"},
    "LAW": {"source": "PER", "team": "Red Bull Racing"}, # Lawson using Perez data
    "NOR": {"source": "NOR", "team": "McLaren"},
    "PIA": {"source": "PIA", "team": "McLaren"},
    "RUS": {"source": "RUS", "team": "Mercedes"},
    "ANT": {"source": "SAI", "team": "Mercedes"}, # Antonelli using Sainz data
    "ALO": {"source": "ALO", "team": "Aston Martin"},
    "STR": {"source": "STR", "team": "Aston Martin"},
    "TSU": {"source": "TSU", "team": "RB"},
    "HAD": {"source": "RIC", "team": "RB"},
    "HUL": {"source": "HUL", "team": "Kick Sauber"},
    "BOR": {"source": "ZHO", "team": "Kick Sauber"},
    "GAS": {"source": "GAS", "team": "Alpine"},
    "DOO": {"source": "OCO", "team": "Alpine"},
    "ALB": {"source": "ALB", "team": "Williams"},
    "SAI": {"source": "SAR", "team": "Williams"},
    "OCO": {"source": "MAG", "team": "Haas F1 Team"},
    "BEA": {"source": "HUL", "team": "Haas F1 Team"}
}

def get_team_color(team_name: str) -> str:
    """Get hex color for a team with fallback"""
    return TEAM_COLORS.get(team_name, "#FFFFFF")
