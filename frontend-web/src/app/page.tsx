'use client';

import { useEffect, useState } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { initSession, getDriverLaps, getLapTelemetry } from '@/lib/api';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { WeekendSummary } from '@/components/dashboard/WeekendSummary'; // [NEW]
import { CHART_REGISTRY } from '@/lib/chartRegistry';
import { cn } from '@/lib/utils';

import { Toaster, toast } from 'sonner';

interface Telemetry {
    driver: string;
    color: string;
    distance: number[];
    speed: number[];
    throttle: number[];
    brake: number[];
    corners: { number: number; distance: number }[];
    brakingZones: number[][];
}

export default function Dashboard() {
    const { session, setSession, setLoading, isLoading, selectedDriver, activeCharts, setDriverLaps, driverLaps, selectedYear, selectedGP, selectedSessionType, viewMode, setViewMode, reorderCharts } = useF1Store();
    const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Load session on mount and when selection changes
    useEffect(() => {
        async function loadSession() {
            if (!selectedGP) return;

            const toastId = toast.loading(`Loading ${selectedGP} ${selectedYear}...`);
            setLoading(true);
            setSession(null); // Clear previous session

            try {
                const data = await initSession(selectedYear, selectedGP, selectedSessionType);
                setSession(data);
                toast.success("Session Data Loaded", { id: toastId });
            } catch (err: any) {
                const msg = err.response?.status === 500 ? 'Backend Error (500). Check Server Logs.' : 'Failed to load session.';
                setError(msg);
                toast.error(msg, { id: toastId });
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        loadSession();
    }, [selectedYear, selectedGP, selectedSessionType, setSession, setLoading]);

    // Load driver data when selected
    useEffect(() => {
        async function loadDriverData() {
            if (!selectedDriver) return;

            try {
                // Get laps
                const lapsData = await getDriverLaps(selectedDriver);
                setDriverLaps(lapsData.laps);

                // Get fastest lap telemetry
                const fastestLap = lapsData.laps.reduce(
                    (min: any, lap: any) => (lap.lapTime < min.lapTime ? lap : min),
                    lapsData.laps[0]
                );

                if (fastestLap) {
                    const telemData = await getLapTelemetry(selectedDriver, fastestLap.lapNumber);
                    setTelemetry(telemData);
                }
            } catch (err) {
                console.error('Failed to load driver data:', err);
            }
        }
        loadDriverData();
    }, [selectedDriver, setDriverLaps]);

    // Get driver color
    const driverColor = session?.drivers.find((d) => d.code === selectedDriver)?.color || '#0A84FF';

    return (
        <div className="flex h-screen bg-background text-text-primary overflow-hidden">
            <Toaster position="top-right" theme="dark" />

            {/* Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 p-4 h-full overflow-hidden relative flex flex-col gap-4">

                {/* GLOBAL HEADER */}
                <header className="bg-black rounded-xl p-4 flex items-center justify-between shrink-0 border border-white/5">
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-bold">
                            {viewMode === 'summary' ? 'Weekend Summary' : (session?.eventName || 'F1 Dashboard')}
                        </h1>
                        <span className="text-text-secondary text-sm bg-white/5 px-2 py-1 rounded">
                            {viewMode === 'summary' ? `${selectedYear} ${selectedGP}` : (session?.sessionType || '-')}
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* VIEW MODE TOGGLE */}
                        <div className="flex bg-white/5 p-1 rounded-lg">
                            <button
                                onClick={() => setViewMode('dashboard')}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'dashboard'
                                    ? 'bg-primary text-white shadow-lg'
                                    : 'text-text-secondary hover:text-white'
                                    }`}
                            >
                                Dashboard
                            </button>
                            <button
                                onClick={() => setViewMode('summary')}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'summary'
                                    ? 'bg-primary text-white shadow-lg'
                                    : 'text-text-secondary hover:text-white'
                                    }`}
                            >
                                Summary
                            </button>
                        </div>

                        {isLoading && (
                            <div className="flex items-center gap-2 text-accent animate-pulse">
                                <div className="w-2 h-2 rounded-full bg-accent" />
                                <span className="text-sm">Loading...</span>
                            </div>
                        )}
                    </div>
                </header>

                {viewMode === 'summary' ? (
                    <WeekendSummary />
                ) : (
                    /* DASHBOARD VIEW */
                    <>
                        {/* Session error display if needed */}
                        {error && (
                            <div className="text-red-400 text-sm flex items-center gap-2 px-2">
                                <span>⚠️</span> {error}
                            </div>
                        )}

                        {/* Chart Grid */}
                        <div className="flex-1 overflow-y-auto pr-2 pb-20">
                            {!session ? (
                                <div className="h-full flex flex-col items-center justify-center text-text-secondary animate-in fade-in duration-500">
                                    <div className="p-8 rounded-full bg-white/5 mb-6">
                                        <span className="text-6xl opacity-50">🏎️</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-white mb-2">Ready to Race</h2>
                                    <p>Select a Grand Prix session from the sidebar</p>
                                </div>
                            ) : (
                                <DashboardGrid
                                    activeCharts={activeCharts}
                                    onReorder={reorderCharts}
                                    telemetryData={telemetry}
                                    driverLaps={driverLaps}
                                    selectedDriver={selectedDriver}
                                    driverColor={driverColor}
                                    session={session}
                                />
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
