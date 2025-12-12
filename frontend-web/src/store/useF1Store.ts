/**
 * Zustand Store - Global F1 State Management
 */
import { create } from 'zustand';

export type SessionMode = 'PRACTICE' | 'QUALI' | 'RACE';

interface Driver {
    code: string;
    team: string;
    color: string;
    bestLap: string;
    position: number;
}

interface Corner {
    number: number;
    distance: number;
}

interface SessionInfo {
    year: number;
    gp: string;
    sessionType: string;
    eventName: string;
    circuitName: string;
    drivers: Driver[];
    corners: Corner[];
    totalLaps: number;
}

interface LapData {
    lapNumber: number;
    lapTime: number;
    sector1: number | null;
    sector2: number | null;
    sector3: number | null;
    compound: string;
    tyreLife: number;
    isPersonalBest: boolean;
    isPitOut: boolean;
    isPitIn: boolean;
}

interface F1State {
    // Session
    session: SessionInfo | null;
    isLoading: boolean;
    error: string | null;

    // Selection
    selectedYear: number;
    selectedGP: string;
    selectedSessionType: string;
    selectedDriver: string | null;
    selectedMode: SessionMode;
    hoveredLap: number | null;

    // Data
    driverLaps: LapData[];

    // Actions
    setSession: (session: SessionInfo) => void;
    setSelection: (year: number, gp: string, sessionType: string) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    selectDriver: (code: string) => void;
    setMode: (mode: SessionMode) => void;
    setHoveredLap: (lap: number | null) => void;
    setDriverLaps: (laps: LapData[]) => void;
}

export const useF1Store = create<F1State>((set) => ({
    // Initial State
    session: null,
    isLoading: false,
    error: null,
    selectedYear: 2023,
    selectedGP: "Abu Dhabi",
    selectedSessionType: "R",
    selectedDriver: null,
    selectedMode: 'RACE',
    hoveredLap: null,
    driverLaps: [],

    // Actions
    setSession: (session) => set({ session, error: null }),
    setSelection: (year, gp, sessionType) => set({ selectedYear: year, selectedGP: gp, selectedSessionType: sessionType }),
    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error, isLoading: false }),
    selectDriver: (code) => set({ selectedDriver: code }),
    setMode: (mode) => set({ selectedMode: mode }),
    setHoveredLap: (lap) => set({ hoveredLap: lap }),
    setDriverLaps: (laps) => set({ driverLaps: laps }),
}));
