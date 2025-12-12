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
    activeCharts: string[];
    hoveredLap: number | null;
    viewMode: 'dashboard' | 'summary';

    // Data
    driverLaps: LapData[];

    // Actions
    setSession: (session: SessionInfo | null) => void;
    setSelection: (year: number, gp: string, sessionType: string) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    selectDriver: (code: string) => void;
    setMode: (mode: SessionMode) => void;
    toggleChart: (chartId: string) => void;
    reorderCharts: (orderedCharts: string[]) => void;
    setHoveredLap: (lap: number | null) => void;
    setDriverLaps: (laps: LapData[]) => void;
    setViewMode: (mode: 'dashboard' | 'summary') => void;
}

export const useF1Store = create<F1State>((set) => ({
    // Initial State
    session: null,
    isLoading: false,
    error: null,
    // State
    selectedYear: 2024,
    selectedGP: "",
    selectedSessionType: "R",
    selectedDriver: null,
    selectedMode: 'RACE',
    activeCharts: ['the_worm', 'consistency_box'], // Default charts
    hoveredLap: null,
    viewMode: 'dashboard',
    driverLaps: [],

    // Actions
    setSession: (session) => set({ session, error: null }),
    setSelection: (year, gp, sessionType) => set({ selectedYear: year, selectedGP: gp, selectedSessionType: sessionType }),
    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error, isLoading: false }),
    selectDriver: (code) => set({ selectedDriver: code }),
    setMode: (mode) => set({ selectedMode: mode }),
    toggleChart: (chartId) => set((state) => {
        const isActive = state.activeCharts.includes(chartId);
        let updatedCharts = isActive
            ? state.activeCharts.filter(id => id !== chartId)
            : [...state.activeCharts, chartId];
        if (updatedCharts.length === 0) updatedCharts = [chartId]; // Keep one active
        return { activeCharts: updatedCharts };
    }),
    reorderCharts: (orderedCharts) => set({ activeCharts: orderedCharts }),
    setHoveredLap: (lap) => set({ hoveredLap: lap }),
    setDriverLaps: (laps) => set({ driverLaps: laps }),
    setViewMode: (mode) => set({ viewMode: mode }),
}));
