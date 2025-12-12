/**
 * Master Team Color Map
 * Enforces correct branding across the application.
 */
export const ACTION_COLOR = '#0A84FF'; // iOS Blue
export const POSITIVE_COLOR = '#30D158'; // iOS Green
export const NEGATIVE_COLOR = '#FF453A'; // iOS Red

export const TEAM_COLORS: Record<string, string> = {
    "Red Bull Racing": "#3671C6",
    "McLaren": "#FF8000",
    "Ferrari": "#E80020",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "VCARB": "#6692FF", // Alias
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252", // Alias
    "Haas": "#B6BABD",
    "Haas F1 Team": "#B6BABD",
};

export const DEFAULT_COLOR = "#FFFFFF";

export function getTeamColor(teamName: string | undefined | null): string {
    if (!teamName) return DEFAULT_COLOR;
    // Normalize string: Trim and handle potential inconsistencies
    const key = Object.keys(TEAM_COLORS).find(k => k.toLowerCase() === teamName.toLowerCase()) || teamName;
    return TEAM_COLORS[key] || DEFAULT_COLOR;
}
